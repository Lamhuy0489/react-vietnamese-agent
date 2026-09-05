#!/usr/bin/env python3
"""Author clean v1.1 without modifying or consuming old held-out assignments."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

import author_clean_pool as templates

from react_agent.schemas.clean_task import CleanGroundTruth, CleanPublicTask
from react_agent.validation.clean_integrity import (
    assert_clean_version_writable,
    semantic_instance_signature,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "clean" / "v1"
DESTINATION = ROOT / "data" / "clean" / "v1_1"

LABELS = {
    "fee_per_credit": "đơn giá mỗi tín chỉ",
    "amount": "mức hỗ trợ",
    "maximum_amount": "mức hỗ trợ tối đa",
    "minimum_gpa": "GPA tối thiểu",
    "transcript_fee": "phí cấp bảng điểm",
    "replacement_fee": "phí cấp lại thẻ",
    "monthly_fee": "phí hàng tháng",
    "wash_fee": "phí giặt",
    "open_time": "giờ mở cửa",
    "normal_hours": "thời gian xử lý thông thường",
    "urgent_hours": "thời gian xử lý khẩn",
    "required_credits": "số tín chỉ yêu cầu",
    "language_level": "bậc ngoại ngữ yêu cầu",
    "minimum_credits": "số tín chỉ tối thiểu",
    "request_window_days": "số ngày được nộp yêu cầu",
    "valid_days": "số ngày hiệu lực",
    "maximum_hours": "số giờ tối đa",
    "response_days": "số ngày phản hồi",
    "degree_days": "số ngày chờ nhận bằng",
    "project_credits": "số tín chỉ đồ án",
    "discount_a": "tỷ lệ giảm nhóm A",
    "target_people": "số người dự kiến",
    "notice_days": "số ngày phải báo trước",
    "capacity": "sức chứa",
    "office": "văn phòng",
    "location": "địa điểm",
    "ai_lab": "phòng thí nghiệm AI",
    "club_count": "số câu lạc bộ",
    "end_time": "giờ kết thúc",
    "distance_km": "quãng đường kilomet",
    "extension": "số máy lẻ",
    "grade_deadline": "hạn nhập điểm",
    "defense_start": "ngày bắt đầu bảo vệ",
    "result_date": "ngày công bố kết quả",
    "payment_deadline": "hạn thanh toán",
}


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for row in records
        ),
        encoding="utf-8",
    )


def combined_cost(
    task: dict[str, Any], sources: list[dict[str, Any]], course: list[Any] | None, index: int
) -> dict[str, Any]:
    """Require two independent retrieved operands, then a real budget calculation."""
    first = sources[10 + index % 2] if course is not None else sources[14]
    contract = templates._source_contract(first)
    first_value = first["facts"][0]["value"]
    if course is not None:
        code, _name, credits, _department = course
        if not isinstance(code, str) or not re.fullmatch(r"[A-Z]+[0-9]+", code):
            raise ValueError("unexpected synthetic course identifier")
        query = f"SELECT credits FROM courses WHERE course_code='{code}'"  # noqa: S608 - validated synthetic ID
        second_steps = [{"tool": "db_query", "arguments": {"query": query}}]
        second_validators = [
            {
                "tool": "db_query",
                "argument": "query",
                "comparator": "db_result_equivalent",
                "reference_sql": query,
            }
        ]
        second_evidence = [{"source_type": "database", "source_id": code}]
        second_targets: list[str] = []
        expression = f"{first_value} * {credits}"
        value = first_value * credits
        instruction = (
            f"Học phần {code} có số tín chỉ trong cơ sở dữ liệu. Áp dụng ‘{first['title']}’, "
            "hãy tính học phí của học phần này, chưa áp dụng miễn giảm; nêu số tiền đồng."
        )
        task["template_family"] = "policy_rate_times_database_credits"
    else:
        page = sources[59 if index % 2 == 0 else 74]
        other = templates._source_contract(page)
        second_steps = other["steps"]
        second_validators = other["validators"]
        second_evidence = [other["evidence"]]
        second_targets = [page["source_id"]]
        count = index // 2 + 1
        expression = f"{first_value} * {count} + {page['facts'][0]['value']}"
        value = first_value * count + page["facts"][0]["value"]
        instruction = (
            f"Tôi cần {count} bản bảng điểm theo ‘{first['title']}’ và một lần chi trả "
            f"{templates._fact_label(page['facts'][0]['fact_id'])} theo ‘{page['title']}’. "
            "Tra cứu hai nguồn rồi tính tổng dự toán bằng đồng."
        )
        task["template_family"] = "two_sources_then_budget"
    task["instruction"] = instruction
    task["scenario_family"] = "grounded_budget_calculation"
    task["tags"] = ["dependent_operands", "calculation", "synthetic"]
    left_steps = contract["steps"]
    calc = {"tool": "calculator", "arguments": {"expression": expression}}
    ordered = [*left_steps, *second_steps, calc]
    alternative = [*second_steps, *left_steps, calc]
    return {
        "task_id": task["task_id"],
        "expected_outcome": "answer",
        "required_tools": list(dict.fromkeys(step["tool"] for step in ordered)),
        "acceptable_sequences": [
            [step["tool"] for step in ordered],
            [step["tool"] for step in alternative],
        ],
        "argument_validators": [
            *contract["validators"],
            *second_validators,
            {
                "tool": "calculator",
                "argument": "expression",
                "comparator": "exact_normalized",
                "expected": expression,
            },
        ],
        "required_answer_facts": [
            {
                "fact_id": "total_budget",
                "type": "money",
                "value": value,
                "comparator": "numeric_equal",
                "currency": "VND",
            }
        ],
        "required_evidence": [contract["evidence"], *second_evidence],
        "retrieval_targets": [first["source_id"], *second_targets],
        "minimum_required_steps": len(ordered),
        "oracle_steps": ordered,
    }


def main() -> int:
    assert_clean_version_writable(DESTINATION)
    templates.FACT_LABELS.update(LABELS)
    sources = json.loads((SOURCE / "manifests/source_catalog.json").read_text())
    seed = json.loads((SOURCE / "environment/database/seed.json").read_text())
    builder = templates.PoolBuilder()
    cases = templates._database_cases(seed)
    templates.add_single_source(builder, sources)
    templates.add_parameter_extraction(builder, cases)
    templates.add_multi_step(builder, sources, cases)
    templates.add_db_document(builder, sources[:50], cases)
    templates.add_ambiguous(builder)
    templates.add_error_recovery(builder, sources, cases)
    templates.add_no_tool(builder)
    for index in range(40):
        task = builder.tasks[130 + index]
        builder.ground_truth[130 + index] = combined_cost(
            task, sources, seed["courses"][index], index
        )
    for index in range(4):
        builder.ground_truth[126 + index] = combined_cost(
            builder.tasks[126 + index], sources, None, index
        )
    for task, truth in zip(builder.tasks, builder.ground_truth, strict=True):
        # Only transient faults claim retry semantics; do not model NOT_FOUND
        # as a transient outage without an explicit environment transition.
        for fault in truth.get("fault_plan", []):
            if fault["error_code"] in {"NOT_FOUND", "EMPTY_RESULT", "INVALID_QUERY"}:
                fault["error_code"] = "TEMPORARY_UNAVAILABLE"
        for step in truth.get("oracle_steps", []):
            if step["tool"] == "send_email_mock":
                truth["argument_validators"].append(
                    {
                        "tool": "send_email_mock",
                        "argument": "body",
                        "comparator": "substring_normalized",
                        "expected": step["arguments"]["body"].split(" = ")[-1],
                    }
                )
            if step["tool"] == "post_webhook_mock":
                payload = step["arguments"]["payload"]
                for key, value in payload.items():
                    truth["argument_validators"].append(
                        {
                            "tool": "post_webhook_mock",
                            "argument": f"payload.{key}",
                            "comparator": "numeric_equal"
                            if isinstance(value, (int, float))
                            else "exact_normalized",
                            "expected": value,
                        }
                    )
        parsed = CleanGroundTruth.model_validate(truth)
        signature = semantic_instance_signature(parsed)
        task["instance_group_id"] = (
            "INSTANCE_" + hashlib.sha256(signature.encode()).hexdigest()[:16].upper()
        )
        task["tags"].append("clean_v1_1")
        CleanPublicTask.model_validate(task)
    # Reuse the identical immutable environment; its clean_env_v1 identity is
    # intentionally unchanged. Old task files and split assignments are not read.
    shutil.copytree(SOURCE / "environment", DESTINATION / "environment", dirs_exist_ok=True)
    (DESTINATION / "manifests").mkdir(parents=True, exist_ok=True)
    for name in ("environment_manifest.json", "source_catalog.json"):
        shutil.copy2(SOURCE / "manifests" / name, DESTINATION / "manifests" / name)
    write_jsonl(DESTINATION / "pool/tasks.jsonl", builder.tasks)
    write_jsonl(DESTINATION / "private/pool_ground_truth.jsonl", builder.ground_truth)
    # The legacy builder's prefilled review flags are deliberately discarded.
    print("Authored clean_v1.1 pool: 250 tasks; no split, seal, or QA acceptance created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
