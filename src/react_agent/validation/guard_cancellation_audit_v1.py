"""Read-only audit of complete cancellation trials; never launches a worker."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.guard_cancellation_v1 import MIN_RESIDENCY, PLAN, SAMPLES, TOLERANCE
from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_probe_v1 import GENERATION
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.validation.guard_probe_audit_v2 import positive, read_json, require


def memory(value: Any) -> None:
    require(
        isinstance(value, dict)
        and set(value) == {"free_bytes", "total_bytes"}
        and all(type(v) is int for v in value.values())
        and 0 <= value["free_bytes"] <= value["total_bytes"]
        and value["total_bytes"] > 0,
        "invalid memory sample",
    )


def audit_probe(probe: Path, pin: GuardSnapshot, commit: str) -> dict[str, Any]:
    """Reject partial/failed trials; they need failure analysis, never automatic rerun.

    Resource thresholds are the predeclared engineering contract, not model quality.
    Actual sample timestamps are unavailable; report declared cadence only.
    """
    manifest = read_json(probe / "manifest.json")
    initial = manifest["initial_memory"]
    memory(initial)
    config = WarmGuardConfig(pin.model_id, pin.model_revision)
    adapter = GuardHFConfig()
    require(
        manifest
        == {
            "protocol": "guard_cancellation_v1",
            "plan": list(PLAN),
            "identity": {"backend": "hf", "source_commit": commit, "snapshot_sha256": pin.sha256},
            "execution_config_sha256": config.identity,
            "timeout_seconds": 120.0,
            "terminate_grace_seconds": 0.5,
            "kill_grace_seconds": 1.0,
            "generation": GENERATION.model_dump(),
            "model_generation_calls": 0,
            "recovery_samples": SAMPLES,
            "sample_interval_seconds": 1.0,
            "memory_tolerance_bytes": TOLERANCE,
            "min_residency_bytes": MIN_RESIDENCY,
            "initial_memory": initial,
            "automatic_retry": False,
        },
        "manifest identity",
    )
    rows, measurements = [], []
    expected_files = {"manifest.json", "summary.json"}
    for name in PLAN:
        root = probe / name
        row = read_json(root / "trial.json")
        require(
            row["trial"] == name
            and row["status"] == "EXECUTION_COMPLETE"
            and row["closed"] is True
            and row["reaped"] is True,
            "incomplete trial",
        )
        before, resident, after = row["before"], row["resident"], row["after_samples"]
        for sample in [before, resident, *after]:
            memory(sample)
            require(sample["total_bytes"] == initial["total_bytes"], "memory total changed")
        require(abs(before["free_bytes"] - initial["free_bytes"]) <= TOLERANCE, "baseline drift")
        used = before["free_bytes"] - resident["free_bytes"]
        require(used >= MIN_RESIDENCY, "no resident model")
        residuals = [before["free_bytes"] - sample["free_bytes"] for sample in after]
        recovery = len(after) == SAMPLES and all(abs(r) <= TOLERANCE for r in residuals[-3:])
        require(
            recovery and row["recovery_valid"] is True and row["valid"] is True,
            "memory recovery failed",
        )
        require(
            read_json(root / "before.json") == before
            and read_json(root / "resident_memory.json") == resident,
            "memory sidecar",
        )
        attempts, events = row["attempts"], row["lifecycle"]
        require(
            len(attempts) == (1 if name == PLAN[0] else 2) and len(events) == 1, "attempt coverage"
        )
        event = events[0]
        pid = event["pid"]
        require(
            type(pid) is int
            and pid > 0
            and event["reaped"] is True
            and event["sequence"] == 1
            and positive(event["elapsed_seconds"])
            and (event["method"], event["exitcode"])
            in {("GRACEFUL", 0), ("TERMINATE", -15), ("KILL", -9)},
            "cleanup lifecycle",
        )
        require(row["graceful"] is (event["method"] == "GRACEFUL"), "graceful label")
        if name == PLAN[2]:
            require(event["method"] == "KILL" and event["exitcode"] == -9, "kill escalation")
        for i, attempt in enumerate(attempts):
            command = "resident_ack" if i == 0 else "busy"
            require(
                attempt["pid"] == pid
                and attempt["sequence"] == i + 1
                and attempt["cold_start"] is (i == 0)
                and attempt["status"] == ("OK" if i == 0 else "TIMEOUT")
                and attempt["worker_retained"] is (i == 0)
                and attempt["reaped"] is (i != 0),
                "request lifecycle",
            )
            require(
                attempt["execution_config_sha256"] == config.identity
                and attempt["generation_sha256"]
                == text_hash(canonical_json(GENERATION.model_dump()))
                and attempt["request_sha256"]
                == text_hash(canonical_json([{"role": "user", "content": command}])),
                "request identity",
            )
            require(positive(attempt["elapsed_seconds"]), "request timing")
            if i:
                require(
                    attempt["elapsed_seconds"] >= 120 and row["timeout_observed"] is True,
                    "early timeout",
                )
            else:
                require(
                    positive(attempt["load_seconds"])
                    and attempt["elapsed_seconds"] >= attempt["load_seconds"],
                    "load timing",
                )
        require(
            read_json(root / "resident_ready.json")
            == {
                "pid": pid,
                "model_id": pin.model_id,
                "model_revision": pin.model_revision,
                "actual_cuda_operation": True,
                "model_generation_calls": 0,
            },
            "resident CUDA identity",
        )
        names = {
            "trial.json",
            "before.json",
            "resident_memory.json",
            "resident_ready.json",
            "hf_metrics.jsonl",
        }
        if name != PLAN[0]:
            require(
                read_json(root / "busy_entered.json")
                == {
                    "pid": pid,
                    "ignore_sigterm": name == PLAN[2],
                    "actual_cuda_operation": True,
                    "model_generation_calls": 0,
                },
                "busy CUDA identity",
            )
            names.add("busy_entered.json")
        expected_files.update(f"{name}/{n}" for n in names)
        metrics = [
            json.loads(line) for line in (root / "hf_metrics.jsonl").read_text().splitlines()
        ]
        require(len(metrics) == 1, "load-only metrics required")
        load = metrics[0]
        for key, value in {
            "event": "load",
            "model_id": pin.model_id,
            "model_revision": pin.model_revision,
            "snapshot_sha256": pin.sha256,
            "adapter_config_sha256": adapter.sha256,
            "device": 1,
            "device_map": {"": 1},
            "dtype": "float16",
            "quantization": None,
            "allocator_limit_bytes": adapter.allocator_limit_bytes,
        }.items():
            require(load[key] == value, "HF load identity: " + key)
        require(
            "T4" in load["device_name"] and positive(load["load_seconds_including_hashes"]),
            "HF device/timing",
        )
        require(
            0 < load["process_peak_allocated_bytes"] <= adapter.allocator_limit_bytes,
            "allocator budget",
        )
        rows.append(row)
        measurements.append(
            {
                "trial": name,
                "pid": pid,
                "resident_bytes": used,
                "residual_bytes": residuals,
                "ack_seconds": attempts[0]["elapsed_seconds"],
                "busy_timeout_seconds": attempts[1]["elapsed_seconds"]
                if len(attempts) == 2
                else None,
                "cleanup": event,
                "hf_load": load,
            }
        )
    require(
        not probe.is_symlink() and not any(p.is_symlink() for p in probe.rglob("*")),
        "linked artifact",
    )
    require(
        {p.relative_to(probe).as_posix() for p in probe.rglob("*") if p.is_file()}
        == expected_files,
        "probe inventory",
    )
    summary = read_json(probe / "summary.json")
    for key, value in {
        "protocol": "guard_cancellation_v1",
        "valid": True,
        "phase5_accepted": False,
        "model_generation_calls": 0,
        "rows": rows,
    }.items():
        require(summary[key] == value, "summary mismatch: " + key)
    return {
        "protocol": "guard_cancellation_audit_v1",
        "valid": True,
        "phase5_accepted": False,
        "resource_recovery_pass": True,
        "normal_close_graceful": rows[0]["graceful"],
        "model_generation_calls": 0,
        "measurements": measurements,
        "declared_sample_interval_seconds": 1.0,
        "limitations": "No sample timestamps, quality inference, agent coexistence or Test. "
        "Signed residual = before free minus after free; tolerance is not exact zero leak.",
    }
