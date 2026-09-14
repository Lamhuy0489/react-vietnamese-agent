"""Summarize an authenticated native shard without oracle scoring or inference."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.validation.context_stress_audit_v1 import equal
from react_agent.validation.guard_probe_audit_v2 import digest, require


def summarize(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Descriptive totals only; role throughput includes completely joined calls only."""
    rows = []
    roles: dict[str, Any] = {}
    classifications: Counter[str] = Counter()
    for task in tasks:
        guard = task["guard_diagnostics"]
        joined = guard["joined"] if guard else []
        for record in joined:
            classifications[record["stage"] + ":" + record["classification_status"]] += 1
        rows.append(
            dict(
                key=task["key"],
                level=task["level"],
                branch="attack" if task["key"].startswith("ATK_") else "benign",
                terminal=task["terminal"],
                recovered=task["recovered"],
                all_workers_graceful=task["observed_graceful"],
                returned_guard_responses=len(joined),
                valid_guard_responses=sum(r["classification_status"] == "OK" for r in joined),
                startup_seconds=task["startup_seconds"],
                runtime_seconds=task["runtime_total_seconds"],
                task_wall_seconds=task["task_timing"][
                    "task_wall_seconds_including_setup_cleanup_recovery"
                ],
            )
        )
        for role, data in task["roles"].items():
            item = roles.setdefault(
                role,
                dict(
                    workers=0,
                    worker_attempts=0,
                    fully_joined_workers=0,
                    failed_or_partial_workers=0,
                    joined_calls=0,
                    input_tokens=0,
                    output_tokens=0,
                    generate_seconds=0.0,
                ),
            )
            item["workers"] += 1
            item["worker_attempts"] += data["worker_attempts"]
            item["fully_joined_workers"] += data["policy_attention_verified"]
            item["failed_or_partial_workers"] += data["failed_or_partial"]
            for call in data["calls"]:
                item["joined_calls"] += 1
                for name in ("input_tokens", "output_tokens", "generate_seconds"):
                    item[name] += call[name]
    for item in roles.values():
        item["tokens_per_generate_second_joined_only"] = (
            item["output_tokens"] / item["generate_seconds"] if item["generate_seconds"] else None
        )
    return dict(
        tasks=rows,
        tasks_count=len(rows),
        terminals=dict(Counter(t["terminal"] for t in rows)),
        recovered_tasks=sum(t["recovered"] for t in rows),
        all_graceful_tasks=sum(t["all_workers_graceful"] for t in rows),
        returned_guard_classifications=dict(classifications),
        roles=roles,
        task_wall_seconds_total=sum(t["task_wall_seconds"] for t in rows),
        startup_seconds_total=sum(t["startup_seconds"] for t in rows),
        scope="Descriptive single-shard Dev diagnostics. Guard counts include returned responses "
        "only, not backend failures without a response. Throughput excludes unjoined partial "
        "calls; all task/worker failures remain counted. Not utility/ASR/FPR or model ranking.",
    )


def path_coverage(raw: Path) -> dict[str, Any]:
    """Count observable events, including action omission; never infer a semantic score."""
    events: Counter[str] = Counter()
    answers: Counter[str] = Counter()
    lifecycle: Counter[str] = Counter()
    for task in sorted((raw / "grouped/tasks").iterdir()):
        trace = task / "execution/runtime/trace_legacy.jsonl"
        for line in trace.read_text().splitlines():
            record = json.loads(line)
            events[record["event"]] += 1
            if record["event"] == "final_answer":
                answers[record["data"]["answer"]] += 1
        runtime = json.loads((task / "execution/pair_runtime.json").read_text())
        for worker in runtime["snapshot"]["workers"].values():
            for event in worker["lifecycle"]:
                lifecycle[event["method"] + (":reaped" if event["reaped"] else ":unreaped")] += 1
    return dict(
        trace_events=dict(events),
        distinct_final_answers=len(answers),
        lifecycle=dict(lifecycle),
        quality_scoring=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("audit", "raw", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    for path in (args.audit, args.raw, args.output):
        no_links(path)
    require(
        not args.output.exists()
        and all(
            not args.output.resolve().is_relative_to(p.resolve())
            and not p.resolve().is_relative_to(args.output.resolve())
            for p in (args.raw, args.audit, Path(__file__).resolve().parents[1] / "data")
        ),
        "fresh summary output outside frozen inputs",
    )
    audit_hash = digest(args.audit)
    audit = json.loads(args.audit.read_text())
    require(
        audit["protocol"] == "grouped_gpu_v3_release_audit"
        and audit["artifact_integrity_valid"] is True
        and audit["remote_source_authenticated"] is True
        and audit["completed"] == audit["expected"] == len(audit["tasks"]) == 14,
        "complete authenticated native audit required",
    )
    before = inventory(args.raw)
    equal(before, audit["raw_sha256"], "raw evidence unchanged since audit")
    summary = summarize(audit["tasks"])
    summary["path_coverage"] = path_coverage(args.raw)
    summary.update(
        protocol="grouped_gpu_v3_descriptive_summary",
        audit_sha256=audit_hash,
        source_commit=audit["source_commit"],
        shard=audit["shard"],
        actual_kernel=audit["actual_kernel"],
        kernel_version=audit["kernel_version"],
        script_sha256=digest(Path(__file__)),
        phase5_accepted=False,
        quality_scoring=False,
    )
    equal(inventory(args.raw), before, "raw unchanged during summary")
    equal(digest(args.audit), audit_hash, "audit unchanged during summary")
    args.output.mkdir(parents=True)
    write_receipt(args.output / "summary.json", summary)
    with (args.output / "tasks.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary["tasks"][0]))
        writer.writeheader()
        writer.writerows(summary["tasks"])
    print(json.dumps(dict(tasks=summary["tasks_count"], terminals=summary["terminals"])))


if __name__ == "__main__":
    main()
