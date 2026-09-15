"""Re-audit immutable observer outputs and derive descriptive, non-acceptance metrics."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from audit_phase5_observer_gpu_v2 import ROOT, audit

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory


def summarize(verified: dict[str, Any], raw: Path) -> dict[str, Any]:
    """Input must be the freshly regenerated release audit, never a trust-on-flag receipt."""
    if verified.get("valid") is not True or verified.get("source_authenticated") is not True:
        raise ValueError("authenticated release audit required")
    if inventory(raw) != verified["raw_sha256"]:
        raise ValueError("raw hash mismatch")
    tasks = verified["native"]["tasks"]
    keys = [task["key"] for task in tasks]
    if len(keys) != len(set(keys)) or len(keys) != verified["native"]["expected"]:
        raise ValueError("unique complete schedule required")
    rows = []
    methods: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    syntax: Counter[str] = Counter()
    framing: Counter[str] = Counter()
    classifications: Counter[str] = Counter()
    stage_categories: Counter[str] = Counter()
    workers = []
    for task in tasks:
        key = task["key"]
        if Path(key).name != key or key in (".", ".."):
            raise ValueError("task basename required")
        base = raw / "observer/tasks" / key / "execution"
        runtime = json.loads((base / "pair_runtime.json").read_text())
        trace = base / "runtime/trace_guard.jsonl"
        traces = (
            [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
        )
        errors = Counter(t["outcome"]["error_code"] for t in traces if t["outcome"]["error_code"])
        joined = task["guard_diagnostics"]["joined"]
        valid = 0
        for response in joined:
            diagnostic = response["diagnostic"]
            category = diagnostic["baseline"]["category"]
            valid += category == "valid"
            categories[category] += 1
            framing[diagnostic["framing"]] += 1
            syntax[diagnostic["syntax_kind"]] += 1
            classifications[response["classification_status"]] += 1
            stage_categories[f"{response['stage']}:{category}"] += 1
        task_methods: Counter[str] = Counter()
        for role, worker in runtime["snapshot"]["workers"].items():
            for event in worker["lifecycle"]:
                methods[event["method"]] += 1
                task_methods[event["method"]] += 1
                workers.append(dict(task=key, role=role, **event))
        rows.append(
            dict(
                task=key,
                terminal=task["terminal"],
                executed_tool_calls=task["executed_tool_calls"],
                guard_responses=len(joined),
                guard_valid=valid,
                guard_invalid=len(joined) - valid,
                guard_invalid_output_events=errors["INVALID_OUTPUT"],
                guard_backend_failure_events=errors["BACKEND_FAILURE"],
                recovered=task["recovered"],
                graceful_workers=task_methods["GRACEFUL"],
                forced_workers=sum(n for method, n in task_methods.items() if method != "GRACEFUL"),
                startup_seconds=task["startup_seconds"],
                total_seconds=task["total_seconds"],
            )
        )
    role_totals = {}
    for role in ("agent", "guard"):
        calls = [call for task in tasks for call in task["roles"][role]["calls"]]
        seconds = sum(c["generate_seconds"] for c in calls)
        output_tokens = sum(c["output_tokens"] for c in calls)
        role_totals[role] = dict(
            joined_calls=len(calls),
            input_tokens=sum(c["input_tokens"] for c in calls),
            output_tokens=output_tokens,
            generate_seconds=seconds,
            call_seconds=sum(c["call_seconds"] for c in calls),
            pooled_output_tokens_per_generate_second=output_tokens / seconds if seconds else None,
            failed_or_partial_tasks=sum(t["roles"][role]["failed_or_partial"] for t in tasks),
        )
    if inventory(raw) != verified["raw_sha256"]:
        raise ValueError("raw changed during summary")
    return dict(
        protocol="observer_native_descriptive_report_v2",
        source_commit=verified["source_commit"],
        source_authenticated=True,
        notebook_url=verified["notebook_url"],
        kernel_version=verified["kernel_version"],
        tasks=rows,
        workers=workers,
        terminal_counts=dict(Counter(t["terminal"] for t in tasks)),
        guard_categories=dict(categories),
        guard_framing=dict(framing),
        guard_syntax=dict(syntax),
        guard_classifications=dict(classifications),
        guard_stage_categories=dict(stage_categories),
        shutdown_methods=dict(methods),
        all_workers_reaped=all(w["reaped"] for w in workers),
        recovered_tasks=sum(t["recovered"] for t in tasks),
        role_totals=role_totals,
        summed_task_startup_seconds=sum(t["startup_seconds"] for t in tasks),
        summed_task_total_seconds=sum(t["total_seconds"] for t in tasks),
        raw_files_verified=len(verified["raw_sha256"]),
        remote_files_verified=len(verified["remote_sha256"]),
        guard_quality_validated=False,
        semantic_utility_measured=False,
        phase5_accepted=False,
        limitations=[
            "Four diagnostic tasks are not independent quality or acceptance samples.",
            "Framing hints are hash-bound worker telemetry, not a reconstruction of raw text.",
            "Only joined native calls enter timing denominators; startup is reported separately.",
            "Task total excludes runner recovery sampling and notebook bootstrap/download.",
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "remote", "preflight", "submission", "observation", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    protected = [
        args.raw,
        args.remote,
        args.preflight,
        args.submission,
        args.observation,
        ROOT / "data",
    ]
    if args.output.exists() or any(
        args.output.resolve().is_relative_to(p.resolve())
        or p.resolve().is_relative_to(args.output.resolve())
        for p in protected
    ):
        raise ValueError("fresh report directory outside inputs required")
    verified = audit(args.raw, args.remote, args.preflight, args.submission, args.observation)
    result = summarize(verified, args.raw)
    args.output.mkdir(parents=True)
    write_receipt(args.output / "release_audit.json", verified)
    write_receipt(args.output / "summary.json", result)
    with (args.output / "tasks.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result["tasks"][0]))
        writer.writeheader()
        writer.writerows(result["tasks"])
    print("OBSERVER_NATIVE_REPORT_COMPLETE")


if __name__ == "__main__":
    main()
