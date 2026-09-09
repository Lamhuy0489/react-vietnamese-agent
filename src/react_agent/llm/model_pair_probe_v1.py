"""Durable pair residency/small-context probe; quality and long context are separate."""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.model_pair_v1 import ModelPair
from react_agent.security_v1.guard import PROMPT, GuardInput

TOLERANCE = 256 * 1024**2
MIN_RESIDENT = (8 * 1024**3, 6 * 1024**3)


class PairObserver(Protocol):
    interval: float

    def sample(self, phase: str) -> list[dict[str, int]]: ...


@dataclass(frozen=True)
class SyntheticPairFactory:
    role: str
    evidence_root: Path

    def __call__(self) -> LLMBackend:
        write_receipt(
            self.evidence_root / f"{self.role}_synthetic_load.json",
            {
                "pid": os.getpid(),
                "actual_model_load": False,
                "role": self.role,
            },
        )
        return SyntheticPairBackend(self.role)


class SyntheticPairBackend:
    def __init__(self, role: str) -> None:
        self.model_id, self.model_revision = "synthetic-" + role, "v1"

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        return ModelResponse(
            text="synthetic transport response",
            model_id=self.model_id,
            model_revision=self.model_revision,
        )


class SyntheticPairObserver:
    interval = 0.0

    def sample(self, phase: str) -> list[dict[str, int]]:
        return [
            {
                "device": i,
                "total_bytes": 16 * 1024**3,
                "free_bytes": 14 * 1024**3
                - (MIN_RESIDENT[i] if phase in {"resident", "after_call"} else 0),
            }
            for i in (0, 1)
        ]


class PairCUDAObserver:
    interval = 1.0

    def __init__(self) -> None:
        import torch  # type: ignore[import-not-found]

        if torch.cuda.device_count() != 2 or any(
            torch.cuda.get_device_name(i) not in {"T4", "Tesla T4", "NVIDIA T4"} for i in (0, 1)
        ):
            raise RuntimeError("two T4 devices required")
        self.torch = torch
        for device in (0, 1):
            value = torch.ones(2, device=f"cuda:{device}")
            if value.sum().item() != 2:
                raise RuntimeError("actual CUDA operation failed")
            del value
            torch.cuda.synchronize(device)
            torch.cuda.empty_cache()

    def sample(self, phase: str) -> list[dict[str, int]]:
        rows = []
        for device in (0, 1):
            free, total = self.torch.cuda.mem_get_info(device)
            rows.append({"device": device, "free_bytes": int(free), "total_bytes": int(total)})
        return rows


def validate_memory(rows: list[dict[str, int]]) -> None:
    if len(rows) != 2 or [r.get("device") for r in rows] != [0, 1]:
        raise ValueError("two ordered device observations required")
    for row in rows:
        if (
            set(row) != {"device", "free_bytes", "total_bytes"}
            or any(type(v) is not int for v in row.values())
            or not 0 <= row["free_bytes"] <= row["total_bytes"]
            or row["total_bytes"] <= 0
        ):
            raise ValueError("invalid device memory sample")


def technical_inputs() -> dict[str, list[dict[str, str]]]:
    guard = GuardInput(
        user_instruction="Tóm tắt thông báo công khai giả lập.",
        source_type="document",
        candidate_content="Thông báo giả lập: thư viện mở cửa lúc 8 giờ sáng.",
    )
    return {
        "agent": [
            {"role": "user", "content": "Trả lời ngắn bằng tiếng Việt: một cộng một bằng mấy?"}
        ],
        "guard": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": canonical_json(guard.model_dump(mode="json"))},
        ],
    }


