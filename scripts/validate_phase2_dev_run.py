#!/usr/bin/env python3
"""Audit downloaded Phase 2 Kaggle Dev-pilot artifacts without Test access."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from react_agent.schemas.trace import TraceEvent

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data" / "clean" / "v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    artifact_root = parse_args().artifacts.resolve()
    run_root = artifact_root / "phase2_clean_dev_pilot"
    failures: list[str] = []
    required = (
        artifact_root / "kaggle_bundle_info.json",
        run_root / "run_metadata.json",
        run_root / "summary.json",
        run_root / "results.json",
        run_root / "traces.jsonl",
        run_root / "evaluation.json",
    )
    for path in required:
        if not path.is_file():
            failures.append(f"missing artifact: {path}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    bundle = _load_json(required[0])
    metadata = _load_json(required[1])
    summary = _load_json(required[2])
    results = _load_json(required[3])
    evaluation = _load_json(required[5])
    selection = _load_json(CLEAN_ROOT / "dev_pilot" / "task_ids.json")["task_ids"]
    expected_ids = set(selection)
    public_dev_hash = _sha256(CLEAN_ROOT / "splits" / "dev.jsonl")

    if bundle.get("test_in_bundle") is not False:
        failures.append("bundle does not prove Test exclusion")
    if bundle.get("private_ground_truth_in_bundle") is not False:
        failures.append("bundle does not prove private-ground-truth exclusion")
    if summary.get("test_tasks_loaded") != 0 or summary.get("private_ground_truth_loaded") != 0:
        failures.append("run loaded Test or private ground truth")
    if metadata.get("selected_task_ids") != selection:
        failures.append("run task selection differs from frozen 21-task Dev pilot")
    if metadata.get("public_dev_sha256") != public_dev_hash:
        failures.append("run public Dev hash differs from local frozen Dev")
    if metadata.get("git_commit") != bundle.get("git_commit"):
        failures.append("run commit differs from Kaggle bundle commit")
    if summary.get("total_tasks") != 21 or summary.get("terminal_runs") != 21:
        failures.append("pilot did not produce 21 terminal runs")
    if summary.get("model_crashes") != 0:
        failures.append("pilot contains a model crash")
    result_ids = {item["task_id"] for item in results}
    if result_ids != expected_ids or len(results) != 21:
        failures.append("run results do not join one-to-one with selected Dev tasks")
    if evaluation.get("test_tasks_read") != 0 or evaluation.get("evaluated_tasks") != 21:
        failures.append("local evaluator scope is not exactly the selected Dev pilot")

    events = [
        TraceEvent.model_validate_json(line)
        for line in required[4].read_text(encoding="utf-8").splitlines()
        if line
    ]
    if evaluation.get("trace_events_valid") != len(events):
        failures.append("evaluator trace count differs from schema-valid trace count")
    task_event_counts: dict[str, Counter[str]] = defaultdict(Counter)
    call_events: dict[tuple[str, str], list[str]] = defaultdict(list)
    for event in events:
        task_event_counts[event.task_id][event.event] += 1
        if event.call_id is not None:
            call_events[(event.task_id, event.call_id)].append(event.event)
    for task_id in expected_ids:
        if task_event_counts[task_id]["run_start"] != 1:
            failures.append(f"{task_id} does not have exactly one run_start")
        if task_event_counts[task_id]["run_end"] != 1:
            failures.append(f"{task_id} does not have exactly one run_end")
    expected_order = ["tool_call_proposed", "tool_call_executed", "tool_result"]
    bad_calls = [call_key for call_key, order in call_events.items() if order != expected_order]
    if bad_calls:
        failures.append(f"invalid Tool Broker event order for calls: {bad_calls[:10]}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(
        f"PASS: 21 Dev terminal runs, {len(events)} valid trace events, 0 crashes, "
        "0 Test/private worker access, and valid Tool Broker ordering"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
