"""Describe authenticated Dev32 v2 traces without oracle scoring or inference."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.validation.context_stress_audit_v1 import equal, read_record
from react_agent.validation.guard_probe_audit_v2 import digest, require

ROOT = Path(__file__).resolve().parents[1]


def nearest_rank(values: list[float], proportion: float) -> float:
    """Use the named nearest-rank quantile, not an implicit library default."""
    require(bool(values) and 0 < proportion <= 1, "nonempty values and valid proportion")
    return sorted(values)[math.ceil(proportion * len(values)) - 1]


def records(path: Path) -> list[dict[str, Any]]:
    no_links(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def task_row(
    task: dict[str, Any], raw_task: Path
) -> tuple[dict[str, Any], Counter[str], Counter[str], Counter[str]]:
    """Read only observable event names/outcomes; never copy final-answer text."""
    legacy = records(raw_task / "execution/runtime/trace_legacy.jsonl")
    security = records(raw_task / "execution/runtime/trace_security.jsonl")
    events: Counter[str] = Counter(entry["event"] for entry in legacy)
    security_events: Counter[str] = Counter(entry["event"] for entry in security)
    tools: Counter[str] = Counter(
        entry["data"]["name"] for entry in legacy if entry["event"] == "tool_call_proposed"
    )
    results = [entry["data"] for entry in legacy if entry["event"] == "tool_result"]
    decisions: Counter[str] = Counter()
    for entry in security:
        if entry["event"] == "decision":
            data = json.loads(entry["data_json"])
            decisions[":".join((data["stage"], data["effect"], data["component"]))] += 1
    joined = task["guard_diagnostics"]["constrained"]["observer"]["joined"]
    require(
        len(joined) == task["guard_diagnostics"]["constrained"]["observer"]["response_records"]
        == len(task["roles"]["guard"]["calls"]),
        "guard response joins",
    )
    equal(events["run_start"], 1, "one run start")
    equal(events["run_end"], 1, "one run end")
    equal(events["final_answer"], 1, "one final answer")
    equal(events["model_output"], len(task["roles"]["agent"]["calls"]), "agent calls")
    equal(events["tool_call_proposed"], events["tool_call_executed"], "tool proposals")
    equal(events["tool_call_executed"], events["tool_result"], "tool results")
    row = dict(
        key=task["key"],
        branch="attack" if task["key"].startswith("ATK_") else "benign",
        level=task["level"],
        terminal=task["terminal"],
        recovered=task["recovered"],
        all_workers_graceful=task["observed_graceful"],
        agent_calls=len(task["roles"]["agent"]["calls"]),
        guard_calls=len(task["roles"]["guard"]["calls"]),
        guard_ok=sum(item["classification_status"] == "OK" for item in joined),
        tool_proposals=events["tool_call_proposed"],
        tool_results_ok=sum(item["ok"] is True for item in results),
        tool_results_error=sum(item["ok"] is False for item in results),
        pre_denials=sum(key.startswith("PRE:DENY:") for key in decisions.elements()),
        final_redactions=sum(key.startswith("FINAL:REDACT:") for key in decisions.elements()),
        startup_seconds=task["startup_seconds"],
        task_wall_seconds=task["task_timing"]["task_wall_seconds_including_setup_cleanup_recovery"],
    )
    return row, events, security_events, tools


def summarize(audit: dict[str, Any], raw: Path) -> dict[str, Any]:
    require(audit["protocol"] == "clause_dev32_gpu_release_audit_v2", "v2 audit protocol")
    require(audit["valid"] is True and audit["source_authenticated"] is True, "release audit")
    native = audit["native"]
    equal([native["completed"], native["expected"]], [32, 32], "complete Dev32")
    shards = native["shards"]
    equal(sorted(shard["shard"] for shard in shards), list(range(8)), "eight unique shards")
    rows: list[dict[str, Any]] = []
    event_counts: Counter[str] = Counter()
    security_counts: Counter[str] = Counter()
    tool_counts: Counter[str] = Counter()
    guard_statuses: Counter[str] = Counter()
    exit_methods: Counter[str] = Counter()
    decisions: Counter[str] = Counter()
    pairs: Counter[tuple[str, str, str]] = Counter()
    role_calls: Counter[str] = Counter()
    role_tokens: Counter[str] = Counter()
    role_generation_seconds: Counter[str] = Counter()
    for shard in shards:
        equal(shard["completed"], shard["expected"], "complete shard")
        for task in shard["tasks"]:
            key = task["key"]
            require(key.startswith(("ATK_", "BEN_")) and "__" in key, "public pair key")
            branch = "attack" if key.startswith("ATK_") else "benign"
            pair_id, level = key[4:].rsplit("__", 1)
            equal(level, task["level"], "level suffix")
            pairs[(pair_id, branch, level)] += 1
            raw_task = raw / "dev32" / f"shard{shard['shard']}" / "tasks" / key
            row, events, security_events, tools = task_row(task, raw_task)
            rows.append(row)
            event_counts.update(events)
            security_counts.update(security_events)
            tool_counts.update(tools)
            for item in task["guard_diagnostics"]["constrained"]["observer"]["joined"]:
                guard_statuses[item["stage"] + ":" + item["classification_status"]] += 1
            for role, record in task["guard_diagnostics"]["exit"]["roles"].items():
                exit_methods[role + ":" + record["method"]] += 1
            for entry in records(raw_task / "execution/runtime/trace_security.jsonl"):
                if entry["event"] == "decision":
                    data = json.loads(entry["data_json"])
                    decisions[":".join((data["stage"], data["effect"], data["component"]))] += 1
            for role, record in task["roles"].items():
                role_calls[role] += len(record["calls"])
                for call in record["calls"]:
                    role_tokens[role + ":input"] += call["input_tokens"]
                    role_tokens[role + ":output"] += call["output_tokens"]
                    role_generation_seconds[role] += call["generate_seconds"]
    require(len(rows) == len({row["key"] for row in rows}) == 32, "32 unique tasks")
    pair_ids = {key[0] for key in pairs}
    require(len(pair_ids) == 8, "eight selected public pairs")
    equal(
        {": ".join(key): value for key, value in pairs.items()},
        {": ".join(key): value for key, value in Counter(
            (pair, branch, level) for pair in pair_ids for branch in ("attack", "benign")
            for level in ("A2", "A6")
        ).items()},
        "exact paired coverage",
    )
    equal(event_counts["run_start"], 32, "32 run starts")
    equal(event_counts["final_answer"], 32, "32 finals")
    equal(sum(guard_statuses.values()), role_calls["guard"], "guard response count")
    wall = [row["task_wall_seconds"] for row in rows]
    startup = [row["startup_seconds"] for row in rows]
    return dict(
        protocol="clause_dev32_gpu_v2_descriptive_summary",
        source_commit=audit["source_commit"],
        kernel_version=audit["kernel_version"],
        tasks=rows,
        tasks_count=len(rows),
        terminals=dict(Counter(row["terminal"] for row in rows)),
        levels=dict(Counter(row["level"] for row in rows)),
        branches=dict(Counter(row["branch"] for row in rows)),
        recovered_tasks=sum(row["recovered"] for row in rows),
        all_workers_graceful_tasks=sum(row["all_workers_graceful"] for row in rows),
        agent_and_guard_calls=dict(role_calls),
        role_tokens=dict(role_tokens),
        role_generate_seconds=dict(role_generation_seconds),
        role_output_tokens_per_generate_second={
            role: role_tokens[role + ":output"] / seconds if seconds else None
            for role, seconds in role_generation_seconds.items()
        },
        guard_classifications=dict(guard_statuses),
        tasks_without_guard=sum(row["guard_calls"] == 0 for row in rows),
        exit_methods=dict(exit_methods),
        trace_events=dict(event_counts),
        security_events=dict(security_counts),
        security_decisions=dict(decisions),
        proposed_tools=dict(tool_counts),
        tool_results_ok=sum(row["tool_results_ok"] for row in rows),
        tool_results_error=sum(row["tool_results_error"] for row in rows),
        task_wall_seconds=dict(total=sum(wall), median=statistics.median(wall),
                               p95_nearest_rank=nearest_rank(wall, 0.95), maximum=max(wall)),
        startup_seconds=dict(total=sum(startup), median=statistics.median(startup),
                             p95_nearest_rank=nearest_rank(startup, 0.95)),
        raw_files_verified=len(audit["raw_sha256"]),
        remote_files_verified=len(audit["remote_sha256"]),
        phase5_accepted=False,
        quality_scored=False,
        model_weight_sha_verified=False,
        scope="Observable public Dev diagnostics only. Completion, guard JSON validity and policy "
              "decisions are not ASR/FPR/benign utility; no oracle, Test or new inference. "
              "Summed task wall time is not calendar elapsed time.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    for path in (args.audit, args.raw, args.output):
        no_links(path)
    output = args.output.resolve()
    require(
        not output.exists() and output.is_relative_to(ROOT / "results")
        and not args.raw.resolve().is_relative_to(output)
        and not output.is_relative_to(args.raw.resolve()),
        "fresh results output outside raw evidence",
    )
    before = inventory(args.raw)
    selected = read_record(args.audit)
    equal(before, selected["raw_sha256"], "raw unchanged since independent audit")
    audit_sha256 = digest(args.audit)
    summary = summarize(selected, args.raw)
    equal(inventory(args.raw), before, "raw unchanged during report")
    equal(digest(args.audit), audit_sha256, "audit unchanged during report")
    summary.update(audit_sha256=audit_sha256, script_sha256=digest(Path(__file__)))
    output.mkdir()
    write_receipt(output / "summary.json", summary)
    with (output / "tasks.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary["tasks"][0]))
        writer.writeheader()
        writer.writerows(summary["tasks"])
    print("CLAUSE_DEV32_V2_DESCRIPTIVE_REPORT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
