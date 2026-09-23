#!/usr/bin/env python3
"""Read-only lifecycle audit of the immutable Dev32 v2 pair-worker receipts."""

from __future__ import annotations

import argparse
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.guard_probe_audit_v2 import digest, require

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/evaluation/phase5_clause_guard_exit_diagnostic_protocol_v1.md"


def lifecycle_row(key: str, task: dict[str, Any], directory: Path) -> dict[str, Any]:
    pair = read_record(directory / "execution/pair_runtime.json")
    exit_report = read_record(directory / "execution/exit_milestones.json")
    equal(pair["task_id"], exit_report["task_id"], "pair/exit task")
    equal(pair["snapshot"]["state"], "CLOSED", "closed pair")
    equal(pair["terminal"], task["terminal"], "task terminal")
    equal(pair["cleanup_error_class"], None, "cleanup error")
    equal(pair["error_class"], None, "runtime error")
    require(pair["startup_completed"] is True, "pair startup")
    rows: dict[str, Any] = {}
    for role in ("agent", "guard"):
        worker = pair["snapshot"]["workers"][role]
        observed = exit_report["workers"][role]
        equal(len(worker["lifecycle"]), 1, "one shutdown per role")
        life = worker["lifecycle"][0]
        events = observed["milestones"]["events"]
        equal(observed["status"], "reaped", "observed reaped")
        require(worker["closed"] is True and worker["handle_pending"] is False, "closed worker")
        require(life["reaped"] is True and life["graceful_requested"] is True, "reaped worker")
        equal(life["pid"], events["target_enter"]["pid"], "worker PID")
        equal(life["stop_received"], events["target_return"] is not None, "stop/return join")
        equal(life["serve_returned"], events["target_return"] is not None, "serve return join")
        for stage in ("target", "finalizers", "threads"):
            require(events[f"{stage}_return"] is not None, f"{stage} return")
            equal(events[f"{stage}_error"], None, f"{stage} error")
            equal(events[f"{stage}_return"]["non_daemon_threads"], 0, "no non-daemon threads")
        require(
            events["target_return"]["at"]
            <= events["finalizers_return"]["at"]
            <= events["threads_return"]["at"],
            "milestone ordering",
        )
        require(life["method"] in {"GRACEFUL", "TERMINATE"}, "known lifecycle method")
        equal(life["exitcode"], 0 if life["method"] == "GRACEFUL" else -15, "exit code/method")
        equal(
            life["graceful_shutdown_seconds"],
            pair["pair_config"]["graceful_shutdown_seconds"],
            "configured graceful deadline",
        )
        rows[role] = {
            "method": life["method"],
            "exitcode": life["exitcode"],
            "elapsed_seconds": life["elapsed_seconds"],
            "graceful_shutdown_seconds": life["graceful_shutdown_seconds"],
            "stop_received": life["stop_received"],
            "serve_returned": life["serve_returned"],
            "finalizers_returned": True,
            "threads_returned": True,
            "non_daemon_threads_at_return": events["threads_return"]["non_daemon_threads"],
            "request_attempts": len(worker["attempts"]),
            "host_role_attempts": len(pair["host_role_attempts"][role]),
        }
    equal(
        rows["guard"]["host_role_attempts"], len(task["roles"]["guard"]["calls"]), "guard call join"
    )
    return {"key": key, "terminal": task["terminal"], "roles": rows}


def diagnose(audit: dict[str, Any], raw: Path) -> dict[str, Any]:
    require(
        audit["protocol"] == "clause_dev32_gpu_release_audit_v2"
        and audit["valid"] is True
        and audit["source_authenticated"] is True,
        "authenticated Dev32 v2 audit",
    )
    equal([audit["native"]["expected"], audit["native"]["completed"]], [32, 32], "Dev32 coverage")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for shard in audit["native"]["shards"]:
        for task in shard["tasks"]:
            key = task["key"]
            require(key not in seen, "unique task")
            seen.add(key)
            path = raw / "dev32" / f"shard{shard['shard']}" / "tasks" / key
            rows.append(lifecycle_row(key, task, path))
    equal(len(seen), 32, "exact Dev32 task count")
    equal(len(audit["native"]["shards"]), 8, "eight fixed shards")
    methods = {
        role: dict(Counter(row["roles"][role]["method"] for row in rows))
        for role in ("agent", "guard")
    }
    anomalies = [
        row
        for row in rows
        if any(row["roles"][role]["method"] != "GRACEFUL" for role in ("agent", "guard"))
    ]
    guard_elapsed = [row["roles"]["guard"]["elapsed_seconds"] for row in rows]
    return {
        "protocol": "phase5_clause_guard_exit_diagnostic_v1",
        "source_commit": audit["source_commit"],
        "task_count": len(rows),
        "raw_files_verified": len(audit["raw_sha256"]),
        "methods": methods,
        "all_workers_reaped": True,
        "guard_shutdown_elapsed_median_seconds": statistics.median(guard_elapsed),
        "guard_shutdown_elapsed_max_seconds": max(guard_elapsed),
        "anomalies": anomalies,
        "test_payloads_read": 0,
        "oracle_records_read": 0,
        "new_inference_runs": 0,
        "root_cause_proven": False,
        "phase5_lifecycle_accepted": False,
        "phase5_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    for path in (args.audit, args.raw, args.output):
        no_links(path)
    output = args.output.resolve()
    require(not output.exists() and output.is_relative_to(ROOT / "results"), "fresh output")
    before = inventory(args.raw)
    audit = read_record(args.audit)
    equal(before, audit["raw_sha256"], "raw inventory unchanged")
    audit_hash = digest(args.audit)
    report = diagnose(audit, args.raw)
    equal(inventory(args.raw), before, "raw unchanged during diagnostic")
    equal(digest(args.audit), audit_hash, "audit unchanged during diagnostic")
    report.update(
        audit_sha256=audit_hash,
        protocol_sha256=digest(PROTOCOL),
        script_sha256=digest(Path(__file__)),
    )
    output.mkdir()
    write_receipt(output / "diagnostic.json", report)
    print("PHASE5_GUARD_EXIT_DIAGNOSTIC_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
