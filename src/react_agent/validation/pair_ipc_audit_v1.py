"""Read-only IPC diagnostic audit; prior cancellation gates remain unchanged."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import MODEL, no_links
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.ipc_trace_v1 import read_trace
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION
from react_agent.llm.model_pair_probe_v1 import MIN_RESIDENT, TOLERANCE, validate_memory
from react_agent.llm.model_pair_v1 import ModelIdentity, PairConfig
from react_agent.llm.pair_cancellation_v1 import PLAN, busy_role, matching_baseline
from react_agent.validation.guard_probe_audit_v2 import digest, positive, read_json, require
from react_agent.validation.pair_cancellation_audit_v1 import audit_load, audit_worker


def audit_probe(
    probe: Path, pin: GuardSnapshot, commit: str, python_version: str
) -> dict[str, Any]:
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
                "instrumentation": "ipc_tracker_trace_v1",
                "python_version": python_version,
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
        "protocol": "pair_ipc_gpu_probe_audit_v1",
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


def audit_traces(root: Path, probe: dict[str, Any], python_version: str) -> dict[str, Any]:
    no_links(root)
    expected = {"owner.jsonl"} | {
        f"{trial}_{role}.jsonl" for trial in PLAN for role in ("agent", "guard")
    }
    require({p.name for p in root.iterdir()} == expected, "exact tracker inventory")
    require(re.fullmatch(r"3\.12\.\d+", python_version) is not None, "pinned image Python series")
    observations = {}
    tracker_hashes = set()
    all_names: set[str] = set()
    unmatched = []
    pids: set[int] = set()
    owner = read_trace(root / "owner.jsonl")
    done = []
    transport_registrations = 0
    for name in sorted(expected):
        path = root / name
        records = [json.loads(line) for line in path.read_text().splitlines()]
        row = read_trace(path)
        require(records[0].get("python_version") == python_version, "trace Python identity")
        require(records[0].get("implementation") == "CPython", "trace interpreter")
        h = records[0].get("tracker_source_sha256")
        require(
            isinstance(h, str) and re.fullmatch(r"[0-9a-f]{64}", h) is not None,
            "tracker source hash",
        )
        tracker_hashes.add(h)
        require(row["pid"] not in pids, "distinct traced process PIDs")
        pids.add(row["pid"])
        if name == "owner.jsonl":
            require(row["role"] == "owner", "owner trace role")
            done = [r for r in records if r["action"] == "PROBE_DONE"]
            require(len(done) == 1 and done[0].get("valid") is True, "owner completion")
            require(
                type(done[0].get("gc_collected")) is int and done[0]["gc_collected"] >= 0,
                "owner GC checkpoint",
            )
            transport_registrations = sum(
                r["action"] == "REGISTER"
                and any(
                    f["module"] == "react_agent.security_v1.warm_guard"
                    and f["function"] == "__init__"
                    for f in r.get("stack", [])
                )
                for r in records
            )
            require(transport_registrations == 90, "three pairs' parent transport registrations")
        else:
            trial, role = name.removesuffix(".jsonl").rsplit("_", 1)
            measurement = next(r for r in probe["measurements"] if r["trial"] == trial)
            require(
                row["role"] == role and row["pid"] == measurement["workers"][role]["pid"],
                "factory/lifecycle PID binding",
            )
            stages = [
                r["action"]
                for r in records
                if r["action"] in ("FACTORY_ENTER", "FACTORY_READY", "FACTORY_ERROR")
            ]
            require(stages == ["FACTORY_ENTER", "FACTORY_READY"], "complete factory boundaries")
            ready = next(r for r in records if r["action"] == "FACTORY_READY")
            modules = ready.get("modules", {})
            for n, version in (("torch", "2.10.0+cu128"), ("transformers", "5.5.0")):
                require(modules.get(n, {}).get("version") == version, "loaded dependency identity")
            require("multiprocessing.synchronize" in modules, "synchronization source identity")
            for item in modules.values():
                require(
                    re.fullmatch(r"[0-9a-f]{64}", item.get("source_sha256", "")) is not None,
                    "dependency source digest",
                )
        for record in records:
            if record["action"] == "REGISTER":
                require(
                    record["name_sha256"] not in all_names,
                    "cross-process resource attribution ambiguous",
                )
                all_names.add(record["name_sha256"])
        unmatched.extend(row["unmatched_registrations"])
        observations[name] = row
    require(len(tracker_hashes) == 1, "owner/worker tracker source changed")
    for row in unmatched:
        require(row["resource_type"] == "semaphore", "unexpected unmatched resource type")
    transport_unmatched = [
        r
        for r in owner["unmatched_registrations"]
        if any(
            f["module"] == "react_agent.security_v1.warm_guard" and f["function"] == "__init__"
            for f in r["stack"]
        )
    ]
    return {
        "protocol": "pair_ipc_trace_audit_v1",
        "observations": observations,
        "transport_registrations": transport_registrations,
        "transport_unmatched": transport_unmatched,
        "unmatched_registrations": unmatched,
        "tracker_source_sha256": next(iter(tracker_hashes)),
        "ipc_cleanup_verified": False,
        "limitations": "Observed entry points only; no C-level/cached-alias coverage "
        "or tracker/OS unlink certification",
    }
