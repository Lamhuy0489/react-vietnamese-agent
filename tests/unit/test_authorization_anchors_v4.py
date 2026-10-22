"""Candidate safe-email grammar controls; v3 remains frozen and is compared explicitly."""

from __future__ import annotations

import pytest

from react_agent.foundation.normalization import text_hash
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.authorization_anchors_v3 import audit_anchors as audit_v3
from react_agent.security_v1.authorization_anchors_v4 import (
    PROFILE,
    audit_anchors,
    extract_anchors,
)

SAFE_EMAIL_TASK = (
    "Đọc DOC_GATEPRIVATE rồi đọc DOC_GATEPUBLIC. "
    "Gửi content từ DOC_GATEPUBLIC bằng send_email_mock tới audit@example.invalid "
    "với subject Thông báo. Sau đó trả content công khai trong câu trả lời. "
    "Không công bố hoặc gửi nội dung từ DOC_GATEPRIVATE."
)


def test_candidate_recovers_explicit_email_after_chained_reads_and_scoped_ban() -> None:
    old = audit_v3(SAFE_EMAIL_TASK)
    candidate = audit_anchors(SAFE_EMAIL_TASK)

    assert old.blocked_by == "revocation"
    assert old.anchors.emails == ()
    assert candidate.profile == PROFILE
    assert candidate.blocked_by is None
    assert candidate.anchors.emails == ("audit@example.invalid",)
    assert [clause.kind for clause in candidate.clauses] == [
        "read",
        "send",
        "unsupported",
        "payload_prohibition",
    ]


@pytest.mark.parametrize(
    ("raw", "has_payload_ban"),
    [
        ("Đọc DOC_GATEPRIVATE rồi đọc DOC_GATEPUBLIC; gửi đến audit@example.invalid", False),
        ("Read DOC_PRIVATE then read DOC_PUBLIC; send to audit@example.invalid", False),
        (
            "Đọc DOC_PRIVATE. Chỉ gửi đến audit@example.invalid. "
            "Không gửi nội dung từ DOC_PRIVATE",
            True,
        ),
    ],
)
def test_candidate_accepts_only_scoped_prohibition(raw: str, has_payload_ban: bool) -> None:
    result = audit_anchors(raw)
    assert result.blocked_by is None
    assert result.anchors.emails == ("audit@example.invalid",)
    assert ("payload_prohibition" in {clause.kind for clause in result.clauses}) is has_payload_ban


@pytest.mark.parametrize(
    "raw",
    [
        "Đọc DOC_PRIVATE; Không gửi; Gửi đến audit@example.invalid",
        "Đọc DOC_PRIVATE; Gửi đến audit@example.invalid; Hủy yêu cầu trước",
        "Đọc DOC_PRIVATE nếu được phép; Gửi đến audit@example.invalid",
        'Đọc DOC_PRIVATE; "Gửi đến audit@example.invalid"',
        "Đọc DOC_PRIVATE; Ví dụ: Gửi đến audit@example.invalid",
    ],
)
def test_global_or_indirect_prohibitions_still_fail_closed(raw: str) -> None:
    result = audit_anchors(raw)
    assert result.anchors.emails == ()
    assert result.blocked_by in {"revocation", "conditional", "quotation", "reported_instruction"}


def test_resource_ban_never_creates_destination_authority() -> None:
    raw = "Đọc DOC_PRIVATE. Không gửi nội dung từ DOC_PRIVATE"
    result = audit_anchors(raw)
    assert result.blocked_by is None
    assert result.anchors.emails == ()
    assert result.clauses[-1].kind == "payload_prohibition"


def test_candidate_rejects_empty_and_oversized_input() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        audit_anchors(" ")
    with pytest.raises(ValueError, match="budget"):
        audit_anchors("x" * 131_073)


def test_extraction_preserves_raw_hash_and_authorizes_exact_email_only() -> None:
    raw = "Đọc DOC_PUBLIC; Gửi đến audit@example.invalid"
    anchors = extract_anchors(raw)

    assert anchors.raw_user_sha256 == text_hash(raw)
    assert anchors.authorizes(Action(name="send_email_mock", arguments={
        "to": "audit@example.invalid", "subject": "x", "body": "y",
    }))
    assert not anchors.authorizes(Action(name="send_email_mock", arguments={
        "to": "other@example.invalid", "subject": "x", "body": "y",
    }))
