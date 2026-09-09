"""Task-owned pair cancellation diagnostics; model generation is never invoked."""

from __future__ import annotations

import json
import math
import os
import signal
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.model_pair_probe_v1 import (
    MIN_RESIDENT,
    TOLERANCE,
    PairObserver,
    validate_memory,
)
from react_agent.llm.model_pair_v1 import ModelPair, Role

PLAN = ("agent_busy", "guard_busy", "guard_ignore_term")
BUSY = "__HOST_PAIR_CANCELLATION_BUSY_V1__"


def busy_role(trial: str) -> Role:
    if trial not in PLAN:
        raise ValueError("unknown cancellation trial")
    return "agent" if trial == "agent_busy" else "guard"


@dataclass(frozen=True)
class BusyFactory:
    factory: Callable[[], LLMBackend]
    role: Role
    trial: str
    output: Path
    actual_cuda: bool = False

    def __post_init__(self) -> None:
        busy_role(self.trial)
        if self.role not in ("agent", "guard") or type(self.actual_cuda) is not bool:
            raise ValueError("explicit role and CUDA mode required")

    def __call__(self) -> LLMBackend:
        return BusyBackend(self.factory(), self)


class BusyBackend:
    def __init__(self, backend: LLMBackend, spec: BusyFactory) -> None:
        self.backend, self.spec = backend, spec
        self.model_id, self.model_revision = backend.model_id, backend.model_revision

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        spec = self.spec
        if (
            messages != [{"role": "user", "content": BUSY}]
            or config != GenerationConfig()
            or spec.role != busy_role(spec.trial)
        ):
            raise ValueError("only selected host busy command allowed")
        ignored = spec.trial == "guard_ignore_term"
        if ignored:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        devices = (0, 1) if spec.role == "agent" else (1,)
        tensors = []
        torch: Any = None
        if spec.actual_cuda:
            import torch as cuda_torch  # type: ignore[import-not-found]

            torch = cuda_torch

            for device in devices:
                tensor = torch.ones((256, 256), device=f"cuda:{device}", dtype=torch.float16)
                if (tensor @ tensor)[0, 0].item() != 256:
                    raise RuntimeError("busy CUDA operation failed")
                torch.cuda.synchronize(device)
                tensors.append((device, tensor))
        no_links(spec.output)
        write_receipt(
            spec.output / "busy_entered.json",
            {
                "trial": spec.trial,
                "role": spec.role,
                "pid": os.getpid(),
                "ignore_sigterm": ignored,
                "actual_cuda_operation": spec.actual_cuda,
                "devices": list(devices) if spec.actual_cuda else [],
                "model_generation_calls": 0,
            },
        )
        while True:
            for device, tensor in tensors:
                result = tensor @ tensor
                torch.cuda.synchronize(device)
                del result
            time.sleep(0.005)


def matching_baseline(before: list[dict[str, int]], after: list[dict[str, int]]) -> bool:
    validate_memory(before)
    validate_memory(after)
    return all(
        before[i]["total_bytes"] == after[i]["total_bytes"]
        and abs(before[i]["free_bytes"] - after[i]["free_bytes"]) <= TOLERANCE
        for i in (0, 1)
    )


