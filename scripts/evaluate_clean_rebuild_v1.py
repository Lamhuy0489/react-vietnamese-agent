#!/usr/bin/env python3
"""Score saved v1.1 Dev checkpoints for rebuild A (full Dev, optional numfix).

Copy of the Phase 5-pinned `evaluate_clean_v11_dev.py` plus `--full-dev` and
`--numfix`; the original stays byte-identical because native wiring QA pins it.
A Test run (``"split": "test"`` in its identity) is scored with the Test ground
truth only while the R3 freeze manifest still matches; Dev runs never load Test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import react_agent.evaluation.final_config_v1 as final_config_v1
from react_agent.agent.state import RunResult
from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.schemas.clean_task import CleanGroundTruth
from react_agent.schemas.trace import TraceEvent
from react_agent.tools.factory import build_clean_registry
from react_agent.validation import clean_rebuild_v1
from react_agent.validation.clean_v11 import EVALUATOR_VERSION, calls_from_trace, score_observation

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data/clean/v1_1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--numfix", action="store_true",
                        help="use the rebuild numeric-token fix (clean_rebuild_v1)")
    parser.add_argument("--full-dev", action="store_true",
                        help="score the tasks listed in identity.json (150-task Dev API run)")
    args = parser.parse_args()
    evaluator = clean_rebuild_v1.activate() if args.numfix else EVALUATOR_VERSION
    if args.output.exists():
        raise ValueError("evaluation output already exists; preserve prior artifacts")
    identity = json.loads((args.artifacts / "identity.json").read_text())
    split = identity.get("split", "dev")
    expected = hashlib.sha256((CLEAN_ROOT / f"splits/{split}.jsonl").read_bytes()).hexdigest()
    if identity["file_sha256"][split] != expected:
        raise ValueError(f"public {split} identity mismatch")
    if split == "test":
        if not identity.get("dry_run_dummy"):
            final_config_v1.verify(ROOT)
            if identity.get("final_config_sha256") != final_config_v1.manifest_sha256(ROOT):
                raise ValueError("Test run was not made under the current freeze manifest")
        test_ids = [json.loads(line)["task_id"]
                    for line in (CLEAN_ROOT / "splits/test.jsonl").read_text().splitlines()]
        selection = identity["task_ids"]
        if selection != test_ids:
            raise ValueError("Test runs must cover the whole Test split")
    elif args.full_dev:
        dev_ids = [json.loads(line)["task_id"]
                   for line in (CLEAN_ROOT / "splits/dev.jsonl").read_text().splitlines()]
        selection = identity["task_ids"]
        if selection != dev_ids[: len(selection)]:
            raise ValueError("selected task identity mismatch")
    else:
        selection = json.loads((CLEAN_ROOT / "dev_pilot/task_ids.json").read_text())["task_ids"]
        if identity["task_ids"] != selection:
            raise ValueError("selected task identity mismatch")
    truths = {
        item.task_id: item
        for item in (
            CleanGroundTruth.model_validate_json(line)
            for line in (CLEAN_ROOT / f"private/{split}_ground_truth.jsonl")
            .read_text().splitlines()
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
        "evaluator": evaluator,
        "scope": ("DRY RUN with a CPU stand-in; not a result" if identity.get("dry_run_dummy")
                  else "Held-out Test" if split == "test"
                  else "Dev pilot diagnostic; not thesis Test result"),
        "test_tasks_read": len(rows) if split == "test" else 0,
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
