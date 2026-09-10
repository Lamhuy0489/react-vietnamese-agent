"""Versioned paired maximum-context protocol; no changes to frozen small-context probes."""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.context_stress_v1 import ACK, REQUEST
from react_agent.llm.model_pair_probe_v1 import (
    MIN_RESIDENT,
    TOLERANCE,
    PairObserver,
    validate_memory,
)
from react_agent.llm.model_pair_v1 import ModelPair


def validate_completion(value: dict[str, Any], role: str, snapshot: dict[str, Any]) -> None:
    expected = 512 if role == "agent" else 128
    ready = next(e for e in snapshot["events"] if e["role"] == role and e["stage"] == "ready")
    summary = value["summary"]
    if (
        value.get("protocol") != "context_stress_v1"
        or value.get("stage") != "completed"
        or value.get("role") != role
        or value.get("pid") != ready["pid"]
        or value.get("model_generation_calls") != 1
        or value.get("separate_final_forwards") != 1
        or summary.get("input_tokens") != 4096
        or summary.get("new_tokens") != expected
        or summary.get("cache_length_after_generation") != 4096 + expected - 1
        or summary.get("cache_length_after_final_forward") != 4096 + expected
        or summary.get("full_boundary_cache_observed") is not True
        or summary.get("generated_text_retained") is not False
    ):
        raise ValueError("PID-bound full-context completion required")


@dataclass(frozen=True)
class SyntheticStressFactory:
    role: str
    output: Path

    def __call__(self) -> LLMBackend:
        write_receipt(
            self.output / f"{self.role}_synthetic_load.json",
            {"pid": os.getpid(), "role": self.role, "actual_model_load": False},
        )
        return SyntheticStressBackend(self.role)


class SyntheticStressBackend:
    def __init__(self, role: str) -> None:
        self.model_id, self.model_revision = "synthetic-" + role, "v1"

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if messages != REQUEST:
            raise ValueError("fixed synthetic request required")
        return ModelResponse(text=ACK, model_id=self.model_id, model_revision=self.model_revision)


def run_context_probe(
    output: Path, pair: ModelPair, observer: PairObserver, identity: dict[str, Any]
) -> dict[str, Any]:
    """One fresh pair and two single-use stress calls, finally-cleanup; no retry."""
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
    if identity.get("backend") not in {"stub", "hf"}:
        raise ValueError("explicit synthetic/native identity required")
    calls = {"agent": [dict(m) for m in REQUEST], "guard": [dict(m) for m in REQUEST]}
    write_receipt(
        output / "manifest.json",
        {
            "protocol": "context_stress_pair_probe_v1",
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
            if response.text != ACK:
                raise ValueError("diagnostic acknowledgement required")
            if identity["backend"] == "hf":
                completion = json.loads((output / f"{role}_stress/completed.json").read_text())
                validate_completion(completion, role, pair.snapshot())
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
            "protocol": "context_stress_pair_probe_v1",
            "status": status,
            "valid": status == "EXECUTION_COMPLETE" and reaped and recovered and not cleanup_error,
            "phase5_accepted": False,
            "calls_completed": len(rows),
            "reaped": reaped,
            "recovery_valid": recovered,
            "cleanup_error": cleanup_error,
            # A timed-out/failed call may already have entered native generation.
            # Do not misreport completed acknowledgements as total attempted calls.
            "actual_model_generation_calls": (
                (2 if status == "EXECUTION_COMPLETE" else None)
                if identity["backend"] == "hf"
                else 0
            ),
            "native_stress_verified": identity["backend"] == "hf"
            and len(rows) == 2
            and status == "EXECUTION_COMPLETE"
            and recovered
            and reaped
            and not cleanup_error,
            "scope": "Stress transport/completion/recovery; stub is not native GPU evidence; "
            "native records still require independent artifact audit",
        }
        write_receipt(output / "summary.json", summary)
    return summary
