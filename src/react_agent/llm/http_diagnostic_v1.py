"""Opt-in legacy HTTP backend for technical smoke, not attested benchmark runs."""

from __future__ import annotations

import json
import math
import ssl
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig, ModelResponse

Transport = Callable[[str, str, dict[str, Any] | None], dict[str, Any]]
MAX_BYTES = 262144


class APIError(RuntimeError):
    """Only public error codes cross the transport boundary."""

    def __init__(self, code: str, status: int | None = None) -> None:
        super().__init__(code)
        self.code, self.status = code, status


def strict_object(text: str) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    value = json.loads(text, object_pairs_hook=unique)
    canonical_json(value)  # Reject non-finite numbers.
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        raise APIError("REDIRECT_REFUSED")


class HTTPSJSON:
    """Explicit verified HTTPS, bounded reads, socket timeout, no retry/redirect."""

    def __init__(self, base_url: str, api_key: str, *, timeout: float = 90,
                 cafile: Path | None = None) -> None:
        parts = urlsplit(base_url)
        if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
                or parts.query or parts.fragment or parts.path.rstrip("/") != "/v1"
                or not api_key or any(c in api_key for c in "\r\n")
                or not math.isfinite(timeout) or not 1 <= timeout <= 240):
            raise ValueError("HTTPS /v1 endpoint, key and bounded timeout required")
        # The macOS Python framework may have no CA file. Keep verification on.
        if cafile is None and ssl.get_default_verify_paths().cafile is None:
            system_ca = Path("/etc/ssl/cert.pem")
            if system_ca.is_file():
                cafile = system_ca
        context = ssl.create_default_context(cafile=str(cafile) if cafile else None)
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=context), NoRedirect())
        self._base, self._key, self._timeout = base_url.rstrip("/"), api_key, timeout

    def __call__(self, method: str, path: str,
                 payload: dict[str, Any] | None) -> dict[str, Any]:
        if (method, path) not in {("GET", "/models"), ("POST", "/chat/completions")}:
            raise APIError("UNSUPPORTED_OPERATION")
        data = canonical_json(payload).encode() if payload is not None else None
        if data is not None and len(data) > MAX_BYTES:
            raise APIError("REQUEST_TOO_LARGE")
        request = urllib.request.Request(  # noqa: S310 - constructor admits HTTPS only
            self._base + path, data=data, method=method,
            headers={"Authorization": "Bearer " + self._key,
                     "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with self._opener.open(request, timeout=self._timeout) as response:
                if response.status != 200:
                    raise APIError("HTTP_ERROR", response.status)
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise APIError("RESPONSE_TOO_LARGE")
                return strict_object(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise APIError("HTTP_ERROR", exc.code) from None
        except urllib.error.URLError as exc:
            code = "TLS_ERROR" if isinstance(exc.reason, ssl.SSLError) else (
                "TIMEOUT" if isinstance(exc.reason, TimeoutError) else "NETWORK_ERROR")
            raise APIError(code) from None
        except TimeoutError:
            raise APIError("TIMEOUT") from None
        except ssl.SSLError:
            raise APIError("TLS_ERROR") from None
        except OSError:
            raise APIError("NETWORK_ERROR") from None
        except (ValueError, UnicodeError):
            raise APIError("INVALID_RESPONSE") from None


class HTTPDiagnosticBackend:
    """LLMBackend-compatible; revision is a diagnostic binding, NOT weight proof."""

    def __init__(self, transport: Transport, *, model_id: str, expected_mount: str) -> None:
        if not model_id or not expected_mount:
            raise ValueError("explicit model and mount required")
        self.model_id = model_id
        self.model_revision = "diagnostic-unverified:not-probed"
        self._transport, self._mount = transport, expected_mount
        self.metadata: dict[str, Any] | None = None
        self.calls: list[dict[str, Any]] = []

    def probe(self) -> dict[str, Any]:
        data = self._transport("GET", "/models", None)
        rows = data.get("data")
        if (not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict)
                or rows[0].get("id") != self.model_id or data.get("model_path") != self._mount):
            raise APIError("MODEL_MISMATCH")
        metadata = {"model_id": self.model_id, "model_path": self._mount,
                    "gpu": data.get("gpu"), "precision": data.get("quantization"),
                    "identity_attested": False, "seed_supported": False,
                    "constrained_decoding_supported": False}
        if self.metadata is not None and metadata != self.metadata:
            raise APIError("MODEL_METADATA_CHANGED")
        self.metadata = metadata
        self.model_revision = "diagnostic-unverified:" + text_hash(canonical_json(metadata))
        return dict(metadata)

    def generate(self, messages: list[dict[str, str]],
                 config: GenerationConfig) -> ModelResponse:
        if self.metadata is None:
            raise APIError("PROBE_REQUIRED")
        if config.temperature != 0 or not 1 <= config.max_new_tokens <= 1024:
            raise APIError("UNSUPPORTED_GENERATION")
        if (not messages or any(set(m) != {"role", "content"}
                or m["role"] not in {"system", "user", "assistant"}
                or not isinstance(m["content"], str) for m in messages)):
            raise APIError("INVALID_MESSAGES")
        payload = {"model": self.model_id, "messages": messages, "stream": False,
                   "temperature": 0, "max_tokens": config.max_new_tokens}
        receipt: dict[str, Any] = {"request_sha256": text_hash(canonical_json(payload)),
            "model_id": self.model_id, "generation": config.model_dump(mode="json"),
            "seed_applied": False, "identity_attested": False, "status": "STARTED"}
        self.calls.append(receipt)
        started = time.monotonic()
        try:
            data = self._transport("POST", "/chat/completions", payload)
            if data.get("model") != self.model_id:
                raise APIError("MODEL_MISMATCH")
            choices = data.get("choices")
            if not isinstance(choices, list) or len(choices) != 1:
                raise APIError("INVALID_RESPONSE")
            choice = choices[0]
            if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
                raise APIError("INVALID_RESPONSE")
            message = choice["message"]
            text = message.get("content")
            if (message.get("role") != "assistant" or not isinstance(text, str)
                    or not text or len(text.encode()) > MAX_BYTES
                    or message.get("tool_calls") or message.get("reasoning_content")
                    or message.get("reasoning")):
                raise APIError("UNSUPPORTED_OUTPUT")
            finish = choice.get("finish_reason")
            if finish != "stop":
                raise APIError("OUTPUT_LIMIT" if finish == "length" else "UNSUPPORTED_FINISH")
            # Only structured observable objects are admitted. No rejected raw text is saved.
            try:
                strict_object(text)
            except (ValueError, RecursionError):
                raise APIError("INVALID_JSON_OUTPUT") from None
            usage = data.get("usage", {})
            receipt.update(status="OK", finish_reason_reported=finish,
                finish_reason_verified=False, usage_verified=False,
                usage_reported={k: v for k, v in usage.items() if k in {
                    "prompt_tokens", "completion_tokens", "total_tokens"}
                    and type(v) is int and v >= 0} if isinstance(usage, dict) else {})
            return ModelResponse(text=text, model_id=self.model_id,
                                 model_revision=self.model_revision)
        except APIError as exc:
            receipt.update(status="ERROR", error_code=exc.code, http_status=exc.status)
            raise
        finally:
            receipt["wall_seconds"] = time.monotonic() - started
