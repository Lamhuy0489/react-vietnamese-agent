#!/usr/bin/env python3
"""Score saved v1.1 Dev checkpoints locally without loading held-out tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from react_agent.agent.state import RunResult
from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.schemas.clean_task import CleanGroundTruth
from react_agent.schemas.trace import TraceEvent
from react_agent.tools.factory import build_clean_registry
from react_agent.validation.clean_v11 import EVALUATOR_VERSION, calls_from_trace, score_observation

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data/clean/v1_1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("evaluation output already exists; preserve prior artifacts")
    identity = json.loads((args.artifacts / "identity.json").read_text())
    expected_dev = hashlib.sha256((CLEAN_ROOT / "splits/dev.jsonl").read_bytes()).hexdigest()
    if identity["file_sha256"]["dev"] != expected_dev:
        raise ValueError("public Dev identity mismatch")
    selection = json.loads((CLEAN_ROOT / "dev_pilot/task_ids.json").read_text())["task_ids"]
    if identity["task_ids"] != selection:
        raise ValueError("selected task identity mismatch")
    truths = {
        item.task_id: item
        for item in (
            CleanGroundTruth.model_validate_json(line)
            for line in (CLEAN_ROOT / "private/dev_ground_truth.jsonl").read_text().splitlines()
        )
    }
    rows = []
    for task_id in selection:
        directory = args.artifacts / "tasks" / task_id
        checkpoint = json.loads((directory / "result.json").read_text())
        trace_path = directory / "trace.jsonl"
        if hashlib.sha256(trace_path.read_bytes()).hexdigest() != checkpoint["trace_sha256"]:
            raise ValueError("checkpoint trace hash mismatch")
        result = RunResult.model_validate(checkpoint["result"])
        events = [
            TraceEvent.model_validate_json(line) for line in trace_path.read_text().splitlines()
        ]
        if result.task_id != task_id or any(
            event.task_id != task_id or event.run_id != result.run_id for event in events
        ):
            raise ValueError("trace task/run identity mismatch")
        if not events or events[0].event != "run_start" or events[-1].event != "run_end":
            raise ValueError("missing terminal trace boundary")
        final_answers = [event.data["answer"] for event in events if event.event == "final_answer"]
        if result.status == "completed" and final_answers != [result.final_answer]:
            raise ValueError("final answer differs from checkpoint")
        calls = calls_from_trace(events)
        if [name for name, _, _ in calls] != result.tool_sequence:
            raise ValueError("tool sequence differs from checkpoint")
        reference_broker = ToolBroker(
            build_clean_registry(CLEAN_ROOT / "environment"), TraceLogger()
        )
        outcome = score_observation(
            truths[task_id],
            result.final_answer or "",
            calls,
            reference_broker,
            status=result.status,
        )
        rows.append(
            {"task_id": task_id, "status": result.status, "trace_events": len(events), **outcome}
        )
    report = {
        "evaluator": EVALUATOR_VERSION,
        "scope": "Dev pilot diagnostic; not thesis Test result",
        "test_tasks_read": 0,
        "evaluated_tasks": len(rows),
        "successes": sum(row["success"] for row in rows),
        "trace_events": sum(row["trace_events"] for row in rows),
        "failures": dict(Counter(reason for row in rows for reason in row["failures"])),
        "source_identity": identity,
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in {"results", "source_identity"}
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
