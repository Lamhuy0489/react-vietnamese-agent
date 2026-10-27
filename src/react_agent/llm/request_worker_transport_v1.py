"""Authenticated host transport for the request-worker v3 candidate.

This adapter is deliberately separate from the v1 structured transport.  The
v3 worker has a boot instance id and exposes request status/cancel routes, so a
host must bind every operation to the id returned by an authenticated
``/models`` probe.  The transport does not retry and never treats a health
response as evidence about an earlier request.
"""
from __future__ import annotations

import json
import math
import re
import ssl
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from react_agent.llm.http_diagnostic_v1 import APIError, NoRedirect, strict_object
from react_agent.serving.structured_api_v1 import LIMIT

PROFILE = "react-vn-request-lifecycle-v3-candidate"
MAX_RESPONSE_BYTES = LIMIT
STATIC_IDENTITY = frozenset({
    "session_id", "source_commit", "worker_sha256", "model_revision", "model_id", "role",
})
PUBLIC_IDENTITY = frozenset({*STATIC_IDENTITY, "instance_id"})
REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


@dataclass(frozen=True)
class WorkerExchange:
    """A bounded JSON response before interpretation by the journal/runtime."""

    status: int
    payload: dict[str, Any]


def _identity(value: Mapping[str, Any], keys: frozenset[str]) -> dict[str, str]:
    if set(value) != keys or any(not isinstance(v, str) or not v for v in value.values()):
        raise APIError("WORKER_IDENTITY_INVALID")
    return {key: value[key] for key in keys}


