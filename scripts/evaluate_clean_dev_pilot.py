#!/usr/bin/env python3
"""Evaluate a Phase 2 Dev-only pilot after inference; never reads held-out Test."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from react_agent.schemas.clean_task import CleanGroundTruth, CleanPublicTask
from react_agent.schemas.trace import TraceEvent

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data" / "clean" / "v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value).casefold())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(re.findall(r"\w+", text, flags=re.UNICODE))


def _fact_present(answer: str, value: object) -> bool:
    if isinstance(value, list):
        return all(_fact_present(answer, item) for item in value)
    if isinstance(value, bool):
        accepted = ("có", "đúng", "true") if value else ("không", "sai", "false")
        normalized = _normalize(answer)
        return any(term in normalized for term in accepted)
    normalized_answer = _normalize(answer)
    normalized_value = _normalize(value)
    if normalized_value in normalized_answer:
        return True
    if isinstance(value, (int, float)):
        digits = re.sub(r"\D", "", str(value))
        answer_numbers = [re.sub(r"\D", "", token) for token in re.findall(r"[\d.,]+", answer)]
        return digits in answer_numbers
    return False


def evaluate(artifacts: Path) -> dict[str, Any]:
    selection = json.loads(
        (CLEAN_ROOT / "dev_pilot" / "task_ids.json").read_text(encoding="utf-8")
    )["task_ids"]
    selected_ids = set(selection)
    dev_tasks = {
        item["task_id"]: CleanPublicTask.model_validate(item)
        for item in _load_jsonl(CLEAN_ROOT / "splits" / "dev.jsonl")
        if item["task_id"] in selected_ids
    }
    dev_ground_truth = {
        item["task_id"]: CleanGroundTruth.model_validate(item)
        for item in _load_jsonl(CLEAN_ROOT / "private" / "dev_ground_truth.jsonl")
        if item["task_id"] in selected_ids
    }
    raw_results = json.loads((artifacts / "results.json").read_text(encoding="utf-8"))
    results = {item["task_id"]: item for item in raw_results}
    traces = [TraceEvent.model_validate(item) for item in _load_jsonl(artifacts / "traces.jsonl")]
    events_by_task: dict[str, list[TraceEvent]] = defaultdict(list)
    for event in traces:
        events_by_task[event.task_id].append(event)

    rows: list[dict[str, Any]] = []
    taxonomy: Counter[str] = Counter()
    for task_id in selection:
        task = dev_tasks[task_id]
        truth = dev_ground_truth[task_id]
        result = results.get(task_id)
        failures: list[str] = []
        if result is None:
            failures.append("missing_run_result")
            rows.append({"task_id": task_id, "category": task.category, "failures": failures})
            taxonomy.update(failures)
            continue
        sequence = result["tool_sequence"]
        if result["status"] != "completed":
            failures.append(f"terminal_{result['status']}")
        if sequence not in truth.acceptable_sequences:
            failures.append("tool_sequence")
        answer = result.get("final_answer") or ""
        missing_facts = [
            fact.fact_id
            for fact in truth.required_answer_facts
            if not _fact_present(answer, fact.value)
        ]
        if missing_facts:
            failures.append("required_answer_facts")

        task_events = events_by_task[task_id]
        proposed = [event for event in task_events if event.event == "tool_call_proposed"]
        tool_results = [event for event in task_events if event.event == "tool_result"]
        arguments_usable = len(proposed) == len(sequence)
        if not arguments_usable:
            failures.append("argument_trace")
        if truth.fault_plan:
            injected = [
                event
                for event in tool_results
                if isinstance(event.data.get("metadata"), dict)
                and event.data["metadata"].get("injected") is True
            ]
            if len(injected) != len(truth.fault_plan):
                failures.append("error_recovery_observation")
        taxonomy.update(failures)
        rows.append(
            {
                "task_id": task_id,
                "category": task.category,
                "status": result["status"],
                "tool_sequence": sequence,
                "sequence_valid": sequence in truth.acceptable_sequences,
                "argument_labels_usable": arguments_usable,
                "missing_answer_facts": missing_facts,
                "task_success": not failures,
                "failures": failures,
            }
        )

    category_success: Counter[str] = Counter()
    category_total: Counter[str] = Counter()
    for row in rows:
        category_total[row["category"]] += 1
        category_success[row["category"]] += bool(row.get("task_success"))
    summary = {
        "scope": "clean_v1.0_dev_pilot_only",
        "test_tasks_read": 0,
        "evaluated_tasks": len(rows),
        "trace_events_valid": len(traces),
        "completed": sum(row.get("status") == "completed" for row in rows),
        "task_successes": sum(bool(row.get("task_success")) for row in rows),
        "sequence_labels_usable": sum("tool_sequence" not in row["failures"] for row in rows),
        "argument_labels_usable": sum(bool(row.get("argument_labels_usable")) for row in rows),
        "answer_fact_labels_usable": sum(
            "required_answer_facts" not in row["failures"] for row in rows
        ),
        "failure_taxonomy": dict(sorted(taxonomy.items())),
        "category_results": {
            category: {"successes": category_success[category], "total": total}
            for category, total in sorted(category_total.items())
        },
        "results": rows,
    }
    return summary


def main() -> int:
    args = parse_args()
    result = evaluate(args.artifacts.resolve())
    output = args.output or args.artifacts / "evaluation.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in result.items() if key != "results"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
