"""Read-only verification of complete GPU cancellation evidence; no worker launch."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import MODEL, no_links
from react_agent.llm.agent_runtime_input_v1 import INVENTORY_SHA256
from react_agent.llm.base import GenerationConfig
from react_agent.llm.coexistence_placement_v1 import PlacementPlan
from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AGENT_CONTENT, AGENT_REVISION
from react_agent.llm.model_pair_probe_v1 import MIN_RESIDENT, TOLERANCE, validate_memory
from react_agent.llm.model_pair_v1 import READY_COMMAND, ModelIdentity, PairConfig, Role
from react_agent.llm.pair_cancellation_v1 import BUSY, PLAN, busy_role, matching_baseline
from react_agent.validation.guard_probe_audit_v2 import digest, positive, read_json, require


def audit_worker(
    worker: dict[str, Any], role: Role, trial: str, config: PairConfig
) -> dict[str, Any]:
    busy = role == busy_role(trial)
    attempts, events = worker["attempts"], worker["lifecycle"]
    require(worker["closed"] is True and worker["handle_pending"] is False, "pending worker")
    require(len(attempts) == (2 if busy else 1) and len(events) == 1, "attempt/lifecycle coverage")
    event = events[0]
    pid = event["pid"]
    require(
        type(pid) is int
        and pid > 0
        and event["reaped"] is True
        and event["sequence"] == 1
        and positive(event["elapsed_seconds"]),
        "reap event",
    )
    require(
        (event["method"], event["exitcode"]) in {("GRACEFUL", 0), ("TERMINATE", -15), ("KILL", -9)},
        "cleanup method",
    )
    if busy:
        expected = ("KILL", -9) if trial == "guard_ignore_term" else ("TERMINATE", -15)
        require((event["method"], event["exitcode"]) == expected, "busy termination method")
    for i, attempt in enumerate(attempts):
        execution = config.execution(role, cold=i == 0)
        request = [{"role": "user", "content": READY_COMMAND if i == 0 else BUSY}]
        require(
            attempt["pid"] == pid
            and attempt["sequence"] == i + 1
            and attempt["cold_start"] is (i == 0)
            and attempt["status"] == ("OK" if i == 0 else "TIMEOUT")
            and attempt["reaped"] is (i != 0)
            and attempt["worker_retained"] is (i == 0),
            "attempt lifecycle",
        )
        require(
            attempt["execution_config_sha256"] == execution.identity
            and attempt["request_sha256"] == text_hash(canonical_json(request))
            and attempt["generation_sha256"]
            == text_hash(canonical_json(GenerationConfig().model_dump())),
            "attempt identity",
        )
        require(positive(attempt["elapsed_seconds"]), "attempt duration")
        if i:
            require(attempt["elapsed_seconds"] >= execution.timeout_seconds, "early timeout")
        else:
            require(
                positive(attempt["load_seconds"])
                and attempt["load_seconds"]
                <= attempt["elapsed_seconds"]
                < execution.timeout_seconds,
                "cold duration",
            )
    return {
        "pid": pid,
        "ready_seconds": attempts[0]["elapsed_seconds"],
        "busy_seconds": attempts[-1]["elapsed_seconds"] if busy else None,
        "cleanup": event,
        "graceful": event["method"] == "GRACEFUL",
    }


def audit_load(path: Path, role: Role, config: PairConfig, pin: GuardSnapshot) -> dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    require(len(rows) == 1 and rows[0]["event"] == "load", "load-only HF evidence")
    row: dict[str, Any] = rows[0]
    identity = config.agent if role == "agent" else config.guard
    for key, value in {
        "model_id": identity.model_id,
        "model_revision": identity.model_revision,
        "dtype": "float16",
        "quantization": None,
        "attention": "sdpa",
        "torch_version": "2.10.0+cu128",
        "transformers_version": "5.5.0",
        "cuda_version": "12.8",
    }.items():
        require(row[key] == value, "HF identity: " + key)
    require(positive(row["load_seconds_including_hashes"]), "HF load duration")
    if role == "agent":
        plan = PlacementPlan()
        require(
            row["adapter_protocol"] == "agent_hf_dual_gpu_v2_tf550"
            and row["placement_sha256"] == plan.sha256
            and row["device_map"] == plan.device_map()
            and row["agent_caps"] == list(plan.agent_caps),
            "agent placement",
        )
        admission = row["runtime_admission"]
        for key, expected in {
            "content_sha256": AGENT_CONTENT,
            "inventory_sha256": INVENTORY_SHA256,
            "full_inventory_match": False,
            "documentation_mismatches": ["README.md"],
            "runtime_files_match": True,
            "runtime_files": 11,
            "parameter_tensors": 339,
            "serialized_parameter_bytes": 15231233024,
        }.items():
            require(admission[key] == expected, "agent runtime admission: " + key)
        require(
            len(row["memory"]) == 2 and [m["device"] for m in row["memory"]] == [0, 1],
            "agent devices",
        )
        for memory in row["memory"]:
            for key in (
                "allocated_bytes",
                "reserved_bytes",
                "peak_allocated_bytes",
                "peak_reserved_bytes",
            ):
                require(
                    type(memory[key]) is int
                    and 0 < memory[key] <= plan.agent_caps[memory["device"]],
                    "agent allocator budget",
                )
    else:
        adapter = GuardHFConfig()
        require(
            row["snapshot_sha256"] == pin.sha256
            and row["adapter_config_sha256"] == adapter.sha256
            and row["device"] == 1
            and row["device_map"] == {"": 1}
            and row["allocator_limit_bytes"] == adapter.allocator_limit_bytes,
            "guard placement",
        )
        for key in (
            "process_allocated_bytes",
            "process_reserved_bytes",
            "process_peak_allocated_bytes",
            "process_peak_reserved_bytes",
        ):
            require(
                type(row[key]) is int and 0 < row[key] <= adapter.allocator_limit_bytes,
                "guard allocator budget",
            )
    return row


def audit_probe(probe: Path, pin: GuardSnapshot, commit: str) -> dict[str, Any]:
    no_links(probe)
    require(not any(p.is_symlink() for p in probe.rglob("*")), "linked probe artifact")
    hashes = {p.relative_to(probe).as_posix(): digest(p) for p in probe.rglob("*") if p.is_file()}
    config = PairConfig(
        ModelIdentity(MODEL, AGENT_REVISION), ModelIdentity(pin.model_id, pin.model_revision)
    )
    manifest = read_json(probe / "manifest.json")
    baseline = manifest["initial_memory"]
    validate_memory(baseline)
    require(
        manifest
        == {
            "protocol": "pair_cancellation_v1",
            "plan": list(PLAN),
            "identity": {
                "backend": "hf",
                "source_commit": commit,
                "snapshot_sha256": pin.sha256,
                "agent_adapter": "agent_hf_dual_gpu_v2_tf550",
                "environment": {"torch": "2.10.0+cu128", "cuda": "12.8", "transformers": "5.5.0"},
            },
            "actual_cuda": True,
            "initial_memory": baseline,
            "sample_interval_seconds": 1.0,
            "recovery_samples": 6,
            "tolerance_bytes": TOLERANCE,
            "min_resident_bytes": list(MIN_RESIDENT),
            "model_generation_calls": 0,
            "automatic_retry": False,
        },
        "suite manifest",
    )
    measurements, rows = [], []
    all_pids: set[int] = set()
    expected_files = {"manifest.json", "summary.json"}
    for trial in PLAN:
        root = probe / trial
        row = read_json(root / "trial.json")
        require(
            row
            == {
                "trial": trial,
                "valid": True,
                "status": "EXECUTION_COMPLETE",
                "timeout_observed": True,
                "reaped": True,
                "cleanup_error": False,
                "recovery_valid": True,
                "forced_method_valid": True,
            },
            "trial result",
        )
        require(
            read_json(root / "pair_config.json")
            == {"sha256": config.sha256, "values": asdict(config)},
            "pair config",
        )
        before = read_json(root / "baseline.json")["memory"]
        require(matching_baseline(baseline, before), "suite baseline drift")
        ready = read_json(root / "ready.json")
        resident = ready["memory"]
        validate_memory(resident)
        require(
            all(
                resident[i]["total_bytes"] == before[i]["total_bytes"]
                and before[i]["free_bytes"] - resident[i]["free_bytes"] >= MIN_RESIDENT[i]
                for i in (0, 1)
            ),
            "combined residency",
        )
        require(
            ready["pair"]["state"] == "READY" and ready["pair"]["config_sha256"] == config.sha256,
            "ready pair",
        )
        closed = read_json(root / "closed.json")
        require(
            closed["state"] == "FAILED" and closed["config_sha256"] == config.sha256,
            "timeout must retire pair",
        )
        workers = {}
        loads = {}
        for role in ("agent", "guard"):
            workers[role] = audit_worker(closed["workers"][role], role, trial, config)
            pid = workers[role]["pid"]
            require(pid not in all_pids, "worker PID reused across fresh pairs")
            all_pids.add(pid)
            require(
                ready["pair"]["workers"][role]["attempts"]
                == closed["workers"][role]["attempts"][:1],
                "ready attempt continuity",
            )
            loads[role] = audit_load(root / f"{role}_hf_metrics.jsonl", role, config, pin)
        role = busy_role(trial)
        require(
            read_json(root / "busy_entered.json")
            == {
                "trial": trial,
                "role": role,
                "pid": workers[role]["pid"],
                "ignore_sigterm": trial == "guard_ignore_term",
                "actual_cuda_operation": True,
                "devices": [0, 1] if role == "agent" else [1],
                "model_generation_calls": 0,
            },
            "busy CUDA marker",
        )
        residuals, timestamps = [], []
        for i in range(6):
            sample = read_json(root / f"recovery_{i}.json")
            memory = sample["memory"]
            validate_memory(memory)
            require(
                all(memory[j]["total_bytes"] == before[j]["total_bytes"] for j in (0, 1)),
                "recovery device total",
            )
            require(positive(sample["elapsed_seconds"]), "recovery time")
            timestamps.append(sample["elapsed_seconds"])
            residuals.append([before[j]["free_bytes"] - memory[j]["free_bytes"] for j in (0, 1)])
        require(
            all(b > a for a, b in zip(timestamps, timestamps[1:], strict=False)), "sample order"
        )
        require(
            all(abs(v) <= TOLERANCE for values in residuals[-3:] for v in values), "VRAM recovery"
        )
        rows.append(row)
        measurements.append(
            {
                "trial": trial,
                "workers": workers,
                "hf_loads": loads,
                "resident_bytes": [
                    before[j]["free_bytes"] - resident[j]["free_bytes"] for j in (0, 1)
                ],
                "signed_residual_bytes": residuals,
                "sample_elapsed_seconds": timestamps,
            }
        )
        names = {
            "trial.json",
            "pair_config.json",
            "baseline.json",
            "ready.json",
            "closed.json",
            "busy_entered.json",
            "agent_hf_metrics.jsonl",
            "guard_hf_metrics.jsonl",
        }
        names.update(f"recovery_{i}.json" for i in range(6))
        expected_files.update(f"{trial}/{name}" for name in names)
    summary = read_json(probe / "summary.json")
    require(
        summary
        == {
            "protocol": "pair_cancellation_v1",
            "rows": rows,
            "valid": True,
            "phase5_accepted": False,
            "model_generation_calls": 0,
            "error_class": None,
            "scope": "Cancellation with sibling resident; not model generation or context stress",
        },
        "suite summary",
    )
    require(set(hashes) == expected_files, "exact probe inventory")
    require(
        hashes
        == {p.relative_to(probe).as_posix(): digest(p) for p in probe.rglob("*") if p.is_file()},
        "raw changed during audit",
    )
    return {
        "protocol": "pair_cancellation_gpu_audit_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_commit": commit,
        "measurements": measurements,
        "model_generation_calls": 0,
        "workers_reaped": len(all_pids),
        "resource_recovery_pass": True,
        "limitations": "CUDA busy loops with weights resident, not native generation cancellation, "
        "maximum context, quality, continuous peak memory, owner SIGKILL or driver-crash safety",
    }