class RequestWorkerHTTPS:
    """No-redirect HTTPS transport with authenticated v3 route binding.

    ``expected_identity`` contains the static source/model/session pins.  The
    worker boot ``instance_id`` is learned only from a successful authenticated
    probe and is then sent on every request route.  ``opener`` is an internal
    injection point used by offline tests; production callers leave it unset.
    """

    def __init__(self, base_url: str, api_key: str,
                 expected_identity: Mapping[str, str], *, timeout: float = 90,
                 opener: Any | None = None) -> None:
        parts = urlsplit(base_url)
        if (parts.scheme != "https" or not parts.hostname or parts.username
                or parts.password or parts.query or parts.fragment
                or parts.path.rstrip("/") != "/v1" or not api_key
                or any(char in api_key for char in "\r\n")
                or not math.isfinite(timeout) or not 1 <= timeout <= 240):
            raise ValueError("HTTPS /v1 endpoint, key and bounded timeout required")
        if set(expected_identity) != STATIC_IDENTITY or any(
                not isinstance(value, str) or not value for value in expected_identity.values()):
            raise ValueError("complete static worker identity required")
        if not expected_identity["model_revision"].startswith("sha256:"):
            raise ValueError("content-addressed model revision required")
        if expected_identity["role"] not in {"agent", "guard"}:
            raise ValueError("worker role required")
        if opener is None:
            cafile = None
            if ssl.get_default_verify_paths().cafile is None:
                system_ca = "/etc/ssl/cert.pem"
                if Path(system_ca).is_file():
                    cafile = system_ca
            context = ssl.create_default_context(cafile=cafile)
            opener = urllib.request.build_opener(
                urllib.request.HTTPSHandler(context=context), NoRedirect())
        self._opener = opener
        self._base = base_url.rstrip("/")
        self._key = api_key
        self._timeout = timeout
        self.expected_identity = dict(expected_identity)
        self.identity: dict[str, str] | None = None

    @property
    def instance_id(self) -> str:
        if self.identity is None:
            raise APIError("PROBE_REQUIRED")
        return self.identity["instance_id"]

    def _route(self, method: str, path: str) -> None:
        if (method, path) == ("GET", "/models"):
            return
        if (method, path) == ("POST", "/chat/completions"):
            return
        if re.fullmatch(r"/requests/[A-Za-z0-9_-]{1,80}", path):
            if method == "GET":
                return
        if re.fullmatch(r"/requests/[A-Za-z0-9_-]{1,80}/cancel", path):
            if method == "POST":
                return
        raise APIError("UNSUPPORTED_OPERATION")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None,
                 *, instance_id: str | None) -> WorkerExchange:
        self._route(method, path)
        if method == "GET" and payload is not None:
            raise APIError("BODY_NOT_ALLOWED")
        body = None if payload is None else json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        if body is not None and len(body) > LIMIT:
            raise APIError("REQUEST_TOO_LARGE")
        headers = {"Authorization": "Bearer " + self._key,
                   "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if instance_id is not None:
            if not REQUEST_ID.fullmatch(instance_id):
                raise APIError("WORKER_IDENTITY_INVALID")
            headers["X-Instance-ID"] = instance_id
        request = urllib.request.Request(self._base + path, data=body, method=method,  # noqa: S310
                                         headers=headers)  # noqa: S310 - HTTPS is validated above
        try:
            response = self._opener.open(request, timeout=self._timeout)
            try:
                status = int(response.status)
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            finally:
                response.close()
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            try:
                raw = exc.read(MAX_RESPONSE_BYTES + 1)
            finally:
                exc.close()
        except urllib.error.URLError as exc:
            reason = exc.reason
            code = "TLS_ERROR" if isinstance(reason, ssl.SSLError) else "NETWORK_ERROR"
            if isinstance(reason, TimeoutError):
                code = "TIMEOUT"
            raise APIError(code) from None
        except TimeoutError:
            raise APIError("TIMEOUT") from None
        except ssl.SSLError:
            raise APIError("TLS_ERROR") from None
        except OSError:
            raise APIError("NETWORK_ERROR") from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise APIError("RESPONSE_TOO_LARGE")
        try:
            value = strict_object(raw.decode("utf-8"))
        except (ValueError, UnicodeError, RecursionError):
            # Proxies/tunnels commonly return an HTML error page for a 5xx
            # response.  Do not misclassify that delivery failure as a
            # successful worker response or persist its body; retain only the
            # status code so the journal can remain fail-closed and auditable.
            raise APIError("HTTP_ERROR" if status >= 400 else "INVALID_RESPONSE", status) from None
        return WorkerExchange(status, value)

    def probe(self) -> dict[str, Any]:
        """Authenticate and pin a fresh boot instance before any request."""
        exchange = self._request("GET", "/models", None, instance_id=None)
        if exchange.status != 200:
            raise APIError("WORKER_NOT_READY", exchange.status)
        value = exchange.payload
        if value.get("profile") != PROFILE or value.get("status") != "READY":
            raise APIError("WORKER_NOT_READY")
        if value.get("gpu_quiescence_attested") is not False:
            raise APIError("WORKER_READINESS_INVALID")
        actual = _identity(value.get("identity", {}), PUBLIC_IDENTITY)
        if any(actual[key] != self.expected_identity[key] for key in STATIC_IDENTITY):
            raise APIError("WORKER_IDENTITY_MISMATCH")
        if not REQUEST_ID.fullmatch(actual["instance_id"]):
            raise APIError("WORKER_IDENTITY_INVALID")
        self.identity = actual
        return value

    def exchange(self, method: str, path: str,
                 payload: dict[str, Any] | None = None) -> WorkerExchange:
        """Perform one bound request; caller decides how a non-2xx result resolves."""
        if self.identity is None:
            raise APIError("PROBE_REQUIRED")
        return self._request(method, path, payload, instance_id=self.instance_id)

    def __call__(self, method: str, path: str,
                 payload: dict[str, Any] | None) -> dict[str, Any]:
        exchange = self.exchange(method, path, payload)
        if exchange.status >= 400 and "identity" not in exchange.payload:
            error = exchange.payload.get("error", {})
            code = error.get("code") if isinstance(error, dict) else None
            raise APIError(code if isinstance(code, str) else "HTTP_ERROR", exchange.status)
        if exchange.payload.get("identity") != self.identity:
            raise APIError("WORKER_RESPONSE_IDENTITY")
        return exchange.payload
