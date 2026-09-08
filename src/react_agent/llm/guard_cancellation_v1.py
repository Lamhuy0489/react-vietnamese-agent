"""Fixed technical cancellation probe; retains HF weights but never generates text."""

from __future__ import annotations

import json
import os
import signal
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.guard_hf_v1 import GuardHFConfig, GuardHFFactory
from react_agent.llm.guard_probe_v1 import GENERATION, write_json
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.security_v1.warm_guard import WarmGuardBackend, WarmGuardConfig

PLAN = ("resident_close", "busy_timeout", "ignore_term_timeout")
TOLERANCE = 256 * 1024**2
MIN_RESIDENCY = 2 * 1024**3
SAMPLES = 6
ACK = "RESIDENT_ACK_NO_MODEL_GENERATION"


class Observer(Protocol):
    interval: float

    def sample(self, phase: str) -> dict[str, int]: ...


class CUDAObserver:
    interval = 1.0

    def __init__(self) -> None:
        import torch  # type: ignore[import-not-found]

        if torch.cuda.device_count() != 2 or any(
            "T4" not in torch.cuda.get_device_name(i) for i in (0, 1)
        ):
            raise RuntimeError("two T4 GPUs required")
        self.torch = torch
        value = torch.ones(2, device="cuda:1")
        if value.sum().item() != 2:
            raise RuntimeError("observer CUDA operation failed")
        del value
        torch.cuda.synchronize(1)
        torch.cuda.empty_cache()

    def sample(self, phase: str) -> dict[str, int]:
        free, total = self.torch.cuda.mem_get_info(1)
        return {"free_bytes": int(free), "total_bytes": int(total)}


@dataclass
class StubObserver:
    interval: float = 0.0
    recovery_failure: bool = False

    def sample(self, phase: str) -> dict[str, int]:
        used = 3 * 1024**3 if phase == "resident" else 0
        if self.recovery_failure and phase == "after":
            used = 1024**3
        return {"free_bytes": 14 * 1024**3 - used, "total_bytes": 16 * 1024**3}


class ResidentBackend:
    def __init__(
        self, backend: Any, trial: str, root: Path, model_id: str, revision: str, failure: str = ""
    ) -> None:
        self.backend, self.trial, self.root = backend, trial, root
        self.model_id, self.model_revision = model_id, revision
        self.failure = failure

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if config != GENERATION:
            raise ValueError("fixed transport generation identity required")
        if messages == [{"role": "user", "content": "resident_ack"}]:
            return ModelResponse(
                text=ACK, model_id=self.model_id, model_revision=self.model_revision
            )
        if messages != [{"role": "user", "content": "busy"}]:
            raise ValueError("unsupported probe command")
        if self.failure == "busy_error":
            raise RuntimeError("synthetic busy failure")
        ignored = self.trial == "ignore_term_timeout"
        if ignored:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        tensor = None
        if self.backend is not None:
            torch = self.backend.torch
            tensor = torch.ones((256, 256), device="cuda:1", dtype=torch.float16)
            if (tensor @ tensor)[0, 0].item() != 256:
                raise RuntimeError("busy CUDA operation failed")
            torch.cuda.synchronize(1)
        write_json(
            self.root / "busy_entered.json",
            {
                "pid": os.getpid(),
                "ignore_sigterm": ignored,
                "actual_cuda_operation": self.backend is not None,
                "model_generation_calls": 0,
            },
        )
        while True:
            if tensor is not None:
                result = tensor @ tensor
                self.backend.torch.cuda.synchronize(1)
                del result
            time.sleep(0.005)


@dataclass(frozen=True)
class ResidentFactory:
    trial: str
    output: Path
    snapshot: GuardSnapshot | None = None
    model_path: Path | None = None
    failure: str = ""

    def __call__(self) -> LLMBackend:
        if self.failure == "load_error":
            raise RuntimeError("synthetic load failure")
        backend = None
        model_id, revision = "synthetic-resident-stub", "v1"
        if self.snapshot is not None:
            if self.model_path is None:
                raise ValueError("offline model required")
            backend = GuardHFFactory(
                self.model_path, self.snapshot, GuardHFConfig(), self.output / "hf_metrics.jsonl"
            )()
            model_id, revision = self.snapshot.model_id, self.snapshot.model_revision
            value = backend.torch.ones(2, device="cuda:1")
            if value.sum().item() != 2:
                raise RuntimeError("resident CUDA operation failed")
            del value
            backend.torch.cuda.synchronize(1)
        write_json(
            self.output / "resident_ready.json",
            {
                "pid": os.getpid(),
                "model_id": model_id,
                "model_revision": revision,
                "actual_cuda_operation": backend is not None,
                "model_generation_calls": 0,
            },
        )
        return ResidentBackend(backend, self.trial, self.output, model_id, revision, self.failure)


