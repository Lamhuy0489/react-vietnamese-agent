#!/usr/bin/env python3
"""Generate reproducible CSV/JSON/Markdown from audited measured Dev pilot runs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from react_agent.schemas.trace import TraceEvent
from react_agent.validation.pilot_statistics import cluster_mean_interval, distribution

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def condition(run: Path, evaluation_path: Path, audit_path: Path) -> dict[str, Any]:
    evaluation = json.loads(evaluation_path.read_text())
    audit = json.loads(audit_path.read_text())
    identity = json.loads((run / "identity.json").read_text())
    if not audit["valid"] or audit["evaluation_sha256"] != sha(evaluation_path):
        raise ValueError("valid matching artifact audit required")
    for path in run.rglob("*"):
        if path.is_file() and audit["raw_artifact_sha256"].get(
            path.relative_to(run.parent).as_posix()
        ) != sha(path):
            raise ValueError("raw artifact differs from audit")
    if (
        evaluation["source_identity"] != identity
        or identity.get("measurement_protocol") != "dev21_performance_v1"
    ):
        raise ValueError("measured protocol identity mismatch")
    ids = json.loads((ROOT / "data/clean/v1_1/dev_pilot/task_ids.json").read_text())["task_ids"]
    if identity["task_ids"] != ids or len(ids) != 21 or evaluation["test_tasks_read"] != 0:
        raise ValueError("must use exact 21 Dev tasks")
    public = {
        t["task_id"]: t
        for t in (
            json.loads(line)
            for line in (ROOT / "data/clean/v1_1/splits/dev.jsonl").read_text().splitlines()
        )
    }
    scored = {row["task_id"]: row for row in evaluation["results"]}
    if set(scored) != set(ids) or len(evaluation["results"]) != 21:
        raise ValueError("evaluation coverage mismatch")
    setup = json.loads((run / "model_setup.json").read_text())
    metrics = [
        json.loads(line) for line in (run / "inference_metrics.jsonl").read_text().splitlines()
    ]
    if any(m["task_id"] not in ids for m in metrics):
        raise ValueError("unexpected measurement task")
    measured: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for metric in metrics:
        measured[metric["task_id"]].append(metric)
    rows: list[dict[str, Any]] = []
    for task_id in ids:
        task_root = run / "tasks" / task_id
        receipt = json.loads((task_root / "result.json").read_text())
        trace_path = task_root / "trace.jsonl"
        if receipt["trace_sha256"] != sha(trace_path):
            raise ValueError("changed trace since checkpoint")
        events = [
            TraceEvent.model_validate_json(line) for line in trace_path.read_text().splitlines()
        ]
        calls = measured[task_id]
        if [m["call_index"] for m in calls] != list(range(1, len(calls) + 1)):
            raise ValueError("measurement call ordering mismatch")
        if len(calls) != sum(e.event == "model_output" for e in events):
            raise ValueError("missing/extra generation measurements")
        if not calls or any(
            m["generate_seconds"] <= 0
            or m["call_seconds"] < m["generate_seconds"]
            or m["input_tokens"] <= 0
            or not 1 <= m["output_tokens"] <= 512
            or len(m["peak_allocated_bytes"]) != 2
            for m in calls
        ):
            raise ValueError("invalid measurement")
        seconds = (events[-1].timestamp - events[0].timestamp).total_seconds()
        if seconds <= 0:
            raise ValueError("invalid task timing")
        rows.append(
            {
                "task_id": task_id,
                "group": public[task_id]["instance_group_id"],
                "category": public[task_id]["category"],
                "success": scored[task_id]["success"],
                "status": scored[task_id]["status"],
                "task_seconds": seconds,
                "calls": len(calls),
                "parse_errors": sum(e.event == "parse_error" for e in events),
                "input_tokens": sum(m["input_tokens"] for m in calls),
                "output_tokens": sum(m["output_tokens"] for m in calls),
                "generate_seconds": sum(m["generate_seconds"] for m in calls),
                "tool_calls": sum(e.event == "tool_call_executed" for e in events),
                "peak_allocated_bytes_gpu0": max(m["peak_allocated_bytes"][0] for m in calls),
                "peak_allocated_bytes_gpu1": max(m["peak_allocated_bytes"][1] for m in calls),
                "failures": scored[task_id]["failures"],
            }
        )
    groups = [r["group"] for r in rows]
    success = [float(r["success"]) for r in rows]
    durations = [r["task_seconds"] for r in rows]
    output_count = sum(r["output_tokens"] for r in rows)
    generate_seconds = sum(r["generate_seconds"] for r in rows)
    calls = sum(r["calls"] for r in rows)
    success_durations = [r["task_seconds"] for r in rows if r["success"]]
    return {
        "model": identity["model_profile"],
        "source_identity": identity,
        "setup": setup,
        "tasks": 21,
        "semantic_groups": len(set(groups)),
        "successes": sum(success),
        "strict_success_rate": mean(success),
        "success_ci95_cluster_bootstrap": cluster_mean_interval(success, groups),
        "latency_all_tasks_seconds": distribution(durations),
        "mean_latency_ci95_cluster_bootstrap": cluster_mean_interval(durations, groups),
        "latency_successful_tasks_seconds": distribution(success_durations)
        if success_durations
        else None,
        "schema_validity": 1 - sum(r["parse_errors"] for r in rows) / calls,
        "statuses": dict(Counter(r["status"] for r in rows)),
        "category_success": {
            cat: {
                "successes": sum(r["success"] for r in rows if r["category"] == cat),
                "tasks": sum(r["category"] == cat for r in rows),
            }
            for cat in sorted({r["category"] for r in rows})
        },
        "output_tokens": output_count,
        "generate_seconds": generate_seconds,
        "output_tokens_per_generate_second_including_prefill": output_count / generate_seconds,
        "peak_allocated_gib_per_gpu": [
            max(r[f"peak_allocated_bytes_gpu{i}"] for r in rows) / 2**30 for i in range(2)
        ],
        "failure_reasons": evaluation["failures"],
        "rows": rows,
        "hashes": {
            "evaluation": sha(evaluation_path),
            "audit": sha(audit_path),
            "measurements": sha(run / "inference_metrics.jsonl"),
            "setup": sha(run / "model_setup.json"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--condition",
        nargs=3,
        type=Path,
        action="append",
        required=True,
        metavar=("RUN", "EVALUATION", "AUDIT"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("report output must be fresh")
    reports = [condition(*triple) for triple in args.condition]
    if len({r["model"] for r in reports}) != len(reports):
        raise ValueError("duplicate model condition")
    shared_keys = (
        "file_sha256",
        "generation",
        "git_commit",
        "software_versions",
        "measurement_protocol",
    )
    for report in reports[1:]:
        if any(
            report["source_identity"][k] != reports[0]["source_identity"][k] for k in shared_keys
        ):
            raise ValueError("cannot compare different software/source/input conditions")
        for k in ("gpus", "dtype", "quantization", "batch_size", "attention_implementation"):
            if report["setup"][k] != reports[0]["setup"][k]:
                raise ValueError("hardware or numerical condition differs")
    comparisons = []
    for i, left in enumerate(reports):
        for right in reports[i + 1 :]:
            groups = [row["group"] for row in left["rows"]]
            aligned = list(zip(left["rows"], right["rows"], strict=True))
            if any(a["task_id"] != b["task_id"] for a, b in aligned):
                raise ValueError("paired task ordering differs")
            delta = [float(a["success"]) - float(b["success"]) for a, b in aligned]
            latency = [a["task_seconds"] - b["task_seconds"] for a, b in aligned]
            comparisons.append(
                {
                    "left": left["model"],
                    "right": right["model"],
                    "success_difference": mean(delta),
                    "success_difference_ci95": cluster_mean_interval(delta, groups),
                    "latency_difference_seconds": mean(latency),
                    "latency_difference_ci95": cluster_mean_interval(latency, groups),
                }
            )
    args.output.mkdir(parents=True)
    report = {
        "scope": "Dev pilot; not held-out thesis evidence",
        "conditions": reports,
        "paired_comparisons": comparisons,
        "bootstrap_draws": 5000,
        "bootstrap_seed": 2026,
    }
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    all_rows = [{"model": r["model"], **row} for r in reports for row in r["rows"]]
    with (args.output / "tasks.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    lines = [
        "# Measured clean_v1.1 Dev pilot",
        "",
        "21 fixed Dev tasks; 95% cluster-bootstrap intervals (5,000 draws, seed 2026).",
        "",
        "| Model | Strict success | 95% CI | Mean s/task | Median | p95 | "
        "Output tok/s* | Peak GiB GPU0 / GPU1 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in reports:
        ci = r["success_ci95_cluster_bootstrap"]
        latency = r["latency_all_tasks_seconds"]
        peak = r["peak_allocated_gib_per_gpu"]
        lines.append(
            f"| {r['model']} | {int(r['successes'])}/21 ({r['strict_success_rate']:.1%}) | "
            f"{ci[0]:.1%}–{ci[1]:.1%} | {latency['mean']:.2f} | {latency['median']:.2f} | "
            f"{latency['p95']:.2f} | "
            f"{r['output_tokens_per_generate_second_including_prefill']:.2f} | "
            f"{peak[0]:.2f} / {peak[1]:.2f} |"
        )
    lines += [
        "",
        "*Generation throughput includes prefill and special output tokens; tokenizers differ.",
        "Task times include tool calls and schema retries; load/warm-up are separate in JSON.",
        "Single run per condition: spread reflects task differences, not repeat-run variance.",
        "Strict success requires annotated paths; correct final facts alone may fail.",
        "Historical Qwen 3B is excluded from controlled timing comparisons. Test remains sealed.",
        "See docs/evaluation/dev21_performance_protocol.md for design and limitations.",
    ]
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
