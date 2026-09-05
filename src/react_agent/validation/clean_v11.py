"""Evidence-backed pre-split checks for the approved replacement benchmark."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.schemas.clean_task import CleanGroundTruth, CleanPublicTask, OracleStep
from react_agent.schemas.tool import ToolResult
from react_agent.schemas.trace import TraceEvent
from react_agent.tools.factory import build_clean_registry
from react_agent.validation.clean_comparators import argument_matches, fact_in_content, fact_in_text
from react_agent.validation.clean_environment import validate_environment
from react_agent.validation.clean_integrity import semantic_instance_groups
from react_agent.validation.clean_pool import (
    CATEGORY_QUOTAS,
    MINIMUM_TOOL_COVERAGE,
    _duplicate_groups,
)

EVALUATOR_VERSION = "clean_v1_1_typed_v1"


def load_pool(root: Path) -> tuple[list[CleanPublicTask], list[CleanGroundTruth]]:
    tasks = [
        CleanPublicTask.model_validate_json(line)
        for line in (root / "pool/tasks.jsonl").read_text().splitlines()
    ]
    truth = [
        CleanGroundTruth.model_validate_json(line)
        for line in (root / "private/pool_ground_truth.jsonl").read_text().splitlines()
    ]
    return tasks, truth


def oracle_answer(truth: CleanGroundTruth) -> str:
    if truth.expected_outcome == "clarification":
        return "Bạn vui lòng cung cấp " + ", ".join(truth.missing_slots) + "?"
    return "\n".join(
        json.dumps(fact.value, ensure_ascii=False)
        if isinstance(fact.value, (list, bool))
        else str(fact.value)
        for fact in truth.required_answer_facts
    )


def score_observation(
    truth: CleanGroundTruth,
    answer: str,
    calls: list[tuple[str, dict[str, Any], ToolResult]],
    reference_broker: ToolBroker,
    *,
    status: str = "completed",
) -> dict[str, Any]:
    failures: list[str] = []
    sequence = [name for name, _, _ in calls]
    if status != "completed":
        failures.append(f"terminal:{status}")
    if sequence not in truth.acceptable_sequences:
        failures.append("tool_sequence")
    if set(sequence) & set(truth.forbidden_tools):
        failures.append("forbidden_tool")
    if not all(fact_in_text(answer, fact) for fact in truth.required_answer_facts):
        failures.append("answer_facts")
    if truth.expected_outcome == "clarification" and "?" not in answer:
        failures.append("clarification_question")
    argument_results: list[bool] = []
    for validator in truth.argument_validators:
        matched = any(
            name == validator.tool
            and argument_matches(validator, arguments, result, reference_broker)
            for name, arguments, result in calls
        )
        argument_results.append(matched)
    if not all(argument_results):
        failures.append("arguments")
    read_ids = {
        result.content.get("doc_id", result.content.get("page_id"))
        for name, _, result in calls
        if name in {"doc_read", "cached_fetch"} and result.ok and isinstance(result.content, dict)
    }
    if not set(truth.retrieval_targets) <= read_ids:
        failures.append("required_evidence")
    faults = [
        (index, result)
        for index, (_, _, result) in enumerate(calls)
        if result.metadata.get("injected") is True
    ]
    if len(faults) != len(truth.fault_plan):
        failures.append("fault_observation")
    for index, _result in faults:
        name = calls[index][0]
        if not any(
            later_name == name and later_result.ok
            for later_name, _, later_result in calls[index + 1 :]
        ):
            failures.append("recovery")
    if any(not result.ok and result.metadata.get("injected") is not True for _, _, result in calls):
        failures.append("unresolved_tool_error")
    return {"success": not failures, "failures": failures, "argument_checks": argument_results}


def oracle_check(task: CleanPublicTask, truth: CleanGroundTruth, root: Path) -> dict[str, Any]:
    alternatives: list[dict[str, Any]] = []
    grounded = True
    for sequence in truth.acceptable_sequences:
        queues: dict[str, list[OracleStep]] = defaultdict(list)
        for step in truth.oracle_steps:
            queues[step.tool].append(step)
        logger = TraceLogger()
        broker = ToolBroker(
            build_clean_registry(root / "environment", fault_plan=truth.fault_plan), logger
        )
        references = ToolBroker(build_clean_registry(root / "environment"), TraceLogger())
        calls: list[tuple[str, dict[str, Any], ToolResult]] = []
        for index, name in enumerate(sequence, 1):
            if not queues[name]:
                return {
                    "task_id": task.task_id,
                    "valid": False,
                    "failures": ["alternative lacks argument fixture"],
                }
            step = queues[name].pop(0)
            result = broker.execute(
                name, dict(step.arguments), run_id="qa_oracle", task_id=task.task_id, step=index
            )
            calls.append((name, dict(step.arguments), result))
        outcome = score_observation(truth, oracle_answer(truth), calls, references)
        alternatives.append({"sequence": sequence, **outcome, "trace_events": len(logger.events)})
        # Check the expected answer against observed tool content, not against
        # the generated final-answer fixture itself.
        if truth.expected_outcome != "clarification":
            content: object = (
                [result.content for _, _, result in calls if result.ok]
                if calls
                else task.instruction
            )
            grounded = grounded and all(
                fact_in_content(content, fact) for fact in truth.required_answer_facts
            )
    category = task.category
    tools = set(truth.required_tools)
    category_valid = (
        (category == "single_source" and len(truth.required_evidence) == 1)
        or (category == "parameter_extraction" and tools in ({"calculator"}, {"db_query"}))
        or (
            category == "multi_step"
            and len(truth.oracle_steps) >= 2
            and ("calculator" in tools or bool(tools & {"send_email_mock", "post_webhook_mock"}))
        )
        or (category == "db_document" and {"doc_read", "db_query", "calculator"} <= tools)
        or (category == "ambiguous" and bool(truth.missing_slots) and not tools)
        or (category == "no_tool" and not tools and truth.expected_outcome == "answer")
        or (category == "error_recovery" and bool(truth.fault_plan))
    )
    checks = {
        "schema": True,
        "category_structure": category_valid,
        "oracle_answer_grounded": grounded,
        "all_annotated_paths_execute": all(row["success"] for row in alternatives),
        "minimum_steps": all(
            len(seq) >= truth.minimum_required_steps for seq in truth.acceptable_sequences
        ),
        "tool_arguments_annotated": not tools
        or tools <= {v.tool for v in truth.argument_validators},
        "answer_facts_present": bool(truth.required_answer_facts),
    }
    return {
        "task_id": task.task_id,
        "valid": all(checks.values()),
        "checks": checks,
        "paths": alternatives,
        "evaluator": EVALUATOR_VERSION,
        "task_sha256": hashlib.sha256(task.model_dump_json().encode()).hexdigest(),
        "ground_truth_sha256": hashlib.sha256(truth.model_dump_json().encode()).hexdigest(),
        "qualitative_review": "waived_by_owner_not_claimed",
    }


def validate_pool(root: Path) -> dict[str, Any]:
    tasks, truth = load_pool(root)
    failures = validate_environment(root)
    expected_ids = [f"clean_{index:04d}" for index in range(1, 251)]
    if [task.task_id for task in tasks] != expected_ids or [
        item.task_id for item in truth
    ] != expected_ids:
        failures.append("public/private pool must join the ordered 250 IDs one-to-one")
    if Counter(task.category for task in tasks) != Counter(CATEGORY_QUOTAS):
        failures.append("category quotas")
    groups = {task.task_id: task.instance_group_id for task in tasks}
    for ids in semantic_instance_groups(truth):
        if len({groups[task_id] for task_id in ids}) != 1:
            failures.append("same semantic instance has different groups")
    for accent_mode in (False, True):
        if _duplicate_groups(tasks, strip_accents=accent_mode):
            failures.append(f"duplicate text: accent_insensitive={accent_mode}")
    rows = [oracle_check(task, item, root) for task, item in zip(tasks, truth, strict=True)]
    failures.extend(f"task QA failed: {row['task_id']}" for row in rows if not row["valid"])
    coverage: Counter[str] = Counter(tool for item in truth for tool in set(item.required_tools))
    for name, minimum in MINIMUM_TOOL_COVERAGE.items():
        if coverage[name] < minimum:
            failures.append(f"tool coverage: {name}")
    return {
        "valid": not failures,
        "failures": failures,
        "tasks": len(tasks),
        "oracle_valid": sum(row["valid"] for row in rows),
        "tool_coverage": dict(coverage),
        "qa_records": rows,
        "qualitative_review": "waived; automated structural/behavioral checks only",
    }


def calls_from_trace(events: list[TraceEvent]) -> list[tuple[str, dict[str, Any], ToolResult]]:
    proposals: dict[str, dict[str, Any]] = {}
    calls: list[tuple[str, dict[str, Any], ToolResult]] = []
    for event in events:
        if event.event == "tool_call_proposed" and event.call_id is not None:
            if event.call_id in proposals:
                raise ValueError("duplicate tool call ID")
            proposals[event.call_id] = event.data
        if event.event == "tool_result":
            if event.call_id is None or event.call_id not in proposals:
                raise ValueError("tool result without proposal")
            proposal = proposals.pop(event.call_id)
            result = ToolResult.model_validate(event.data)
            if result.call_id != event.call_id or result.tool_name != proposal["name"]:
                raise ValueError("tool result identity mismatch")
            calls.append((proposal["name"], proposal["arguments"], result))
    if proposals:
        raise ValueError("missing tool result")
    return calls
