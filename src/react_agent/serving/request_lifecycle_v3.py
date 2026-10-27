"""Versioned lifecycle with bounded results and explicit native quiescence evidence."""
from __future__ import annotations

import json
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from react_agent.serving.quiescent_engine_v3 import EngineOutcome
from react_agent.serving.request_storage_v3 import save_new
from react_agent.serving.structured_api_v1 import ServiceError, Spec, admit, canonical, sha

TERMINAL = frozenset({"SUCCEEDED", "FAILED", "CANCELLED"})


@dataclass
class Request:
    digest: str
    stop: threading.Event = field(default_factory=threading.Event)
    state: str = "RUNNING"
    result: dict[str, Any] | None = None
    http_status: int = 202
    sequence: int = 0
    engine_returned: bool = False
    quiescent: bool = False
    durable: bool = False


class QuiescentLifecycle:
    """One engine at a time; accepted cancel is pending until the engine returns.

    Engine callback must observe the supplied per-request event and return/raise
    only after its own work is quiescent. CPU tests cannot attest GPU quiescence.
    Persistent instance directories are single-use: restart requires a new ID.
    """

    def __init__(self, *, role: str, model: str, instance_id: str, root: Path,
                 engine: Callable[[Spec, threading.Event], EngineOutcome],
                 capacity: int = 1024, result_limit: int = 262144) -> None:
        if (role not in {"agent", "guard"} or not model
                or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", instance_id)
                or type(capacity) is not int or not 1 <= capacity <= 1024
                or type(result_limit) is not int or not 1024 <= result_limit <= 262144):
            raise ValueError("explicit bounded instance identity required")
        self.role, self.model, self.instance_id = role, model, instance_id
        self.engine, self.capacity = engine, capacity
        self.result_limit = result_limit
        self.root = root / instance_id
        self.root.mkdir(parents=True, exist_ok=False)
        self.lock = threading.Lock()
        self.requests: dict[str, Request] = {}
        self.active: str | None = None
        self.retired = False
        save_new(self.root / "instance.json", {"instance_id": instance_id, "role": role,
                                               "model": model, "capacity": capacity,
                                               "result_limit": result_limit})

    def _view(self, request_id: str, request: Request) -> dict[str, Any]:
        return {"instance_id": self.instance_id, "request_id": request_id,
            "request_sha256": request.digest, "state": request.state,
            "cancel_requested": request.stop.is_set(), "engine_returned": request.engine_returned,
            "engine_active": self.active == request_id,
            "gpu_quiescence_attested": request.quiescent,
            "quiescence_basis": "device_synchronize" if request.quiescent else "unconfirmed",
            "durable": request.durable, "instance_retired": self.retired,
            "http_status": request.http_status,
            "response_sha256": sha(canonical(request.result).encode())
            if request.result is not None else None}

    def _persist(self, request_id: str, request: Request) -> None:
        request.sequence += 1
        request.durable = False
        # The receipt describes the state after successful fsync, never before it.
        save_new(self.root / f"{request_id}.{request.sequence:04d}.json",
                 {**self._view(request_id, request), "durable": True})
        request.durable = True

    def _lookup(self, instance_id: str, request_id: str) -> Request:
        if instance_id != self.instance_id:
            raise ServiceError("INSTANCE_MISMATCH", 409)
        if request_id not in self.requests:
            raise ServiceError("REQUEST_UNKNOWN", 404)
        return self.requests[request_id]

    def status(self, instance_id: str, request_id: str) -> dict[str, Any]:
        with self.lock:
            return self._view(request_id, self._lookup(instance_id, request_id))

    def cancel(self, instance_id: str, request_id: str) -> dict[str, Any]:
        with self.lock:
            request = self._lookup(instance_id, request_id)
            if request.state == "RUNNING":
                request.stop.set()
                request.state = "CANCEL_REQUESTED"
                try:
                    self._persist(request_id, request)
                except OSError:
                    self.retired = True
                    raise ServiceError("STATE_WRITE_FAILED", 503) from None
            return self._view(request_id, request)

    def begin_shutdown(self) -> None:
        """Reject new work and signal the active engine; never assert it stopped."""
        with self.lock:
            self.retired = True
            if self.active is not None:
                request = self.requests[self.active]
                request.stop.set()
                request.state = "CANCEL_REQUESTED"
                self._persist(self.active, request)

    def is_idle(self) -> bool:
        with self.lock:
            return self.active is None

    def complete(self, instance_id: str, body: dict[str, Any]) -> tuple[dict[str, Any], int]:
        if instance_id != self.instance_id:
            raise ServiceError("INSTANCE_MISMATCH", 409)
        if "request_id" not in body:
            raise ServiceError("REQUEST_ID_REQUIRED", 400)
        spec = admit(body, self.role, self.model)
        digest = sha(canonical(body).encode())
        with self.lock:
            if self.retired:
                raise ServiceError("INSTANCE_RETIRED", 503)
            existing = self.requests.get(spec.request_id)
            if existing is not None:
                if existing.digest != digest:
                    raise ServiceError("REQUEST_ID_CONFLICT", 409)
                if existing.state not in TERMINAL:
                    raise ServiceError("REQUEST_IN_PROGRESS", 409)
                if existing.result is None:
                    raise ServiceError("RESULT_UNAVAILABLE", 503)
                return json.loads(canonical(existing.result)), existing.http_status
            if self.active is not None:
                raise ServiceError("BUSY", 429)
            if len(self.requests) >= self.capacity:
                # No eviction that could silently execute an old ID again.
                raise ServiceError("INSTANCE_CAPACITY", 503)
            request = Request(digest)
            self.requests[spec.request_id] = request
            self.active = spec.request_id
            try:
                self._persist(spec.request_id, request)
            except OSError:
                self.active = None
                self.retired = True
                raise ServiceError("STATE_WRITE_FAILED", 503) from None
        interrupted = False
        outcome = EngineOutcome({"error": {"code": "QUIESCENCE_UNKNOWN"}}, 503, False, False)
        try:
            received = self.engine(spec, request.stop)
            if not isinstance(received, EngineOutcome):
                raise TypeError("explicit engine outcome required")
            outcome = received
            result, code = outcome.result, outcome.http_status
            # Copy into JSON so engine-owned mutable state cannot alter cached output.
            encoded = canonical(result)
            if len(encoded.encode()) > self.result_limit:
                result, code = {"error": {"code": "RESULT_TOO_LARGE"}}, 507
            else:
                result = json.loads(encoded)
        except ServiceError as exc:
            result, code = {"error": {"code": exc.code}}, exc.status
        except Exception:  # Sanitize arbitrary model exceptions; no raw text or reasoning.
            result, code = {"error": {"code": "GENERATION_FAILED"}}, 500
            outcome = EngineOutcome(result, code, outcome.quiescent, False)
        except BaseException:
            interrupted = True
            result, code = {"error": {"code": "ENGINE_INTERRUPTED"}}, 503
            raise
        finally:
            with self.lock:
                request.engine_returned = True
                self.active = None
                request.quiescent = outcome.quiescent
                if not outcome.reusable or not outcome.quiescent:
                    self.retired = True
                if not outcome.quiescent:
                    request.state = "QUIESCENCE_UNKNOWN"
                    request.result = {"error": {"code": "QUIESCENCE_UNKNOWN"}}
                    request.http_status = 503
                elif request.stop.is_set():
                    request.state = "CANCELLED"
                    request.result, request.http_status = {"error": {"code": "CANCELLED"}}, 409
                else:
                    request.state = "SUCCEEDED" if code == 200 else "FAILED"
                    request.result, request.http_status = result, code
                if interrupted:
                    self.retired = True
                try:
                    self._persist(spec.request_id, request)
                except OSError:
                    self.retired = True
                    raise ServiceError("STATE_WRITE_FAILED", 503) from None
        return json.loads(canonical(request.result)), request.http_status
