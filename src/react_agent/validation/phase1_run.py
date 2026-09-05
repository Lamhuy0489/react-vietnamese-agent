"""Read-only validation of Phase 1 observable run evidence."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from react_agent.schemas.tool import ToolCall, ToolResult
from react_agent.schemas.trace import TraceEvent

EXPECTED_TASK_IDS = {f"smoke_{index:03d}" for index in range(1, 21)}
TERMINAL_STATUSES = {"completed", "parse_failure", "max_steps", "model_error"}
TOOL_EVENTS = {"tool_call_proposed", "tool_call_executed", "tool_result"}


def validate_phase1_run(run_directory: Path) -> dict[str, Any]:
    failures: list[str] = []
    try:
        summary = json.loads((run_directory / "summary.json").read_text(encoding="utf-8"))
        events = [
            TraceEvent.model_validate_json(line)
            for line in (run_directory / "traces.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, ValueError, ValidationError) as error:
        return {"valid": False, "failures": [f"invalid run artifact: {error}"]}
    if not isinstance(summary, dict):
        return {"valid": False, "failures": ["summary must be an object"]}

    runs: dict[str, list[TraceEvent]] = defaultdict(list)
    for event in events:
        runs[event.run_id].append(event)
    task_counts = Counter(run[0].task_id for run in runs.values())
    if set(task_counts) != EXPECTED_TASK_IDS or any(count != 1 for count in task_counts.values()):
        failures.append("trace must cover each of smoke_001..smoke_020 exactly once")
    if len(runs) != 20:
        failures.append("trace must contain exactly 20 runs")

    status_counts: Counter[str] = Counter()
    tools: set[str] = set()
    for run_id, run in runs.items():
        names = [event.event for event in run]
        if (
            names[0] != "run_start"
            or names[-1] != "run_end"
            or names.count("run_start") != 1
            or names.count("run_end") != 1
        ):
            failures.append(f"{run_id}: expected exactly one start/end boundary")
        if len({event.task_id for event in run}) != 1:
            failures.append(f"{run_id}: inconsistent task identity")
        # On parse_failure/model_error, run_end.step counts completed steps;
        # the preceding attempted model step can be one larger.
        attempts = [event for event in run if event.event != "run_end"]
        if any(left.step > right.step for left, right in zip(attempts, attempts[1:], strict=False)):
            failures.append(f"{run_id}: step numbers move backwards")
        status = run[-1].data.get("status")
        if not isinstance(status, str) or status not in TERMINAL_STATUSES:
            failures.append(f"{run_id}: invalid terminal status")
        else:
            status_counts[status] += 1
        final_answers = [event for event in run if event.event == "final_answer"]
        if status == "completed" and (
            len(final_answers) != 1 or not isinstance(final_answers[0].data.get("answer"), str)
        ):
            failures.append(f"{run_id}: completed run lacks exactly one final answer")
        if status != "completed" and final_answers:
            failures.append(f"{run_id}: non-completed run contains a final answer")

        calls: dict[str, list[TraceEvent]] = defaultdict(list)
        for event in run:
            if event.event in TOOL_EVENTS:
                if not event.call_id:
                    failures.append(f"{run_id}: tool event lacks call_id")
                else:
                    calls[event.call_id].append(event)
            elif event.call_id is not None:
                failures.append(f"{run_id}: non-tool event carries call_id")
        for call_id, call_events in calls.items():
            if [event.event for event in call_events] != [
                "tool_call_proposed",
                "tool_call_executed",
                "tool_result",
            ]:
                failures.append(f"{run_id}/{call_id}: invalid tool event order")
                continue
            try:
                proposal = ToolCall.model_validate(call_events[0].data)
                result = ToolResult.model_validate(call_events[-1].data)
            except ValidationError as error:
                failures.append(f"{run_id}/{call_id}: invalid tool payload: {error}")
                continue
            if proposal.call_id != call_id or result.call_id != call_id:
                failures.append(f"{run_id}/{call_id}: payload call ID mismatch")
            if proposal.name != result.tool_name:
                failures.append(f"{run_id}/{call_id}: result tool name mismatch")
            if len({event.step for event in call_events}) != 1:
                failures.append(f"{run_id}/{call_id}: tool events span multiple steps")
            tools.add(proposal.name)

    expected_summary = {
        "total_tasks": len(runs),
        "terminal_runs": sum(status_counts.values()),
        "completed_runs": status_counts["completed"],
        "crashed_runs": status_counts["model_error"],
        "tools_covered": sorted(tools),
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            failures.append(f"summary {key} does not match trace")
    outputs = sum(event.event == "model_output" for event in events)
    parse_errors = sum(event.event == "parse_error" for event in events)
    validity = (outputs - parse_errors) / outputs if outputs else None
    if summary.get("schema_validity_rate") != validity:
        failures.append("summary schema_validity_rate does not match trace")
    if status_counts["model_error"]:
        failures.append("run contains model/runtime errors")
    return {
        "valid": not failures,
        "failures": failures,
        "runs": len(runs),
        "trace_events": len(events),
        "status_counts": dict(sorted(status_counts.items())),
        "tools_covered": sorted(tools),
    }
