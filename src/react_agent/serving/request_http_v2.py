"""Authenticated HTTP adapter for the CPU lifecycle candidate; not a deployed worker."""
from __future__ import annotations

import hmac
import re
import secrets
import threading
from collections.abc import Callable, Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from react_agent.serving.request_lifecycle_v2 import RequestLifecycle
from react_agent.serving.structured_api_v1 import (
    LIMIT,
    ServiceError,
    Spec,
    canonical,
    json_object,
)

PROFILE = "react-vn-request-lifecycle-v2-candidate"
IDENTITY_KEYS = frozenset({"session_id", "source_commit", "worker_sha256", "model_revision"})
REQUEST_ROUTE = re.compile(r"/v1/requests/([a-zA-Z0-9_-]{1,80})(/cancel)?")


class LifecycleHTTP:
    """Own a fresh boot identity and expose only explicitly public identity fields."""

    def __init__(self, *, api_key: str, identity: Mapping[str, str], role: str,
                 model: str, root: Path,
                 engine: Callable[[Spec, threading.Event], dict[str, Any]]) -> None:
        if (not api_key.isascii() or not 32 <= len(api_key) <= 512
                or any(c.isspace() for c in api_key)):
            raise ValueError("bounded ASCII bearer key required")
        if set(identity) != IDENTITY_KEYS or any(not value for value in identity.values()):
            raise ValueError("exact public worker identity required")
        self._bearer = ("Bearer " + api_key).encode("ascii")
        self.lifecycle = RequestLifecycle(role=role, model=model, root=root,
            instance_id=secrets.token_hex(16), engine=engine)
        self._identity = {**identity, "role": role, "model_id": model,
                          "instance_id": self.lifecycle.instance_id}

    def authenticate(self, authorization: str | None) -> None:
        if authorization is None or not hmac.compare_digest(
                authorization.encode("utf-8"), self._bearer):
            raise ServiceError("UNAUTHORIZED", 401)

    def dispatch(self, method: str, path: str, authorization: str | None,
                 instance_id: str | None, raw: bytes = b"") -> tuple[dict[str, Any], int]:
        self.authenticate(authorization)  # Must precede identity, route and request lookup.
        if len(raw) > LIMIT:
            raise ServiceError("BODY_TOO_LARGE", 413)
        if method == "GET" and path == "/v1/models":
            if raw:
                raise ServiceError("BODY_NOT_ALLOWED", 400)
            return {"profile": PROFILE, "identity": dict(self._identity),
                    "status": "RETIRED" if self.lifecycle.retired else "READY",
                    "gpu_quiescence_attested": False}, 200
        if instance_id != self.lifecycle.instance_id:
            raise ServiceError("INSTANCE_MISMATCH", 409)
        if method == "POST" and path == "/v1/chat/completions":
            try:
                body = json_object(raw.decode("utf-8"))
            except (ValueError, UnicodeError, RecursionError):
                raise ServiceError("INVALID_JSON", 400) from None
            result, status = self.lifecycle.complete(instance_id, body)
            return {"identity": dict(self._identity), "result": result,
                    "request": self.lifecycle.status(instance_id, body["request_id"])}, status
        match = REQUEST_ROUTE.fullmatch(path)
        if match and ((method == "GET" and not match[2])
                      or (method == "POST" and match[2])):
            if raw:
                raise ServiceError("BODY_NOT_ALLOWED", 400)
            request = (self.lifecycle.cancel(instance_id, match[1]) if match[2]
                       else self.lifecycle.status(instance_id, match[1]))
            return {"identity": dict(self._identity), "request": request}, (
                202 if match[2] and request["state"] == "CANCEL_REQUESTED" else 200)
        raise ServiceError("ROUTE_NOT_FOUND", 404)


def make_server(app: LifecycleHTTP, address: tuple[str, int]) -> ThreadingHTTPServer:
    """Bind HTTP explicitly; the caller owns serving, TLS tunneling and shutdown."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass  # Request paths/headers are never written to access logs.

        def handle_one(self) -> None:
            self.close_connection = True
            try:
                auth = self.headers.get_all("Authorization", [])
                if len(auth) != 1:
                    raise ServiceError("UNAUTHORIZED", 401)
                app.authenticate(auth[0])  # Do not read an unauthenticated body.
                if self.headers.get_all("Transfer-Encoding"):
                    raise ServiceError("TRANSFER_ENCODING_UNSUPPORTED", 400)
                lengths = self.headers.get_all("Content-Length", [])
                if len(lengths) > 1 or (lengths and not re.fullmatch(r"[0-9]{1,9}", lengths[0])):
                    raise ServiceError("INVALID_CONTENT_LENGTH", 400)
                length = int(lengths[0]) if lengths else 0
                if length > LIMIT:
                    raise ServiceError("BODY_TOO_LARGE", 413)
                instances = self.headers.get_all("X-Instance-ID", [])
                if len(instances) > 1:
                    raise ServiceError("INSTANCE_MISMATCH", 409)
                self.connection.settimeout(5)
                raw = self.rfile.read(length) if length else b""
                if len(raw) != length:
                    raise ServiceError("INCOMPLETE_BODY", 400)
                payload, status = app.dispatch(self.command, self.path, auth[0],
                                               instances[0] if instances else None, raw)
            except ServiceError as exc:
                payload, status = {"error": {"code": exc.code}}, exc.status
            except (TimeoutError, ConnectionError):
                payload, status = {"error": {"code": "REQUEST_READ_FAILED"}}, 408
            encoded = canonical(payload).encode("utf-8")
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(encoded)
            except (TimeoutError, ConnectionError):
                # Response loss leaves lifecycle evidence/cached result intact.
                return

        do_GET = handle_one
        do_POST = handle_one

    return ThreadingHTTPServer(address, Handler)