def run_trial(
    root: Path,
    trial: str,
    pair: ModelPair,
    observer: PairObserver,
    baseline: list[dict[str, int]],
    *,
    actual_cuda: bool,
) -> dict[str, Any]:
    """Own cleanup even on interruption; preserve partials and propagate BaseException."""
    role = busy_role(trial)
    row: dict[str, Any] = {"trial": trial, "valid": False, "status": "NOT_COMPLETED"}
    samples: list[list[dict[str, int]]] = []
    before: list[dict[str, int]] = []
    started = time.monotonic()
    try:
        if pair.state != "NEW":
            raise ValueError("fresh pair required")
        before = observer.sample("baseline")
        if not matching_baseline(baseline, before):
            raise ValueError("suite baseline drift")
        write_receipt(root / "baseline.json", {"memory": before})
        write_receipt(
            root / "pair_config.json", {"sha256": pair.config.sha256, "values": asdict(pair.config)}
        )
        pair.start()
        resident = observer.sample("resident")
        validate_memory(resident)
        write_receipt(root / "ready.json", {"pair": pair.snapshot(), "memory": resident})
        if any(
            before[i]["total_bytes"] != resident[i]["total_bytes"]
            or before[i]["free_bytes"] - resident[i]["free_bytes"] < MIN_RESIDENT[i]
            for i in (0, 1)
        ):
            raise ValueError("combined model residency not observable")
        try:
            pair.generate(role, [{"role": "user", "content": BUSY}], GenerationConfig())
        except TimeoutError:
            row["timeout_observed"] = True
        else:
            raise ValueError("expected timeout missing")
        snapshot = pair.snapshot()
        attempt = snapshot["workers"][role]["attempts"][-1]
        marker = json.loads((root / "busy_entered.json").read_text())
        expected = {
            "trial": trial,
            "role": role,
            "pid": attempt["pid"],
            "ignore_sigterm": trial == "guard_ignore_term",
            "actual_cuda_operation": actual_cuda,
            "devices": ([0, 1] if role == "agent" else [1]) if actual_cuda else [],
            "model_generation_calls": 0,
        }
        if (
            marker != expected
            or attempt["status"] != "TIMEOUT"
            or attempt["elapsed_seconds"] < pair.config.execution(role, cold=False).timeout_seconds
        ):
            raise ValueError("busy timeout identity mismatch")
        row["status"] = "EXECUTION_COMPLETE"
    except Exception as exc:  # Only sanitized class, no model text or silent retry.
        row.update(status="ERROR", error_class=type(exc).__name__)
    finally:
        cleanup_error = False
        cleanup_interrupt: BaseException | None = None
        try:
            pair.close()
        except BaseException as exc:
            cleanup_error = True
            row.update(status="CLEANUP_ERROR", error_class=type(exc).__name__)
            if not isinstance(exc, Exception):
                cleanup_interrupt = exc
        snapshot = pair.snapshot()
        write_receipt(root / "closed.json", snapshot)
        workers = snapshot["workers"]
        reaped = all(
            w["closed"]
            and not w["handle_pending"]
            and len(w["lifecycle"]) == 1
            and w["lifecycle"][0]["reaped"]
            for w in workers.values()
        )
        row.update(reaped=reaped, cleanup_error=cleanup_error)
        if reaped and before and not cleanup_error:
            try:
                for i in range(6):
                    if i:
                        time.sleep(observer.interval)
                    sample = observer.sample("recovery")
                    validate_memory(sample)
                    write_receipt(
                        root / f"recovery_{i}.json",
                        {"memory": sample, "elapsed_seconds": time.monotonic() - started},
                    )
                    samples.append(sample)
            except Exception as exc:
                row.update(status="OBSERVER_ERROR", error_class=type(exc).__name__)
        recovered = len(samples) == 6 and all(matching_baseline(before, s) for s in samples[-3:])
        events = workers[role]["lifecycle"]
        method, code = ("KILL", -9) if trial == "guard_ignore_term" else ("TERMINATE", -15)
        forced_ok = len(events) == 1 and (events[0]["method"], events[0]["exitcode"]) == (
            method,
            code,
        )
        row.update(recovery_valid=recovered, forced_method_valid=forced_ok)
        row["valid"] = (
            row["status"] == "EXECUTION_COMPLETE"
            and reaped
            and recovered
            and forced_ok
            and not cleanup_error
        )
        write_receipt(root / "trial.json", row)
        if cleanup_interrupt is not None:
            raise cleanup_interrupt
    return row


def run_pair_cancellation(
    output: Path,
    factory: Callable[[str, Path], ModelPair],
    observer: PairObserver,
    identity: dict[str, Any],
    *,
    actual_cuda: bool = False,
) -> dict[str, Any]:
    no_links(output)
    if (
        type(actual_cuda) is not bool
        or type(observer.interval) not in (int, float)
        or not math.isfinite(observer.interval)
        or observer.interval < 0
        or (actual_cuda and observer.interval != 1.0)
    ):
        raise ValueError("explicit CUDA mode and observation cadence required")
    output.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, Any]] = []
    error_class = None
    try:
        baseline = observer.sample("baseline")
        validate_memory(baseline)
        write_receipt(
            output / "manifest.json",
            {
                "protocol": "pair_cancellation_v1",
                "plan": PLAN,
                "identity": identity,
                "actual_cuda": actual_cuda,
                "initial_memory": baseline,
                "sample_interval_seconds": observer.interval,
                "recovery_samples": 6,
                "tolerance_bytes": TOLERANCE,
                "min_resident_bytes": MIN_RESIDENT,
                "model_generation_calls": 0,
                "automatic_retry": False,
            },
        )
        for trial in PLAN:
            if rows and not rows[-1]["valid"]:
                rows.append({"trial": trial, "valid": False, "status": "SKIPPED_AFTER_FAILURE"})
                continue
            root = output / trial
            root.mkdir()
            pair = factory(trial, root)
            rows.append(run_trial(root, trial, pair, observer, baseline, actual_cuda=actual_cuda))
    except Exception as exc:
        error_class = type(exc).__name__
    finally:
        summary = {
            "protocol": "pair_cancellation_v1",
            "rows": rows,
            "valid": len(rows) == len(PLAN) and all(r["valid"] for r in rows),
            "phase5_accepted": False,
            "model_generation_calls": 0,
            "error_class": error_class,
            "scope": "Cancellation with sibling resident; not model generation or context stress",
        }
        write_receipt(output / "summary.json", summary)
    return summary
