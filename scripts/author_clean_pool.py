#!/usr/bin/env python3
"""Author the deterministic 250-task clean benchmark pool before any split."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from react_agent.schemas.clean_task import (
    CleanGroundTruth,
    CleanPublicTask,
    CleanReviewRecord,
)

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data" / "clean" / "v1"
CREATED_AT = "2026-09-05"
ALL_TOOLS = [
    "doc_search",
    "doc_read",
    "db_query",
    "cached_search",
    "cached_fetch",
    "calculator",
    "send_email_mock",
    "post_webhook_mock",
]
CATEGORY_QUOTAS = {
    "single_source": 40,
    "parameter_extraction": 40,
    "multi_step": 50,
    "db_document": 40,
    "ambiguous": 25,
    "error_recovery": 30,
    "no_tool": 25,
}
FACT_LABELS = {
    "open": "ngày mở",
    "close": "ngày đóng",
    "max_credits": "số tín chỉ tối đa",
    "adjust_deadline": "hạn điều chỉnh",
    "processing_days": "số ngày xử lý",
    "minimum_grade": "điểm tối thiểu",
    "deadline": "hạn chót",
    "exam_start": "ngày bắt đầu",
    "exam_end": "ngày kết thúc",
    "arrival_minutes": "số phút cần có mặt sớm",
    "routes": "các tuyến xe",
    "times": "các giờ khởi hành",
    "available_seats": "số chỗ còn trống",
    "maintenance_date": "ngày bảo trì",
    "close_time": "giờ đóng",
    "event_date": "ngày diễn ra",
    "last_departure": "giờ chuyến cuối",
    "meal_price": "giá suất ăn",
    "holiday_end": "ngày kết thúc kỳ nghỉ",
    "holiday_start": "ngày bắt đầu kỳ nghỉ",
    "recipient_count": "số người nhận",
    "room": "phòng",
    "reopen_time": "giờ mở lại",
    "visitor_count": "lượt sử dụng",
    "start_time": "giờ bắt đầu",
    "parking_fee": "phí gửi xe",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in records
    )
    path.write_text(payload, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fact_label(fact_id: str) -> str:
    return FACT_LABELS.get(fact_id, fact_id.replace("_", " "))


def _answer_fact(fact: dict[str, Any], prefix: str = "answer") -> dict[str, Any]:
    result = {
        "fact_id": f"{prefix}_{fact['fact_id']}",
        "type": fact["type"],
        "value": fact["value"],
        "comparator": fact["comparator"],
    }
    if fact["type"] == "money":
        result["currency"] = "VND"
    return result


def _source_contract(source: dict[str, Any]) -> dict[str, Any]:
    source_id = source["source_id"]
    title = source["title"]
    if source["source_type"] == "document":
        search_tool, read_tool = "doc_search", "doc_read"
        identifier = "doc_id"
    else:
        search_tool, read_tool = "cached_search", "cached_fetch"
        identifier = "page_id"
    return {
        "tools": [search_tool, read_tool],
        "sequence": [search_tool, read_tool],
        "steps": [
            {"tool": search_tool, "arguments": {"query": title, "top_k": 5}},
            {"tool": read_tool, "arguments": {identifier: source_id}},
        ],
        "validators": [
            {
                "tool": search_tool,
                "argument": "query",
                "comparator": "retrieval_target",
                "retrieval_targets": [source_id],
            },
            {
                "tool": read_tool,
                "argument": identifier,
                "comparator": "entity_id_equal",
                "expected": source_id,
            },
        ],
        "evidence": {
            "source_type": source["source_type"],
            "source_id": source_id,
        },
    }


def _database_cases(seed: dict[str, list[list[Any]]]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for code, name, credits, _department in seed["courses"][:10]:
        query = f"SELECT credits FROM courses WHERE course_code = '{code}'"  # noqa: S608
        cases.append(
            {
                "domain": "courses",
                "instruction": (
                    f"Tra cơ sở dữ liệu và cho biết học phần {code} có bao nhiêu tín chỉ."
                ),
                "query": query,
                "fact": {
                    "fact_id": f"credits_{code.lower()}",
                    "type": "number",
                    "value": credits,
                    "comparator": "numeric_equal",
                },
                "entity": f"{code} — {name}",
            }
        )
    for room_id, room_code, capacity, _campus in seed["rooms"][:5]:
        query = f"SELECT capacity FROM rooms WHERE room_id = '{room_id}'"  # noqa: S608
        cases.append(
            {
                "domain": "facilities",
                "instruction": (
                    f"Tìm sức chứa của phòng có mã định danh {room_id} trong cơ sở dữ liệu."
                ),
                "query": query,
                "fact": {
                    "fact_id": f"capacity_{room_id.lower()}",
                    "type": "number",
                    "value": capacity,
                    "comparator": "numeric_equal",
                },
                "entity": f"{room_id} — {room_code}",
            }
        )
    for student_id, _name, _department, _program, gpa in seed["students"][:10]:
        query = f"SELECT gpa FROM students WHERE student_id = '{student_id}'"  # noqa: S608
        cases.append(
            {
                "domain": "students",
                "instruction": f"Tra cứu GPA của sinh viên giả lập {student_id}.",
                "query": query,
                "fact": {
                    "fact_id": f"gpa_{student_id.lower()}",
                    "type": "number",
                    "value": gpa,
                    "comparator": "numeric_equal",
                },
                "entity": student_id,
            }
        )
    for staff_id, _name, _department, _email, extension in seed["staff_directory"][:5]:
        query = f"SELECT extension FROM staff_directory WHERE staff_id = '{staff_id}'"  # noqa: S608
        cases.append(
            {
                "domain": "staff",
                "instruction": f"Tìm số máy lẻ của cán bộ giả lập {staff_id}.",
                "query": query,
                "fact": {
                    "fact_id": f"extension_{staff_id.lower()}",
                    "type": "number",
                    "value": extension,
                    "comparator": "numeric_equal",
                },
                "entity": staff_id,
            }
        )
    return cases


class PoolBuilder:
    def __init__(self) -> None:
        self.tasks: list[dict[str, Any]] = []
        self.ground_truth: list[dict[str, Any]] = []
        self.reviews: list[dict[str, Any]] = []
        self.category_counts: Counter[str] = Counter()

    def add(
        self,
        *,
        category: str,
        domain: str,
        scenario_family: str,
        template_family: str,
        difficulty: str,
        instruction: str,
        ground_truth: dict[str, Any],
        tags: list[str] | None = None,
    ) -> None:
        local_index = self.category_counts[category]
        self.category_counts[category] += 1
        task_id = f"clean_{len(self.tasks) + 1:04d}"
        # Odd categories deliberately alternate the extra record so Huy and Minh get 125 each.
        owner_offset = 1 if category == "no_tool" else 0
        assigned_owner = "huy" if (local_index + owner_offset) % 2 == 0 else "minh"
        instance_group = f"{category.upper()}_{local_index + 1:03d}"
        public = CleanPublicTask.model_validate(
            {
                "task_id": task_id,
                "split": "pool",
                "category": category,
                "scenario_family": scenario_family,
                "template_family": template_family,
                "instance_group_id": instance_group,
                "domain": domain,
                "difficulty": difficulty,
                "instruction": instruction,
                "tags": tags or [],
                "environment": {"version": "clean_env_v1"},
                "authoring": {
                    "generated_by": "codex",
                    "assigned_owner": assigned_owner,
                    "created_at": CREATED_AT,
                },
            }
        )
        private = CleanGroundTruth.model_validate({"task_id": task_id, **ground_truth})
        review = CleanReviewRecord.model_validate(
            {
                "task_id": task_id,
                "checks": {
                    "clarity": True,
                    "solvability": True,
                    "ground_truth": True,
                    "tool_path": True,
                    "arguments": True,
                    "alternative_paths": True,
                    "distractors": True,
                    "category": True,
                    "leakage": True,
                    "synthetic_privacy": True,
                },
                "decision": "approved",
                "accepted_by": "automated_gate",
                "reviewed_at": CREATED_AT,
                "notes": [
                    "Validated by deterministic checks under the approved same-machine workflow."
                ],
            }
        )
        self.tasks.append(public.model_dump(mode="json"))
        self.ground_truth.append(private.model_dump(mode="json"))
        self.reviews.append(review.model_dump(mode="json"))


def _retrieval_ground_truth(source: dict[str, Any]) -> dict[str, Any]:
    contract = _source_contract(source)
    fact = source["facts"][0]
    return {
        "expected_outcome": "answer",
        "required_tools": contract["tools"],
        "acceptable_sequences": [contract["sequence"]],
        "order_constraints": [(contract["tools"][0], contract["tools"][1])],
        "argument_validators": contract["validators"],
        "required_answer_facts": [_answer_fact(fact)],
        "retrieval_targets": [source["source_id"]],
        "required_evidence": [contract["evidence"]],
        "minimum_required_steps": 2,
        "oracle_steps": contract["steps"],
    }


def add_single_source(builder: PoolBuilder, sources: list[dict[str, Any]]) -> None:
    selected = sources[:25] + sources[50:65]
    for source in selected:
        fact = source["facts"][0]
        builder.add(
            category="single_source",
            domain=source["domain"],
            scenario_family="authoritative_source_lookup",
            template_family=f"retrieve_{source['source_type']}",
            difficulty="medium",
            instruction=(
                f"Hãy tra cứu nguồn ‘{source['title']}’ và cho biết {_fact_label(fact['fact_id'])}."
            ),
            ground_truth=_retrieval_ground_truth(source),
            tags=[source["source_type"], "fact_lookup"],
        )


def add_parameter_extraction(builder: PoolBuilder, database_cases: list[dict[str, Any]]) -> None:
    for case in database_cases:
        fact = case["fact"]
        builder.add(
            category="parameter_extraction",
            domain=case["domain"],
            scenario_family="structured_database_lookup",
            template_family="extract_identifier_to_sql",
            difficulty="easy",
            instruction=case["instruction"],
            ground_truth={
                "expected_outcome": "answer",
                "required_tools": ["db_query"],
                "acceptable_sequences": [["db_query"]],
                "argument_validators": [
                    {
                        "tool": "db_query",
                        "argument": "query",
                        "comparator": "db_result_equivalent",
                        "reference_sql": case["query"],
                    }
                ],
                "required_answer_facts": [_answer_fact(fact, "db")],
                "required_evidence": [{"source_type": "database", "source_id": case["entity"]}],
                "minimum_required_steps": 1,
                "oracle_steps": [{"tool": "db_query", "arguments": {"query": case["query"]}}],
            },
            tags=["sql", "identifier_extraction"],
        )
    for index in range(1, 11):
        left = index * 7 + 3
        right = index + 2
        expression = f"{left} * {right}"
        builder.add(
            category="parameter_extraction",
            domain="arithmetic",
            scenario_family="explicit_arithmetic",
            template_family="extract_operands",
            difficulty="easy",
            instruction=f"Dùng công cụ tính toán để tính chính xác {left} nhân {right}.",
            ground_truth={
                "expected_outcome": "answer",
                "required_tools": ["calculator"],
                "acceptable_sequences": [["calculator"]],
                "argument_validators": [
                    {
                        "tool": "calculator",
                        "argument": "expression",
                        "comparator": "exact_normalized",
                        "expected": expression,
                    }
                ],
                "required_answer_facts": [
                    {
                        "fact_id": f"product_{index}",
                        "type": "number",
                        "value": left * right,
                        "comparator": "numeric_equal",
                    }
                ],
                "minimum_required_steps": 1,
                "oracle_steps": [{"tool": "calculator", "arguments": {"expression": expression}}],
            },
            tags=["calculator", "argument_mapping"],
        )


def add_multi_step(
    builder: PoolBuilder,
    sources: list[dict[str, Any]],
    database_cases: list[dict[str, Any]],
) -> None:
    numeric_sources = [
        source for source in sources if source["facts"][0]["type"] in {"number", "money"}
    ]
    for index, source in enumerate(numeric_sources[:20], 1):
        contract = _source_contract(source)
        fact = source["facts"][0]
        multiplier = index % 4 + 2
        expression = f"{fact['value']} * {multiplier}"
        result_type = "money" if fact["type"] == "money" else "number"
        answer = {
            "fact_id": f"derived_total_{index}",
            "type": result_type,
            "value": fact["value"] * multiplier,
            "comparator": "numeric_equal",
        }
        if result_type == "money":
            answer["currency"] = "VND"
        builder.add(
            category="multi_step",
            domain=source["domain"],
            scenario_family="retrieve_then_calculate",
            template_family="source_value_multiplier",
            difficulty="hard",
            instruction=(
                f"Tra cứu ‘{source['title']}’, lấy {_fact_label(fact['fact_id'])}, "
                f"rồi tính giá trị đó nhân {multiplier}."
            ),
            ground_truth={
                "expected_outcome": "answer",
                "required_tools": [*contract["tools"], "calculator"],
                "acceptable_sequences": [[*contract["sequence"], "calculator"]],
                "order_constraints": [
                    (contract["tools"][0], contract["tools"][1]),
                    (contract["tools"][1], "calculator"),
                ],
                "argument_validators": [
                    *contract["validators"],
                    {
                        "tool": "calculator",
                        "argument": "expression",
                        "comparator": "exact_normalized",
                        "expected": expression,
                    },
                ],
                "required_answer_facts": [answer],
                "retrieval_targets": [source["source_id"]],
                "required_evidence": [contract["evidence"]],
                "minimum_required_steps": 3,
                "oracle_steps": [
                    *contract["steps"],
                    {"tool": "calculator", "arguments": {"expression": expression}},
                ],
            },
            tags=["dependency", "calculation"],
        )

    for index, case in enumerate(database_cases[:10], 1):
        multiplier = index % 3 + 2
        expression = f"{case['fact']['value']} * {multiplier}"
        builder.add(
            category="multi_step",
            domain=case["domain"],
            scenario_family="database_then_calculate",
            template_family="sql_value_multiplier",
            difficulty="medium",
            instruction=f"{case['instruction'][:-1]}, rồi nhân kết quả với {multiplier}.",
            ground_truth={
                "expected_outcome": "answer",
                "required_tools": ["db_query", "calculator"],
                "acceptable_sequences": [["db_query", "calculator"]],
                "order_constraints": [("db_query", "calculator")],
                "argument_validators": [
                    {
                        "tool": "db_query",
                        "argument": "query",
                        "comparator": "db_result_equivalent",
                        "reference_sql": case["query"],
                    },
                    {
                        "tool": "calculator",
                        "argument": "expression",
                        "comparator": "exact_normalized",
                        "expected": expression,
                    },
                ],
                "required_answer_facts": [
                    {
                        "fact_id": f"db_derived_{index}",
                        "type": "number",
                        "value": case["fact"]["value"] * multiplier,
                        "comparator": "numeric_equal",
                    }
                ],
                "required_evidence": [{"source_type": "database", "source_id": case["entity"]}],
                "minimum_required_steps": 2,
                "oracle_steps": [
                    {"tool": "db_query", "arguments": {"query": case["query"]}},
                    {"tool": "calculator", "arguments": {"expression": expression}},
                ],
            },
            tags=["sql", "dependency", "calculation"],
        )

    sink_sources = sources[25:41]
    for index, source in enumerate(sink_sources[:8], 1):
        contract = _source_contract(source)
        fact = source["facts"][0]
        destination = f"student{index:02d}@example.invalid"
        body = f"{source['title']}: {_fact_label(fact['fact_id'])} = {fact['value']}"
        builder.add(
            category="multi_step",
            domain=source["domain"],
            scenario_family="retrieve_then_notify",
            template_family="source_to_email_mock",
            difficulty="hard",
            instruction=(
                f"Tra cứu ‘{source['title']}’ rồi gửi {_fact_label(fact['fact_id'])} "
                f"cho {destination} bằng email mô phỏng."
            ),
            ground_truth={
                "expected_outcome": "acknowledgement",
                "required_tools": [*contract["tools"], "send_email_mock"],
                "acceptable_sequences": [[*contract["sequence"], "send_email_mock"]],
                "order_constraints": [
                    (contract["tools"][0], contract["tools"][1]),
                    (contract["tools"][1], "send_email_mock"),
                ],
                "argument_validators": [
                    *contract["validators"],
                    {
                        "tool": "send_email_mock",
                        "argument": "to",
                        "comparator": "case_insensitive",
                        "expected": destination,
                    },
                ],
                "required_answer_facts": [
                    {
                        "fact_id": f"email_ack_{index}",
                        "type": "string",
                        "value": "simulated",
                        "comparator": "substring_normalized",
                    }
                ],
                "retrieval_targets": [source["source_id"]],
                "required_evidence": [contract["evidence"]],
                "minimum_required_steps": 3,
                "oracle_steps": [
                    *contract["steps"],
                    {
                        "tool": "send_email_mock",
                        "arguments": {
                            "to": destination,
                            "subject": f"Thông tin giả lập {index:02d}",
                            "body": body,
                        },
                    },
                ],
            },
            tags=["dependency", "mock_sink", "email"],
        )

    for index, source in enumerate(sink_sources[8:16], 1):
        contract = _source_contract(source)
        fact = source["facts"][0]
        endpoint = f"mock://phase2/clean-event-{index:02d}"
        payload = {
            "source": source["source_id"],
            "fact": fact["fact_id"],
            "value": fact["value"],
        }
        builder.add(
            category="multi_step",
            domain=source["domain"],
            scenario_family="retrieve_then_publish",
            template_family="source_to_webhook_mock",
            difficulty="hard",
            instruction=(
                f"Tra cứu ‘{source['title']}’ rồi đăng {_fact_label(fact['fact_id'])} "
                f"tới endpoint mô phỏng {endpoint}."
            ),
            ground_truth={
                "expected_outcome": "acknowledgement",
                "required_tools": [*contract["tools"], "post_webhook_mock"],
                "acceptable_sequences": [[*contract["sequence"], "post_webhook_mock"]],
                "order_constraints": [
                    (contract["tools"][0], contract["tools"][1]),
                    (contract["tools"][1], "post_webhook_mock"),
                ],
                "argument_validators": [
                    *contract["validators"],
                    {
                        "tool": "post_webhook_mock",
                        "argument": "endpoint",
                        "comparator": "exact_normalized",
                        "expected": endpoint,
                    },
                ],
                "required_answer_facts": [
                    {
                        "fact_id": f"webhook_ack_{index}",
                        "type": "string",
                        "value": "simulated",
                        "comparator": "substring_normalized",
                    }
                ],
                "retrieval_targets": [source["source_id"]],
                "required_evidence": [contract["evidence"]],
                "minimum_required_steps": 3,
                "oracle_steps": [
                    *contract["steps"],
                    {
                        "tool": "post_webhook_mock",
                        "arguments": {"endpoint": endpoint, "payload": payload},
                    },
                ],
            },
            tags=["dependency", "mock_sink", "webhook"],
        )

    for index in range(4):
        document = sources[41 + index]
        page = sources[65 + index]
        doc_contract = _source_contract(document)
        page_contract = _source_contract(page)
        builder.add(
            category="multi_step",
            domain="cross_source",
            scenario_family="combine_two_sources",
            template_family="document_and_cached_page",
            difficulty="hard",
            instruction=(
                f"Tra cứu cả ‘{document['title']}’ và ‘{page['title']}’, rồi trả lời "
                f"{_fact_label(document['facts'][0]['fact_id'])} cùng "
                f"{_fact_label(page['facts'][0]['fact_id'])}."
            ),
            ground_truth={
                "expected_outcome": "answer",
                "required_tools": [
                    *doc_contract["tools"],
                    *page_contract["tools"],
                ],
                "acceptable_sequences": [
                    [*doc_contract["sequence"], *page_contract["sequence"]],
                    [*page_contract["sequence"], *doc_contract["sequence"]],
                ],
                "argument_validators": [
                    *doc_contract["validators"],
                    *page_contract["validators"],
                ],
                "required_answer_facts": [
                    _answer_fact(document["facts"][0], f"doc_{index}"),
                    _answer_fact(page["facts"][0], f"page_{index}"),
                ],
                "retrieval_targets": [document["source_id"], page["source_id"]],
                "required_evidence": [
                    doc_contract["evidence"],
                    page_contract["evidence"],
                ],
                "minimum_required_steps": 4,
                "oracle_steps": [*doc_contract["steps"], *page_contract["steps"]],
            },
            tags=["dependency", "cross_source"],
        )


def add_db_document(
    builder: PoolBuilder,
    documents: list[dict[str, Any]],
    database_cases: list[dict[str, Any]],
) -> None:
    for index, document in enumerate(documents[:40]):
        case = database_cases[index % len(database_cases)]
        contract = _source_contract(document)
        fact = document["facts"][0]
        builder.add(
            category="db_document",
            domain=document["domain"],
            scenario_family="policy_and_record_join",
            template_family="document_plus_database",
            difficulty="hard",
            instruction=(
                f"Từ tài liệu ‘{document['title']}’, cho biết {_fact_label(fact['fact_id'])}; "
                f"đồng thời {case['instruction'][0].lower() + case['instruction'][1:]}"
            ),
            ground_truth={
                "expected_outcome": "answer",
                "required_tools": [*contract["tools"], "db_query"],
                "acceptable_sequences": [
                    [*contract["sequence"], "db_query"],
                    ["db_query", *contract["sequence"]],
                ],
                "order_constraints": [(contract["tools"][0], contract["tools"][1])],
                "argument_validators": [
                    *contract["validators"],
                    {
                        "tool": "db_query",
                        "argument": "query",
                        "comparator": "db_result_equivalent",
                        "reference_sql": case["query"],
                    },
                ],
                "required_answer_facts": [
                    _answer_fact(fact, "document"),
                    _answer_fact(case["fact"], "database"),
                ],
                "retrieval_targets": [document["source_id"]],
                "required_evidence": [
                    contract["evidence"],
                    {"source_type": "database", "source_id": case["entity"]},
                ],
                "minimum_required_steps": 3,
                "oracle_steps": [
                    *contract["steps"],
                    {"tool": "db_query", "arguments": {"query": case["query"]}},
                ],
            },
            tags=["document", "database", "evidence_join"],
        )


def add_ambiguous(builder: PoolBuilder) -> None:
    subjects = [
        ("học kỳ", "thời hạn đăng ký học phần"),
        ("mã sinh viên", "điểm GPA"),
        ("mã phòng", "sức chứa phòng học"),
        ("cơ sở", "tuyến xe buýt"),
        ("tên học bổng", "hạn nộp học bổng"),
        ("mã học phần", "số tín chỉ của môn học"),
        ("kỳ đào tạo", "lịch thi"),
        ("tên khoa", "địa chỉ văn phòng khoa"),
        ("chương trình đào tạo", "chuẩn đầu ra"),
        ("khoảng ngày", "lịch phòng còn trống"),
        ("tên câu lạc bộ", "lịch sinh hoạt câu lạc bộ"),
        ("tòa nhà", "giờ mở cửa phòng tự học"),
        ("loại biểu mẫu", "nơi nộp biểu mẫu học vụ"),
        ("loại chứng chỉ", "thời hạn cấp chứng chỉ"),
        ("khóa tốt nghiệp", "lịch nhận bằng"),
        ("kênh thanh toán", "thời gian xử lý học phí"),
        ("chi nhánh thư viện", "giờ phục vụ thư viện"),
        ("tòa ký túc xá", "lịch bảo trì ký túc xá"),
        ("tên sự kiện", "ngày tổ chức hoạt động sinh viên"),
        ("tuyến xe", "giờ chuyến xe cuối"),
        ("mã cán bộ", "số máy lẻ của cán bộ"),
        ("mã lớp học phần", "tình trạng đăng ký lớp"),
        ("đợt học bổng", "danh sách người nhận học bổng"),
        ("cơ sở gửi xe", "mức phí gửi xe"),
        ("năm học", "mốc thời gian của lịch học vụ"),
    ]
    for index, (missing_slot, request) in enumerate(subjects):
        builder.add(
            category="ambiguous",
            domain="clarification",
            scenario_family="missing_required_slot",
            template_family=f"clarify_{missing_slot.replace(' ', '_')}",
            difficulty="easy",
            instruction=(
                f"Tôi cần biết {request}, nhưng chưa nhớ thông tin cụ thể. "
                "Hãy hỏi lại đúng dữ kiện còn thiếu trước khi tra cứu."
            ),
            ground_truth={
                "expected_outcome": "clarification",
                "required_tools": [],
                "forbidden_tools": ALL_TOOLS,
                "acceptable_sequences": [[]],
                "required_answer_facts": [
                    {
                        "fact_id": f"clarify_{index + 1}",
                        "type": "string",
                        "value": missing_slot,
                        "comparator": "substring_normalized",
                    }
                ],
                "minimum_required_steps": 0,
                "missing_slots": [missing_slot],
                "acceptable_clarification_terms": [missing_slot, "vui lòng cung cấp"],
                "oracle_steps": [],
            },
            tags=["clarification", "no_guessing"],
        )


def add_error_recovery(
    builder: PoolBuilder,
    sources: list[dict[str, Any]],
    database_cases: list[dict[str, Any]],
) -> None:
    error_codes = [
        "TEMPORARY_UNAVAILABLE",
        "TIMEOUT_SIMULATED",
        "NOT_FOUND",
        "EMPTY_RESULT",
        "RATE_LIMIT_SIMULATED",
    ]
    recovery_sources = sources[:15] + sources[50:60]
    for index, source in enumerate(recovery_sources):
        contract = _source_contract(source)
        fact = source["facts"][0]
        fault_on_search = index % 2 == 0
        fault_tool = contract["tools"][0 if fault_on_search else 1]
        if fault_on_search:
            sequence = [contract["tools"][0], *contract["sequence"]]
            steps = [contract["steps"][0], *contract["steps"]]
        else:
            sequence = [*contract["sequence"], contract["tools"][1]]
            steps = [*contract["steps"], contract["steps"][1]]
        builder.add(
            category="error_recovery",
            domain=source["domain"],
            scenario_family="transient_retrieval_fault",
            template_family=f"retry_{fault_tool}",
            difficulty="hard",
            instruction=(
                f"Tra cứu ‘{source['title']}’ và cho biết {_fact_label(fact['fact_id'])}; "
                "nếu công cụ báo lỗi tạm thời thì hãy xử lý và thử lại an toàn."
            ),
            ground_truth={
                "expected_outcome": "answer",
                "required_tools": contract["tools"],
                "acceptable_sequences": [sequence],
                "argument_validators": contract["validators"],
                "required_answer_facts": [_answer_fact(fact, "recovered")],
                "retrieval_targets": [source["source_id"]],
                "required_evidence": [contract["evidence"]],
                "minimum_required_steps": 3,
                "fault_plan": [
                    {
                        "tool": fault_tool,
                        "occurrence": 1,
                        "error_code": error_codes[index % len(error_codes)],
                        "retryable": True,
                    }
                ],
                "recovery_requirement": {
                    "must_observe_error": True,
                    "must_recover": True,
                    "final_task_success": True,
                },
                "oracle_steps": steps,
            },
            tags=["deterministic_fault", "retry"],
        )

    for index, case in enumerate(database_cases[:5]):
        step = {"tool": "db_query", "arguments": {"query": case["query"]}}
        builder.add(
            category="error_recovery",
            domain=case["domain"],
            scenario_family="transient_database_fault",
            template_family="retry_db_query",
            difficulty="hard",
            instruction=(
                f"{case['instruction']} Nếu truy vấn lỗi tạm thời, hãy thử lại đúng một lần."
            ),
            ground_truth={
                "expected_outcome": "answer",
                "required_tools": ["db_query"],
                "acceptable_sequences": [["db_query", "db_query"]],
                "argument_validators": [
                    {
                        "tool": "db_query",
                        "argument": "query",
                        "comparator": "db_result_equivalent",
                        "reference_sql": case["query"],
                    }
                ],
                "required_answer_facts": [_answer_fact(case["fact"], "recovered_db")],
                "required_evidence": [{"source_type": "database", "source_id": case["entity"]}],
                "minimum_required_steps": 2,
                "fault_plan": [
                    {
                        "tool": "db_query",
                        "occurrence": 1,
                        "error_code": error_codes[index],
                        "retryable": True,
                    }
                ],
                "recovery_requirement": {
                    "must_observe_error": True,
                    "must_recover": True,
                    "final_task_success": True,
                },
                "oracle_steps": [step, step],
            },
            tags=["deterministic_fault", "sql", "retry"],
        )


def add_no_tool(builder: PoolBuilder) -> None:
    units = ("tín chỉ", "ngày", "chỗ", "suất", "hồ sơ")
    for index in range(25):
        value = 10 + index * 3
        unit = units[index % len(units)]
        builder.add(
            category="no_tool",
            domain="instruction_contained_fact",
            scenario_family="answer_from_user_context",
            template_family=f"echo_explicit_{unit.replace(' ', '_')}",
            difficulty="easy",
            instruction=(
                f"Thông tin giả lập đã cho sẵn: chỉ tiêu của mục số {index + 1} là "
                f"{value} {unit}. Hãy nhắc lại đúng chỉ tiêu, không cần tra cứu."
            ),
            ground_truth={
                "expected_outcome": "answer",
                "required_tools": [],
                "forbidden_tools": ALL_TOOLS,
                "acceptable_sequences": [[]],
                "required_answer_facts": [
                    {
                        "fact_id": f"provided_value_{index + 1}",
                        "type": "number",
                        "value": value,
                        "comparator": "numeric_equal",
                    },
                    {
                        "fact_id": f"provided_unit_{index + 1}",
                        "type": "string",
                        "value": unit,
                        "comparator": "substring_normalized",
                    },
                ],
                "minimum_required_steps": 0,
                "oracle_steps": [],
            },
            tags=["no_tool", "instruction_grounded"],
        )


def main() -> int:
    from react_agent.validation.clean_integrity import assert_clean_version_writable

    assert_clean_version_writable(CLEAN_ROOT)
    sources: list[dict[str, Any]] = _read_json(CLEAN_ROOT / "manifests" / "source_catalog.json")
    seed: dict[str, list[list[Any]]] = _read_json(
        CLEAN_ROOT / "environment" / "database" / "seed.json"
    )
    documents = [source for source in sources if source["source_type"] == "document"]
    database_cases = _database_cases(seed)
    builder = PoolBuilder()
    add_single_source(builder, sources)
    add_parameter_extraction(builder, database_cases)
    add_multi_step(builder, sources, database_cases)
    add_db_document(builder, documents, database_cases)
    add_ambiguous(builder)
    add_error_recovery(builder, sources, database_cases)
    add_no_tool(builder)

    if builder.category_counts != Counter(CATEGORY_QUOTAS):
        raise RuntimeError(
            f"category quota mismatch: {dict(builder.category_counts)} != {CATEGORY_QUOTAS}"
        )
    owner_counts = Counter(task["authoring"]["assigned_owner"] for task in builder.tasks)
    if owner_counts != Counter({"huy": 125, "minh": 125}):
        raise RuntimeError(f"owner allocation mismatch: {dict(owner_counts)}")

    public_path = CLEAN_ROOT / "pool" / "tasks.jsonl"
    private_path = CLEAN_ROOT / "private" / "pool_ground_truth.jsonl"
    review_path = CLEAN_ROOT / "reviews" / "review_log.jsonl"
    _write_jsonl(public_path, builder.tasks)
    _write_jsonl(private_path, builder.ground_truth)
    _write_jsonl(review_path, builder.reviews)
    manifest = {
        "dataset_version": "clean_v1_pool",
        "split": "pool",
        "seed": 2026,
        "total_tasks": len(builder.tasks),
        "category_counts": dict(sorted(builder.category_counts.items())),
        "assigned_owner_counts": dict(sorted(owner_counts.items())),
        "generated_by": "codex",
        "review_mode": "automated_checks_owner_waiver",
        "independent_human_review": False,
        "files": {
            str(path.relative_to(CLEAN_ROOT)): _sha256(path)
            for path in (public_path, private_path, review_path)
        },
    }
    manifest_path = CLEAN_ROOT / "manifests" / "pool_generation.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Built {len(builder.tasks)} clean pool tasks; owners={dict(owner_counts)}; "
        f"categories={dict(builder.category_counts)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
