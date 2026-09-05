"""Deterministic acceptance checks for the unsplit clean benchmark pool."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.schemas.clean_task import (
    CleanGroundTruth,
    CleanPublicTask,
    CleanReviewRecord,
)
from react_agent.tools.factory import build_clean_registry

ROOT = Path(__file__).resolve().parents[3]
CLEAN_ROOT = ROOT / "data" / "clean" / "v1"
CATEGORY_QUOTAS = {
    "single_source": 40,
    "parameter_extraction": 40,
    "multi_step": 50,
    "db_document": 40,
    "ambiguous": 25,
    "error_recovery": 30,
    "no_tool": 25,
}
MINIMUM_TOOL_COVERAGE = {
    "doc_search": 50,
    "doc_read": 50,
    "db_query": 50,
    "cached_search": 20,
    "cached_fetch": 20,
    "calculator": 20,
    "send_email_mock": 8,
    "post_webhook_mock": 8,
}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _normalize(text: str, *, strip_accents: bool = False) -> str:
    normalized = unicodedata.normalize("NFD", text.casefold())
    if strip_accents:
        normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return " ".join(re.findall(r"\w+", normalized, flags=re.UNICODE))


def _duplicate_groups(tasks: list[CleanPublicTask], *, strip_accents: bool) -> list[list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        groups[_normalize(task.instruction, strip_accents=strip_accents)].append(task.task_id)
    return [task_ids for task_ids in groups.values() if len(task_ids) > 1]


def _near_duplicate_rows(tasks: list[CleanPublicTask]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    normalized = [(task, _normalize(task.instruction, strip_accents=True)) for task in tasks]
    for left_index, (left, left_text) in enumerate(normalized):
        left_tokens = set(left_text.split())
        for right, right_text in normalized[left_index + 1 :]:
            if left.category != right.category:
                continue
            right_tokens = set(right_text.split())
            union = left_tokens | right_tokens
            jaccard = len(left_tokens & right_tokens) / len(union) if union else 1.0
            sequence_ratio = SequenceMatcher(None, left_text, right_text, autojunk=False).ratio()
            # Phase 2 specifies a CPU fuzzy queue at similarity >= 0.90. Token
            # Jaccard is the selected metric; sequence ratio is report-only context.
            if jaccard < 0.90:
                continue
            rows.append(
                {
                    "left_task_id": left.task_id,
                    "right_task_id": right.task_id,
                    "category": left.category,
                    "token_jaccard": f"{jaccard:.6f}",
                    "sequence_ratio": f"{sequence_ratio:.6f}",
                    "disposition": "pending_semantic_check",
                }
            )
    return rows


def _contains_fact(haystack: str, value: object) -> bool:
    if isinstance(value, list):
        return all(_contains_fact(haystack, item) for item in value)
    if isinstance(value, bool):
        return str(value).casefold() in haystack.casefold()
    expected = _normalize(str(value), strip_accents=True)
    return expected in _normalize(haystack, strip_accents=True)


def _validate_oracle(
    task: CleanPublicTask,
    ground_truth: CleanGroundTruth,
    environment_root: Path,
) -> tuple[list[str], list[str], int]:
    failures: list[str] = []
    used_tools: list[str] = []
    if not ground_truth.required_tools:
        if ground_truth.oracle_steps:
            failures.append("no-tool/clarification task has oracle tool steps")
        if ground_truth.expected_outcome == "answer":
            for fact in ground_truth.required_answer_facts:
                if not _contains_fact(task.instruction, fact.value):
                    failures.append(f"instruction does not contain no-tool fact {fact.fact_id}")
        return failures, used_tools, 0

    registry = build_clean_registry(environment_root, fault_plan=ground_truth.fault_plan)
    logger = TraceLogger()
    broker = ToolBroker(registry, logger)
    successful_content: list[object] = []
    observed_injected_errors = 0
    successful_after_error = False
    for step_number, oracle_step in enumerate(ground_truth.oracle_steps, 1):
        result = broker.execute(
            oracle_step.tool,
            dict(oracle_step.arguments),
            run_id=f"oracle_{task.task_id}",
            task_id=task.task_id,
            step=step_number,
        )
        used_tools.append(oracle_step.tool)
        if result.ok:
            successful_content.append(result.content)
            if observed_injected_errors:
                successful_after_error = True
        elif result.metadata.get("injected") is True:
            observed_injected_errors += 1
        else:
            error_code = result.error.code if result.error is not None else "UNKNOWN"
            failures.append(f"oracle tool {oracle_step.tool} failed with {error_code}")

    successful_haystack = json.dumps(successful_content, ensure_ascii=False, sort_keys=True)
    for fact in ground_truth.required_answer_facts:
        if not _contains_fact(successful_haystack, fact.value):
            failures.append(f"oracle outputs do not contain fact {fact.fact_id}={fact.value!r}")
    if ground_truth.fault_plan:
        if observed_injected_errors != len(ground_truth.fault_plan):
            failures.append("oracle did not observe every deterministic injected fault")
        if not successful_after_error:
            failures.append("oracle did not recover with a successful call after the fault")
    expected_sequence = [step.tool for step in ground_truth.oracle_steps]
    if expected_sequence not in ground_truth.acceptable_sequences:
        failures.append("oracle sequence is absent from acceptable_sequences")
    if len(expected_sequence) < ground_truth.minimum_required_steps:
        failures.append("oracle is shorter than minimum_required_steps")

    trace_events = logger.events
    expected_trace_events = len(ground_truth.oracle_steps) * 3
    if len(trace_events) != expected_trace_events:
        failures.append(
            f"broker trace has {len(trace_events)} events; expected {expected_trace_events}"
        )
    return failures, used_tools, len(trace_events)


def validate_clean_pool(clean_root: Path = CLEAN_ROOT) -> dict[str, Any]:
    """Validate schemas, joins, quotas, reviews, duplicates, and executable oracles."""

    failures: list[str] = []
    public_path = clean_root / "pool" / "tasks.jsonl"
    private_path = clean_root / "private" / "pool_ground_truth.jsonl"
    review_path = clean_root / "reviews" / "review_log.jsonl"
    for path in (public_path, private_path, review_path):
        if not path.is_file():
            return {"valid": False, "failures": [f"missing file: {path}"]}
    raw_tasks = _load_jsonl(public_path)
    raw_ground_truth = _load_jsonl(private_path)
    raw_reviews = _load_jsonl(review_path)
    try:
        tasks = [CleanPublicTask.model_validate(record) for record in raw_tasks]
        ground_truth = [CleanGroundTruth.model_validate(record) for record in raw_ground_truth]
        reviews = [CleanReviewRecord.model_validate(record) for record in raw_reviews]
    except ValidationError as error:
        return {"valid": False, "failures": [f"schema validation failed: {error}"]}

    expected_ids = [f"clean_{index:04d}" for index in range(1, 251)]
    task_ids = [task.task_id for task in tasks]
    ground_truth_ids = [item.task_id for item in ground_truth]
    review_ids = [item.task_id for item in reviews]
    if task_ids != expected_ids:
        failures.append("public task IDs are not the exact clean_0001..clean_0250 sequence")
    if set(task_ids) != set(ground_truth_ids) or len(ground_truth_ids) != 250:
        failures.append("private ground truth does not join one-to-one with public tasks")
    if set(task_ids) != set(review_ids) or len(review_ids) != 250:
        failures.append("review log does not join one-to-one with public tasks")
    if any(task.split != "pool" for task in tasks):
        failures.append("unsplit pool contains a Dev/Test assignment")

    category_counts = Counter(task.category for task in tasks)
    if category_counts != Counter(CATEGORY_QUOTAS):
        failures.append(f"category quota mismatch: {dict(category_counts)}")
    owner_counts = Counter(task.authoring.assigned_owner for task in tasks)
    if owner_counts != Counter({"huy": 125, "minh": 125}):
        failures.append(f"owner allocation mismatch: {dict(owner_counts)}")
    if len({task.instance_group_id for task in tasks}) != 250:
        failures.append("instance_group_id values are not unique in the authored pool")
    if any(task.prompt_payload().keys() != {"task_id", "instruction"} for task in tasks):
        failures.append("model-visible prompt payload contains metadata or ground truth")

    review_by_id = {review.task_id: review for review in reviews}
    for task in tasks:
        review = review_by_id.get(task.task_id)
        if review is None:
            continue
        checks = review.checks.model_dump()
        if review.decision != "approved" or not all(checks.values()):
            failures.append(f"task {task.task_id} lacks complete owner acceptance")
        if review.review_mode != "automated_owner_accepted":
            failures.append(f"task {task.task_id} has an unauthorized review mode")

    exact_duplicates = _duplicate_groups(tasks, strip_accents=False)
    accent_duplicates = _duplicate_groups(tasks, strip_accents=True)
    if exact_duplicates:
        failures.append(f"exact normalized duplicate groups: {exact_duplicates}")
    if accent_duplicates:
        failures.append(f"accent-insensitive duplicate groups: {accent_duplicates}")
    near_duplicates = _near_duplicate_rows(tasks)

    ground_truth_by_id = {item.task_id: item for item in ground_truth}
    semantic_signatures = {
        task_id: json.dumps(
            {
                "facts": [fact.model_dump(mode="json") for fact in item.required_answer_facts],
                "retrieval_targets": item.retrieval_targets,
                "evidence": [entry.model_dump(mode="json") for entry in item.required_evidence],
                "missing_slots": item.missing_slots,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        for task_id, item in ground_truth_by_id.items()
    }
    for row in near_duplicates:
        left_signature = semantic_signatures[row["left_task_id"]]
        right_signature = semantic_signatures[row["right_task_id"]]
        if left_signature == right_signature:
            row["disposition"] = "rejected_semantic_duplicate"
            failures.append(
                f"semantic duplicate pair: {row['left_task_id']} and {row['right_task_id']}"
            )
        else:
            row["disposition"] = "accepted_distinct_synthetic_instance"

    oracle_rows: list[dict[str, Any]] = []
    tool_call_counts: Counter[str] = Counter()
    tool_task_counts: Counter[str] = Counter()
    total_trace_events = 0
    environment_root = clean_root / "environment"
    for task in tasks:
        item = ground_truth_by_id.get(task.task_id)
        if item is None:
            continue
        task_failures, used_tools, trace_events = _validate_oracle(task, item, environment_root)
        tool_call_counts.update(used_tools)
        tool_task_counts.update(set(used_tools))
        total_trace_events += trace_events
        oracle_rows.append(
            {
                "task_id": task.task_id,
                "valid": not task_failures,
                "failures": task_failures,
                "oracle_steps": len(item.oracle_steps),
                "trace_events": trace_events,
            }
        )
        failures.extend(f"{task.task_id}: {failure}" for failure in task_failures)

    for tool, minimum in MINIMUM_TOOL_COVERAGE.items():
        if tool_task_counts[tool] < minimum:
            failures.append(
                f"tool coverage for {tool} is {tool_task_counts[tool]}; expected at least {minimum}"
            )

    review_coverage = sum(
        review.decision == "approved" and all(review.checks.model_dump().values())
        for review in reviews
    )
    return {
        "valid": not failures,
        "failures": failures,
        "total_tasks": len(tasks),
        "category_counts": dict(sorted(category_counts.items())),
        "owner_counts": dict(sorted(owner_counts.items())),
        "schema_valid": len(tasks),
        "ground_truth_records": len(ground_truth),
        "review_coverage": review_coverage,
        "exact_duplicate_groups": exact_duplicates,
        "accent_duplicate_groups": accent_duplicates,
        "near_duplicates": near_duplicates,
        "oracle_valid": sum(row["valid"] for row in oracle_rows),
        "oracle_rows": oracle_rows,
        "tool_task_counts": dict(sorted(tool_task_counts.items())),
        "tool_call_counts": dict(sorted(tool_call_counts.items())),
        "oracle_trace_events": total_trace_events,
        "pool_hashes": {
            "public": hashlib.sha256(public_path.read_bytes()).hexdigest(),
            "private": hashlib.sha256(private_path.read_bytes()).hexdigest(),
            "reviews": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        },
    }


def write_clean_pool_reports(result: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    summary = {
        key: value for key, value in result.items() if key not in {"oracle_rows", "near_duplicates"}
    }
    (report_root / "validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (report_root / "oracle_validation.json").write_text(
        json.dumps(result["oracle_rows"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (report_root / "category_distribution.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        category_writer = csv.writer(stream)
        category_writer.writerow(["category", "count"])
        category_writer.writerows(result["category_counts"].items())
    with (report_root / "tool_coverage.csv").open("w", encoding="utf-8", newline="") as stream:
        tool_writer = csv.writer(stream)
        tool_writer.writerow(["tool", "task_coverage", "oracle_calls"])
        for tool in sorted(result["tool_task_counts"]):
            tool_writer.writerow(
                [
                    tool,
                    result["tool_task_counts"][tool],
                    result["tool_call_counts"][tool],
                ]
            )
    with (report_root / "duplicate_report.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = [
            "left_task_id",
            "right_task_id",
            "category",
            "token_jaccard",
            "sequence_ratio",
            "disposition",
        ]
        duplicate_writer = csv.DictWriter(stream, fieldnames=fields)
        duplicate_writer.writeheader()
        duplicate_writer.writerows(result["near_duplicates"])
    review_summary = {
        "mode": "automated_owner_accepted",
        "independent_human_review": False,
        "approved": result["review_coverage"],
        "total": result["total_tasks"],
    }
    (report_root / "review_summary.json").write_text(
        json.dumps(review_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
