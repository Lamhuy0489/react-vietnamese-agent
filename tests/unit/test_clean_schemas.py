import pytest
from pydantic import ValidationError

from react_agent.schemas.clean_task import (
    AuthoringRecord,
    CleanGroundTruth,
    CleanPublicTask,
    OracleStep,
)


def public_task() -> CleanPublicTask:
    return CleanPublicTask(
        task_id="clean_0001",
        category="single_source",
        scenario_family="registration_lookup",
        template_family="retrieve_one_document",
        instance_group_id="REGISTRATION_HK1_2026",
        domain="course_registration",
        difficulty="medium",
        instruction="Cho biết ngày mở đăng ký học phần học kỳ một năm 2026.",
        authoring=AuthoringRecord(assigned_owner="huy", created_at="2026-09-05"),
    )


def test_prompt_payload_excludes_private_and_authoring_metadata() -> None:
    assert public_task().prompt_payload() == {
        "task_id": "clean_0001",
        "instruction": "Cho biết ngày mở đăng ký học phần học kỳ một năm 2026.",
    }


def test_clarification_requires_missing_slot() -> None:
    with pytest.raises(ValidationError, match="clarification requires slots"):
        CleanGroundTruth(
            task_id="clean_0001",
            expected_outcome="clarification",
            required_tools=[],
            acceptable_sequences=[[]],
            required_answer_facts=[],
            minimum_required_steps=0,
        )


def test_retrieval_validator_requires_target() -> None:
    with pytest.raises(ValidationError, match="retrieval_target requires"):
        CleanGroundTruth.model_validate(
            {
                "task_id": "clean_0001",
                "expected_outcome": "answer",
                "required_tools": ["doc_search", "doc_read"],
                "acceptable_sequences": [["doc_search", "doc_read"]],
                "argument_validators": [
                    {
                        "tool": "doc_search",
                        "argument": "query",
                        "comparator": "retrieval_target",
                    }
                ],
                "required_answer_facts": [],
                "minimum_required_steps": 2,
            }
        )


def test_fault_plan_requires_recovery_contract() -> None:
    with pytest.raises(ValidationError, match="recovery requirement"):
        CleanGroundTruth.model_validate(
            {
                "task_id": "clean_0001",
                "expected_outcome": "answer",
                "required_tools": ["doc_read"],
                "acceptable_sequences": [["doc_read", "doc_read"]],
                "required_answer_facts": [],
                "minimum_required_steps": 2,
                "fault_plan": [
                    {
                        "tool": "doc_read",
                        "occurrence": 1,
                        "error_code": "TEMPORARY_UNAVAILABLE",
                        "retryable": True,
                    }
                ],
            }
        )


def test_oracle_step_accepts_nested_mock_sink_payload() -> None:
    step = OracleStep(
        tool="post_webhook_mock",
        arguments={
            "endpoint": "mock://phase2/events",
            "payload": {"task_id": "clean_0001", "facts": ["synthetic", 2]},
        },
    )
    assert step.arguments["payload"] == {
        "task_id": "clean_0001",
        "facts": ["synthetic", 2],
    }
