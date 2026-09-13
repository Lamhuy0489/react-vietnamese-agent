"""Versioned stop observation and bounded graceful budget; frozen v1 is unchanged."""

from __future__ import annotations

import ctypes
import json
import math
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.security_v1.process_guard import MAX_RESPONSE_BYTES
from react_agent.security_v1.warm_guard import (
    ERRORS,
    MAX_REQUEST_BYTES,
    WarmGuardBackend,
    WarmGuardConfig,
    _serve,
)


@dataclass(frozen=True)
class ShutdownConfig(WarmGuardConfig):
    """Separate normal shutdown from cancellation; part of the execution identity."""

    graceful_shutdown_seconds: float = 2.0
    lifecycle: str = field(default="task_local_observed_shutdown_v2", init=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        if (
            isinstance(self.graceful_shutdown_seconds, bool)
            or not math.isfinite(self.graceful_shutdown_seconds)
            or self.graceful_shutdown_seconds <= 0
        ):
            raise ValueError("finite positive graceful shutdown budget required")


@dataclass
class _ObservedStop:
    event: Any
    received: Any

    def is_set(self) -> bool:
        stopped = bool(self.event.is_set())
        if stopped and self.received.value < 0:
            self.received.value = time.monotonic()
        return stopped


def _observed_serve(
    factory: Callable[[], LLMBackend],
    identity: tuple[str, str],
    request: Any,
    request_length: Any,
    response: Any,
    response_length: Any,
    pending: Any,
    complete: Any,
    stopping: Any,
    received: Any,
    returned: Any,
) -> None:
    # Observe the frozen transport loop, without changing prompts or generation.
    # Returning from _serve includes destruction of its local backend reference,
    # but is NOT a process-exit, CUDA recovery or multiprocessing-finalizer ACK.
    try:
        _serve(
            factory,
            identity,
            request,
            request_length,
            response,
            response_length,
            pending,
            complete,
            _ObservedStop(stopping, received),
        )
    finally:
        returned.value = time.monotonic()


class ShutdownBackend(WarmGuardBackend):
    """Standalone opt-in worker; not automatically adopted by native ModelPair."""

    config: ShutdownConfig

    def __init__(self, factory: Callable[[], LLMBackend], config: ShutdownConfig) -> None:
        if not isinstance(config, ShutdownConfig):
            raise TypeError("explicit versioned shutdown config required")
        super().__init__(factory, config)
        self._stop_received: Any = self._ctx.RawValue(ctypes.c_double, -1.0)
        self._serve_returned: Any = self._ctx.RawValue(ctypes.c_double, -1.0)

    def _cleanup(self, *, graceful: bool) -> bool:
        process = self._process
        if process is None:
            return True
        started = time.monotonic()
        pid = process.pid
        requested_at: float | None = None
        method = "NOT_STARTED" if pid is None else "EXITED"
        if pid is not None:
            if graceful and process.is_alive():
                requested_at = time.monotonic()
                self._stopping.set()
                self._pending.set()
                process.join(self.config.graceful_shutdown_seconds)
                method = "GRACEFUL" if process.exitcode == 0 else "EXITED"
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
        received = float(self._stop_received.value)
        returned = float(self._serve_returned.value)
        ended = time.monotonic()
        acknowledged = requested_at is not None and requested_at <= received <= ended
        # A successful natural exit must not masquerade as an acknowledged stop.
        if method == "GRACEFUL" and not (
            acknowledged and requested_at is not None and requested_at <= returned <= ended
        ):
            method = "EXITED"
        self.lifecycle_events.append(
            {
                "schema_version": "worker_shutdown_v2",
                "sequence": len(self.lifecycle_events) + 1,
                "pid": pid,
                "method": method,
                "reaped": reaped,
                "exitcode": process.exitcode,
                "elapsed_seconds": ended - started,
                "graceful_requested": requested_at is not None,
                "graceful_shutdown_seconds": self.config.graceful_shutdown_seconds,
                "stop_received": acknowledged,
                "stop_received_seconds": received - requested_at
                if acknowledged and requested_at is not None
                else None,
                "serve_returned": returned >= 0,
                "serve_returned_after_stop_seconds": returned - requested_at
                if requested_at is not None and requested_at <= returned <= ended
                else None,
            }
        )
        if reaped:
            process.close()
            self._process = None
        return reaped

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
                    target=_observed_serve,
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
                        self._stop_received,
                        self._serve_returned,
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
