"""Bounded task-local warm inference worker; no retries or cross-task cache."""

from __future__ import annotations

import ctypes
import json
import multiprocessing as mp
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.security_v1.guard import GuardInput, GuardOutcome, ModelGuard
from react_agent.security_v1.process_guard import MAX_RESPONSE_BYTES, ProcessGuardConfig

MAX_REQUEST_BYTES = 131_072
ERRORS = frozenset({"BACKEND_FAILURE", "IDENTITY_CHANGED", "RESPONSE_TOO_LARGE", "INVALID_REQUEST"})


@dataclass(frozen=True)
class WarmGuardConfig(ProcessGuardConfig):
    lifecycle: str = field(default="task_local_warm_v1", init=False)


def _serve(
    factory: Callable[[], LLMBackend],
    identity: tuple[str, str],
    request: Any,
    request_length: Any,
    response: Any,
    response_length: Any,
    pending: Any,
    complete: Any,
    stopping: Any,
) -> None:
    with open(os.devnull, "w") as sink:
        os.dup2(sink.fileno(), 1)
        os.dup2(sink.fileno(), 2)
    started = time.monotonic()
    backend: LLMBackend | None = None
    load_error: str | None = None
    try:
        backend = factory()
        if (backend.model_id, backend.model_revision) != identity:
            load_error = "IDENTITY_CHANGED"
    except Exception:  # Sanitize the host backend boundary; no raw exception strings.
        load_error = "BACKEND_FAILURE"
    load_seconds = time.monotonic() - started
    expected_sequence = 1
    while True:
        pending.wait()
        pending.clear()
        if stopping.is_set():
            return
        generation_seconds = 0.0
        packet: dict[str, Any] = {"sequence": expected_sequence}
        try:
            size = request_length.value
            if not 0 < size <= MAX_REQUEST_BYTES:
                raise ValueError("request size")
            incoming = json.loads(bytes(request[:size]))
            if incoming["sequence"] != expected_sequence:
                raise ValueError("request sequence")
            generation = GenerationConfig.model_validate(incoming["generation"])
            if load_error:
                packet["error"] = load_error
            elif backend is None:
                packet["error"] = "BACKEND_FAILURE"
            elif (backend.model_id, backend.model_revision) != identity:
                packet["error"] = "IDENTITY_CHANGED"
            else:
                generation_started = time.monotonic()
                try:
                    value = backend.generate(incoming["messages"], generation)
                    if (backend.model_id, backend.model_revision) != identity or (
                        value.model_id,
                        value.model_revision,
                    ) != identity:
                        packet["error"] = "IDENTITY_CHANGED"
                    else:
                        packet["response"] = value.model_dump(mode="json")
                except Exception:  # Never propagate arbitrary backend exception text.
                    packet["error"] = "BACKEND_FAILURE"
                generation_seconds = time.monotonic() - generation_started
        except (ValueError, KeyError, TypeError):
            packet["error"] = "INVALID_REQUEST"
        packet.update(
            load_seconds=load_seconds if expected_sequence == 1 else 0.0,
            generation_seconds=generation_seconds,
        )
        encoded = canonical_json(packet).encode("utf-8")
        if len(encoded) > MAX_RESPONSE_BYTES:
            packet.pop("response", None)
            packet["error"] = "RESPONSE_TOO_LARGE"
            encoded = canonical_json(packet).encode("utf-8")
        response[: len(encoded)] = encoded
        response_length.value = len(encoded)
        complete.set()
        if "error" in packet:
            return
        expected_sequence += 1


