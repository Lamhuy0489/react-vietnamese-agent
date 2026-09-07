"""Cold, process-isolated guard generation with bounded cancellation, no retries."""

from __future__ import annotations

import ctypes
import json
import math
import multiprocessing as mp
import os
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.security_v1.guard import GuardInput, GuardOutcome, ModelGuard

MAX_RESPONSE_BYTES = 65_536


@dataclass(frozen=True)
class ProcessGuardConfig:
    model_id: str
    model_revision: str
    timeout_seconds: float = 120.0
    terminate_grace_seconds: float = 0.5
    kill_grace_seconds: float = 1.0

    def __post_init__(self) -> None:
        if not self.model_id.strip() or not self.model_revision.strip():
            raise ValueError("explicit pinned guard identity required")
        for value in (self.timeout_seconds, self.terminate_grace_seconds, self.kill_grace_seconds):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("finite positive deadline/grace required")

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(asdict(self)))


def _generate_child(
    factory: Callable[[], LLMBackend],
    messages: list[dict[str, str]],
    generation: dict[str, Any],
    identity: tuple[str, str],
    buffer: Any,
    length: Any,
) -> None:
    # Factory/backend output and exception messages may contain arbitrary content.
    with open(os.devnull, "w") as sink:
        os.dup2(sink.fileno(), 1)
        os.dup2(sink.fileno(), 2)
    try:
        packet: dict[str, Any]
        backend = factory()
        if (backend.model_id, backend.model_revision) != identity:
            packet = {"error": "IDENTITY_CHANGED"}
        else:
            response = backend.generate(messages, GenerationConfig.model_validate(generation))
            if (backend.model_id, backend.model_revision) != identity or (
                response.model_id,
                response.model_revision,
            ) != identity:
                packet = {"error": "IDENTITY_CHANGED"}
            else:
                packet = {"response": response.model_dump(mode="json")}
    except Exception:  # Deliberately sanitize the untrusted backend boundary.
        packet = {"error": "BACKEND_FAILURE"}
    encoded = canonical_json(packet).encode("utf-8")
    if len(encoded) > MAX_RESPONSE_BYTES:
        encoded = b'{"error":"RESPONSE_TOO_LARGE"}'
    buffer[: len(encoded)] = encoded
    length.value = len(encoded)


class ProcessGuardBackend:
    """Use via ModelGuard; factory owns local inference, never a detached service."""

    def __init__(self, factory: Callable[[], LLMBackend], config: ProcessGuardConfig) -> None:
        self.factory = factory
        self.config = config
        self.model_id, self.model_revision = config.model_id, config.model_revision
        self.attempts: list[dict[str, Any]] = []
        self.retired = False

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if self.retired:
            raise RuntimeError("guard worker retired; no automatic retry")
        ctx = mp.get_context("spawn")
        buffer = ctx.RawArray(ctypes.c_ubyte, MAX_RESPONSE_BYTES)
        length = ctx.RawValue(ctypes.c_int, -1)
        process = ctx.Process(
            target=_generate_child,
            args=(
                self.factory,
                messages,
                config.model_dump(),
                (self.config.model_id, self.config.model_revision),
                buffer,
                length,
            ),
            daemon=True,
        )
        started = time.monotonic()
        status = "START_FAILURE"
        reaped = True
        pid: int | None = None
        try:
            process.start()
            pid = process.pid
            process.join(max(0.0, self.config.timeout_seconds - (time.monotonic() - started)))
            if process.is_alive():
                status = "TIMEOUT"
                raise TimeoutError("guard deadline exceeded")
            status = "WORKER_CRASH"
            if process.exitcode != 0 or not 0 < length.value <= MAX_RESPONSE_BYTES:
                raise RuntimeError("guard worker failed")
            packet = json.loads(bytes(buffer[: length.value]))
            if "error" in packet:
                status = packet["error"]
                raise RuntimeError("guard worker failed")
            response = ModelResponse.model_validate(packet["response"])
            status = "OK"
            return response
        finally:
            if pid is not None:
                if process.is_alive():
                    process.terminate()
                    process.join(self.config.terminate_grace_seconds)
                if process.is_alive():
                    process.kill()
                    process.join(self.config.kill_grace_seconds)
                reaped = not process.is_alive()
            if status != "OK" or not reaped:
                self.retired = True
            self.attempts.append(
                {
                    "sequence": len(self.attempts) + 1,
                    "status": status if reaped else "CANCELLATION_FAILED",
                    "pid": pid,
                    "reaped": reaped,
                    "elapsed_seconds": time.monotonic() - started,
                    "execution_config_sha256": self.config.identity,
                    "request_sha256": text_hash(canonical_json(messages)),
                    "generation_sha256": text_hash(canonical_json(config.model_dump())),
                }
            )
            if reaped:
                process.close()


class ProcessModelGuard(ModelGuard):
    def __init__(self, backend: ProcessGuardBackend) -> None:
        super().__init__(backend)
        self.process_backend = backend

    def classify(self, request: GuardInput) -> GuardOutcome:
        if self.process_backend.retired:
            self._cache.clear()  # No stale SAFE cache after losing the worker boundary.
        return super().classify(request)
