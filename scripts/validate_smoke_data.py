#!/usr/bin/env python3
"""Validate Phase 1 task counts, assignments, replays, and tool coverage."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from react_agent.schemas.task import SmokeTask

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "smoke"
TOOL_NAMES = {
    "doc_search",
    "doc_read",
    "db_query",
    "cached_search",
    "cached_fetch",
    "calculator",
    "send_email_mock",
    "post_webhook_mock",
}
EXPECTED_CATEGORIES = {
    "no_tool": 2,
    "document_lookup": 3,
    "database": 3,
    "cached_lookup": 2,
    "calculator": 2,
    "multi_tool": 3,
    "external_sink": 2,
    "error_recovery": 3,
}


def load_tasks() -> list[SmokeTask]:
    lines = (DATA_ROOT / "tasks.jsonl").read_text(encoding="utf-8").splitlines()
    return [SmokeTask.model_validate_json(line) for line in lines if line.strip()]


def main() -> int:
    tasks = load_tasks()
    replays = json.loads((DATA_ROOT / "replay_responses.json").read_text(encoding="utf-8"))
    failures: list[str] = []

    ids = [task.task_id for task in tasks]
    if len(tasks) != 20 or len(set(ids)) != 20:
        failures.append("tasks must contain exactly 20 unique IDs")
    if Counter(task.author for task in tasks) != {"huy": 10, "minh": 10}:
        failures.append("author allocation must be exactly 10 Huy / 10 Minh")
    if Counter(task.category for task in tasks) != EXPECTED_CATEGORIES:
        failures.append("category distribution does not match the Phase 1 contract")
    if set(replays) != set(ids):
        failures.append("replay response keys must exactly match task IDs")

    covered = {
        tool
        for task in tasks
        for sequence in task.expected.acceptable_tool_sequences
        for tool in sequence
    }
    if covered != TOOL_NAMES:
        failures.append(f"expected tool coverage mismatch: {sorted(TOOL_NAMES - covered)}")

    for task_id, responses in replays.items():
        if not isinstance(responses, list) or not responses:
            failures.append(f"{task_id} must have at least one replay response")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: 20 tasks, 10/10 ownership, category counts, replays, and 8 tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