class WarmGuardBackend:
    def __init__(self, factory: Callable[[], LLMBackend], config: WarmGuardConfig) -> None:
        self.factory, self.config = factory, config
        self.model_id, self.model_revision = config.model_id, config.model_revision
        self.attempts: list[dict[str, Any]] = []
        self.lifecycle_events: list[dict[str, Any]] = []
        self._retired = False
        self.closed = False
        self._process: Any = None
        self._started = False
        self._owner_pid = os.getpid()
        self._lock = threading.Lock()
        self._ctx = mp.get_context("spawn")
        self._request: Any = self._ctx.RawArray(ctypes.c_ubyte, MAX_REQUEST_BYTES)
        self._response: Any = self._ctx.RawArray(ctypes.c_ubyte, MAX_RESPONSE_BYTES)
        self._request_length: Any = self._ctx.RawValue(ctypes.c_int, -1)
        self._response_length: Any = self._ctx.RawValue(ctypes.c_int, -1)
        self._pending = self._ctx.Event()
        self._complete = self._ctx.Event()
        self._stopping = self._ctx.Event()

    @property
    def retired(self) -> bool:
        if self._process is not None and self._started and not self._process.is_alive():
            self._retired = True
        return self._retired or self.closed

    def _cleanup(self, *, graceful: bool) -> bool:
        process = self._process
        if process is None:
            return True
        started = time.monotonic()
        pid = process.pid
        method = "NOT_STARTED" if pid is None else "EXITED"
        if pid is not None:
            if graceful and process.is_alive():
                self._stopping.set()
                self._pending.set()
                process.join(self.config.terminate_grace_seconds)
                method = "GRACEFUL"
            if process.is_alive():
                process.terminate()
                process.join(self.config.terminate_grace_seconds)
                method = "TERMINATE"
            if process.is_alive():
                process.kill()
                process.join(self.config.kill_grace_seconds)
                method = "KILL"
            reaped = not process.is_alive()
            if reaped:
                process.join(0)
        else:
            reaped = True
        self.lifecycle_events.append(
            {
                "sequence": len(self.lifecycle_events) + 1,
                "pid": pid,
                "method": method,
                "reaped": reaped,
                "exitcode": process.exitcode,
                "elapsed_seconds": time.monotonic() - started,
            }
        )
        if reaped:
            process.close()
            self._process = None
        return reaped

    def retire(self) -> None:
        if os.getpid() != self._owner_pid or not self._lock.acquire(blocking=False):
            raise RuntimeError("retirement requires an idle owning process")
        try:
            self._retired = True
            if not self._cleanup(graceful=False):
                raise RuntimeError("guard cancellation failed")
        finally:
            self._lock.release()

    def close(self) -> None:
        if os.getpid() != self._owner_pid:
            raise RuntimeError("only the owning process may close guard")
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("cannot close an in-flight guard request")
        try:
            self.closed = True
            if not self._cleanup(graceful=True):
                raise RuntimeError("guard cancellation failed")
        finally:
            self._lock.release()

    def __enter__(self) -> WarmGuardBackend:
        if self.closed:
            raise RuntimeError("guard already closed")
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if os.getpid() != self._owner_pid:
            raise RuntimeError("guard belongs to another process")
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("concurrent guard requests are unsupported")
        started = time.monotonic()
        status, pid = "START_FAILURE", None
        cold = not self._started
        timing: dict[str, float] = {}
        try:
            if self.retired:
                status = "RETIRED"
                raise RuntimeError("guard retired; no automatic retry")
            if (self.model_id, self.model_revision) != (
                self.config.model_id,
                self.config.model_revision,
            ):
                status = "IDENTITY_CHANGED"
                raise RuntimeError("guard execution identity changed")
            sequence = len(self.attempts) + 1
            encoded = canonical_json(
                {"sequence": sequence, "messages": messages, "generation": config.model_dump()}
            ).encode("utf-8")
            if len(encoded) > MAX_REQUEST_BYTES:
                status = "REQUEST_TOO_LARGE"
                raise ValueError("guard request exceeds byte limit")
            self._request[: len(encoded)] = encoded
            self._request_length.value = len(encoded)
            self._response_length.value = -1
            self._complete.clear()
            if not self._started:
                self._process = self._ctx.Process(
                    target=_serve,
                    args=(
                        self.factory,
                        (self.model_id, self.model_revision),
                        self._request,
                        self._request_length,
                        self._response,
                        self._response_length,
                        self._pending,
                        self._complete,
                        self._stopping,
                    ),
                    daemon=True,
                )
                self._process.start()
                self._started = True
            pid = self._process.pid
            self._pending.set()
            while True:
                remaining = self.config.timeout_seconds - (time.monotonic() - started)
                if remaining <= 0:
                    status = "TIMEOUT"
                    raise TimeoutError("guard deadline exceeded")
                if self._complete.wait(min(remaining, 0.02)):
                    break
                if not self._process.is_alive():
                    status = "WORKER_CRASH"
                    raise RuntimeError("guard worker exited")
            status = "INVALID_PACKET"
            size = self._response_length.value
            if not 0 < size <= MAX_RESPONSE_BYTES:
                raise ValueError("guard response size")
            packet = json.loads(bytes(self._response[:size]))
            if packet["sequence"] != sequence:
                raise ValueError("guard response sequence mismatch")
            timing = {k: float(packet[k]) for k in ("load_seconds", "generation_seconds")}
            if "error" in packet:
                status = packet["error"] if packet["error"] in ERRORS else "INVALID_PACKET"
                raise RuntimeError("guard backend failed")
            response = ModelResponse.model_validate(packet["response"])
            if (response.model_id, response.model_revision) != (self.model_id, self.model_revision):
                status = "IDENTITY_CHANGED"
                raise RuntimeError("guard response identity changed")
            if time.monotonic() - started > self.config.timeout_seconds:
                status = "TIMEOUT"
                raise TimeoutError("guard deadline exceeded")
            status = "OK"
            return response
        except (KeyboardInterrupt, SystemExit):
            status = "INTERRUPTED"
            raise
        finally:
            reaped = False
            try:
                if status != "OK":
                    self._retired = True
                    reaped = self._cleanup(graceful=False)
                self.attempts.append(
                    {
                        "sequence": len(self.attempts) + 1,
                        "status": status,
                        "pid": pid,
                        "cold_start": cold,
                        "reaped": reaped,
                        "worker_retained": status == "OK",
                        **timing,
                        "elapsed_seconds": time.monotonic() - started,
                        "execution_config_sha256": self.config.identity,
                        "request_sha256": text_hash(canonical_json(messages)),
                        "generation_sha256": text_hash(canonical_json(config.model_dump())),
                    }
                )
                if status != "OK" and not reaped:
                    raise RuntimeError("guard cancellation failed")
            finally:
                self._lock.release()


class WarmModelGuard(ModelGuard):
    def __init__(self, backend: WarmGuardBackend) -> None:
        super().__init__(backend)
        self.warm_backend = backend
        self._classification_lock = threading.Lock()

    def classify(self, request: GuardInput) -> GuardOutcome:
        if not self._classification_lock.acquire(blocking=False):
            raise RuntimeError("concurrent guard classifications are unsupported")
        try:
            if self.warm_backend.retired:
                self._cache.clear()
            outcome = super().classify(request)
            if outcome.cache_hit and self.warm_backend.retired:
                outcome = GuardOutcome(
                    status="ERROR", error_code="BACKEND_FAILURE", cache_key=outcome.cache_key
                )
            if outcome.status == "ERROR":
                self._cache.clear()
                self.warm_backend.retire()
            return outcome
        finally:
            self._classification_lock.release()