def recovery_valid(before: dict[str, int], samples: list[dict[str, int]]) -> bool:
    return len(samples) == SAMPLES and all(
        s["total_bytes"] == before["total_bytes"]
        and abs(s["free_bytes"] - before["free_bytes"]) <= TOLERANCE
        for s in samples[-3:]
    )


def run_cancellation(
    output: Path,
    factories: Callable[[str, Path], Callable[[], LLMBackend]],
    observer: Observer,
    config: WarmGuardConfig,
    identity: dict[str, Any],
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    initial = observer.sample("initial")
    write_json(
        output / "manifest.json",
        {
            "protocol": "guard_cancellation_v1",
            "plan": PLAN,
            "identity": identity,
            "execution_config_sha256": config.identity,
            "timeout_seconds": config.timeout_seconds,
            "terminate_grace_seconds": config.terminate_grace_seconds,
            "kill_grace_seconds": config.kill_grace_seconds,
            "generation": GENERATION.model_dump(),
            "model_generation_calls": 0,
            "recovery_samples": SAMPLES,
            "sample_interval_seconds": observer.interval,
            "memory_tolerance_bytes": TOLERANCE,
            "min_residency_bytes": MIN_RESIDENCY,
            "initial_memory": initial,
            "automatic_retry": False,
        },
    )
    rows: list[dict[str, Any]] = []
    halted = False
    for name in PLAN:
        if halted:
            rows.append({"trial": name, "valid": False, "status": "SKIPPED_AFTER_FAILURE"})
            continue
        root = output / name
        root.mkdir()
        before = observer.sample("before")
        worker = WarmGuardBackend(factories(name, root), config)
        row: dict[str, Any] = {
            "trial": name,
            "before": before,
            "valid": False,
            "status": "NOT_COMPLETED",
        }
        write_json(root / "before.json", before)
        try:
            if (
                before["total_bytes"] != initial["total_bytes"]
                or abs(before["free_bytes"] - initial["free_bytes"]) > TOLERANCE
            ):
                raise ValueError("observer baseline drift")
            response = worker.generate([{"role": "user", "content": "resident_ack"}], GENERATION)
            if response.text != ACK:
                raise ValueError("residency ACK failed")
            row["resident"] = observer.sample("resident")
            write_json(root / "resident_memory.json", row["resident"])
            if before["free_bytes"] - row["resident"]["free_bytes"] < MIN_RESIDENCY:
                raise ValueError("resident model not observable")
            if name != "resident_close":
                try:
                    worker.generate([{"role": "user", "content": "busy"}], GENERATION)
                except TimeoutError:
                    row["timeout_observed"] = True
                else:
                    raise ValueError("expected timeout missing")
                entered = json.loads((root / "busy_entered.json").read_text())
                if entered["pid"] != worker.attempts[-1]["pid"]:
                    raise ValueError("busy worker identity mismatch")
            row["status"] = "EXECUTION_COMPLETE"
        except Exception as exc:  # Class only; retain partials, never retry.
            row.update(status="ERROR", error_class=type(exc).__name__)
        finally:
            try:
                worker.close()
            except Exception as exc:
                row.update(status="CLEANUP_ERROR", error_class=type(exc).__name__)
            row.update(
                attempts=worker.attempts, lifecycle=worker.lifecycle_events, closed=worker.closed
            )
            reaped = bool(worker.lifecycle_events) and all(
                event["reaped"] for event in worker.lifecycle_events
            )
            row["reaped"] = reaped
            samples = []
            if reaped:
                try:
                    for index in range(SAMPLES):
                        if index:
                            time.sleep(observer.interval)
                        samples.append(observer.sample("after"))
                except Exception as exc:
                    row.update(status="OBSERVER_ERROR", error_class=type(exc).__name__)
            row["after_samples"] = samples
            row["recovery_valid"] = reaped and recovery_valid(before, samples)
            row["graceful"] = reaped and worker.lifecycle_events[-1]["method"] == "GRACEFUL"
            forced_ok = name != "ignore_term_timeout" or (
                reaped
                and worker.lifecycle_events[-1]["method"] == "KILL"
                and worker.lifecycle_events[-1]["exitcode"] == -9
            )
            row["valid"] = (
                row["status"] == "EXECUTION_COMPLETE" and row["recovery_valid"] and forced_ok
            )
            write_json(root / "trial.json", row)
        rows.append(row)
        halted = not row["valid"]
    summary = {
        "protocol": "guard_cancellation_v1",
        "valid": all(r["valid"] for r in rows),
        "phase5_accepted": False,
        "model_generation_calls": 0,
        "rows": rows,
        "scope": "Resource lifecycle only; no guard quality or agent coexistence",
    }
    write_json(output / "summary.json", summary)
    return summary