def run_pair_probe(
    output: Path, pair: ModelPair, observer: PairObserver, identity: dict[str, Any]
) -> dict[str, Any]:
    """One fresh pair, two small synthetic calls, finally-cleanup; no retry/resume."""
    no_links(output)
    if pair.state != "NEW":
        raise ValueError("probe requires a fresh unstarted pair")
    if (
        type(observer.interval) not in (float, int)
        or not math.isfinite(observer.interval)
        or observer.interval < 0
    ):
        raise ValueError("valid observation interval required")
    output.mkdir(parents=True, exist_ok=False)
    calls = technical_inputs()
    write_receipt(
        output / "manifest.json",
        {
            "protocol": "model_pair_residency_probe_v1",
            "identity": identity,
            "pair_config_sha256": pair.config.sha256,
            "inputs_sha256": text_hash(canonical_json(calls)),
            "generation": {
                "agent": GenerationConfig().model_dump(),
                "guard": GenerationConfig(max_new_tokens=128).model_dump(),
            },
            "order": [
                "baseline",
                "ready_agent_then_guard",
                "agent_call",
                "guard_call",
                "close",
                "recovery",
            ],
            "min_resident_bytes": MIN_RESIDENT,
            "recovery_tolerance_bytes": TOLERANCE,
            "sample_interval_seconds": observer.interval,
            "recovery_samples": 6,
            "automatic_retry": False,
            "benchmark_tasks": 0,
            "test_payloads_parsed": 0,
        },
    )
    rows: list[dict[str, Any]] = []
    baseline: list[dict[str, int]] = []
    samples: list[list[dict[str, int]]] = []
    status = "NOT_COMPLETED"
    cleanup_error = False
    started = time.monotonic()
    try:
        initial = observer.sample("baseline")
        validate_memory(initial)
        baseline = initial
        write_receipt(output / "baseline.json", {"memory": baseline})
        pair.start()
        resident = observer.sample("resident")
        validate_memory(resident)
        write_receipt(output / "ready.json", {"pair": pair.snapshot(), "memory": resident})
        if any(
            resident[i]["total_bytes"] != baseline[i]["total_bytes"]
            or baseline[i]["free_bytes"] - resident[i]["free_bytes"] < MIN_RESIDENT[i]
            for i in (0, 1)
        ):
            raise RuntimeError("combined model residency not observable")
        for role in ("agent", "guard"):
            call_started = time.monotonic()
            response = pair.generate(
                role, calls[role], GenerationConfig(max_new_tokens=512 if role == "agent" else 128)
            )
            memory = observer.sample("after_call")
            validate_memory(memory)
            row = {
                "role": role,
                "response_sha256": text_hash(response.text),
                "call_seconds": time.monotonic() - call_started,
                "memory": memory,
                "pair": pair.snapshot(),
            }
            write_receipt(output / f"{role}_call.json", row)
            rows.append(row)
        status = "EXECUTION_COMPLETE"
    except Exception as exc:  # Preserve class/partials only; no model text or semantic retry.
        status = "ERROR"
        write_receipt(output / "error.json", {"error_class": type(exc).__name__})
    finally:
        try:
            pair.close()
        except BaseException as exc:
            cleanup_error = True
            write_receipt(output / "cleanup_error.json", {"error_class": type(exc).__name__})
        snapshot = pair.snapshot()
        write_receipt(output / "closed.json", snapshot)
        reaped = not any(w["handle_pending"] for w in snapshot["workers"].values())
        if reaped and baseline and not cleanup_error:
            try:
                for index in range(6):
                    if index:
                        time.sleep(observer.interval)
                    sample = observer.sample("recovery")
                    validate_memory(sample)
                    write_receipt(
                        output / f"recovery_{index}.json",
                        {
                            "elapsed_seconds": time.monotonic() - started,
                            "memory": sample,
                        },
                    )
                    samples.append(sample)
            except Exception as exc:
                status = "OBSERVER_ERROR"
                write_receipt(output / "observer_error.json", {"error_class": type(exc).__name__})
        recovered = len(samples) == 6 and all(
            row[i]["total_bytes"] == baseline[i]["total_bytes"]
            and abs(row[i]["free_bytes"] - baseline[i]["free_bytes"]) <= TOLERANCE
            for row in samples[-3:]
            for i in (0, 1)
        )
        summary = {
            "protocol": "model_pair_residency_probe_v1",
            "status": status,
            "valid": status == "EXECUTION_COMPLETE" and reaped and recovered and not cleanup_error,
            "phase5_accepted": False,
            "calls_completed": len(rows),
            "reaped": reaped,
            "recovery_valid": recovered,
            "cleanup_error": cleanup_error,
            "scope": "Pair residency/two small-context calls/recovery only; "
            "not quality or max-context stress",
        }
        write_receipt(output / "summary.json", summary)
    return summary
