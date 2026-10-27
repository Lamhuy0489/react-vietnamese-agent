"""Per-request HF cancellation with explicit device synchronization, no server startup."""
from __future__ import annotations

import importlib
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from react_agent.serving.structured_api_v1 import HFEngine, ServiceError, Spec


@dataclass(frozen=True)
class EngineOutcome:
    result: dict[str, Any]
    http_status: int
    quiescent: bool
    reusable: bool


class QuiescentEngine:
    """Keep the slot occupied through cleanup, even after generation errors.

    The synchronization callback must cover every device used by the generator.
    A successful callback is a worker assertion, not external GPU attestation.
    """

    def __init__(self, generate: Callable[[Spec, threading.Event], dict[str, Any]],
                 synchronize: Callable[[], None]) -> None:
        self.generate, self.synchronize = generate, synchronize
        self.lock = threading.Lock()
        self.retired = False

    def __call__(self, spec: Spec, stop: threading.Event) -> EngineOutcome:
        if not self.lock.acquire(blocking=False):
            raise ServiceError("ENGINE_BUSY", 429)
        try:
            if self.retired:
                return EngineOutcome({"error": {"code": "ENGINE_RETIRED"}}, 503, False, False)
            reusable = True
            quiescent = False
            try:
                if stop.is_set():
                    raise ServiceError("CANCELLED", 409)
                result, code = self.generate(spec, stop), 200
            except ServiceError as exc:
                result, code = {"error": {"code": exc.code}}, exc.status
            except Exception:
                # Unspecified native failures retire this model instance even if sync succeeds.
                result, code, reusable = {"error": {"code": "GENERATION_FAILED"}}, 500, False
            except BaseException:
                self.retired = True
                raise
            finally:
                try:
                    self.synchronize()
                    quiescent = True
                except Exception:
                    self.retired = True
                    reusable = False
                except BaseException:
                    self.retired = True
                    raise
            if not quiescent:
                return EngineOutcome({"error": {"code": "QUIESCENCE_UNKNOWN"}}, 503, False, False)
            if not reusable:
                self.retired = True
            return EngineOutcome(result, code, True, reusable)
        finally:
            self.lock.release()


def load_hf_engine(cfg: dict[str, Any]) -> tuple[QuiescentEngine, dict[str, Any]]:
    """Explicit native load/warmup using frozen v1 decoding and two-T4 checks."""
    engine = HFEngine(cfg, threading.Event())
    torch = importlib.import_module("torch")

    def synchronize() -> None:
        # Device arguments are required: the default only waits for the current device.
        failed = False
        for device in (0, 1):
            try:
                torch.cuda.synchronize(device)
            except Exception:
                failed = True
        if failed:
            raise ServiceError("CUDA_SYNCHRONIZE_FAILED", 503)

    synchronize()  # Include warmup in admission before any service is exposed.

    def generate(spec: Spec, stop: threading.Event) -> dict[str, Any]:
        # Only QuiescentEngine owns this HFEngine; its lock covers assignment and sync.
        engine.stop = stop
        return engine.generate(spec)

    return QuiescentEngine(generate, synchronize), dict(engine.metadata)
