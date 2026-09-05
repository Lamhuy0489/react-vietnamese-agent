#!/usr/bin/env python3
"""Validate terminal state and trace integrity of a Phase 1 run directory."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    failures: list[str] = []
    summary = json.loads((args.run_directory / "summary.json").read_text(encoding="utf-8"))
    trace_lines = (args.run_directory / "traces.jsonl").read_text(encoding="utf-8").splitlines()
    events: list[dict[str, Any]] = [json.loads(line) for line in trace_lines]
    runs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        runs[event["run_id"]].append(event)

    if len(runs) != 20 or summary.get("terminal_runs", len(runs)) != 20:
        failures.append("run must contain exactly 20 terminal trajectories")
    if summary.get("crashed_runs") != 0:
        failures.append("run must contain zero model/runtime crashes")
    for run_id, run_events in runs.items():
        if run_events[0]["event"] != "run_start" or run_events[-1]["event"] != "run_end":
            failures.append(f"{run_id}: trace must start/end correctly")
        calls: dict[str, list[str]] = defaultdict(list)
        for event in run_events:
            call_id = event.get("call_id")
            if call_id:
                calls[call_id].append(event["event"])
        for call_id, call_events in calls.items():
            expected = ["tool_call_proposed", "tool_call_executed", "tool_result"]
            if call_events != expected:
                failures.append(f"{run_id}/{call_id}: invalid tool event order")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"PASS: {len(runs)} terminal traces, {len(events)} events, valid tool-call order")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
