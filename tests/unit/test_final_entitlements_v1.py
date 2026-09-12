from __future__ import annotations

import pytest

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.foundation.runtime_hooks import derive
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.final_entitlements import (
    EntitledFinalRelease,
    EntitlementError,
    extract_final_entitlement,
    release_final_with_entitlement,
)
from react_agent.security_v1.value_origin import ValueOriginIndex


def build_fixture(
    user_text: str,
    final_text: str,
    *,
    source_id: str = "DOC_PRIVATE",
    source_trust: Trust = Trust.TRUSTED,
    source_content: object | None = None,
) -> tuple[ArtifactStore, ValueOriginIndex, str, str]:
    store = ArtifactStore("synthetic_entitlement")
    user = store.create(
        user_text,
        artifact_type=ArtifactType.USER_INPUT,
        source_type=SourceType.USER,
        source_id="synthetic_user",
        producer="host_context",
        created_step=0,
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.UNTRUSTED,
    )
    source = store.create(
        source_content if source_content is not None else {"gpa": 3.2},
        artifact_type=ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.DOCUMENT,
        source_id=source_id,
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=Sensitivity.CONFIDENTIAL,
        trust=source_trust,
    )
    index = ValueOriginIndex(store)
    index.add_artifact(user.artifact_id, observed_step=0)
    index.add_artifact(source.artifact_id, observed_step=1)
    model = derive(
        store,
        "synthetic model output",
        kind=ArtifactType.MODEL_OUTPUT,
        parents=(user.artifact_id, source.artifact_id),
        step=2,
    )
    proposal = derive(
        store,
        final_text,
        kind=ArtifactType.FINAL_RESPONSE,
        parents=(model.artifact_id,),
        step=3,
    )
    return store, index, user.artifact_id, proposal.artifact_id


def test_extracts_explicit_source_and_value_type_only() -> None:
    entitlement = extract_final_entitlement("Trả GPA từ DOC_PRIVATE trong câu trả lời")
    assert entitlement.explicit
    assert entitlement.resource_ids == ("DOC_PRIVATE",)
    assert entitlement.value_types == ("GPA",)


@pytest.mark.parametrize(
    "text",
    [
        "Không trả GPA từ DOC_PRIVATE",
        "Nếu cần trả GPA từ DOC_PRIVATE",
        "Trả GPA từ 'DOC_PRIVATE'",
        "Đọc tài liệu DOC_PRIVATE",
        "Trả kết quả công khai",
    ],
)
def test_missing_or_rejected_entitlement_is_not_explicit(text: str) -> None:
    entitlement = extract_final_entitlement(text)
    assert not entitlement.explicit
    assert not entitlement.resource_ids or not entitlement.value_types


def test_authorized_private_gpa_is_released() -> None:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = build_fixture(text, "GPA: 3.2")
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    assert decision.effect == Effect.ALLOW
    assert store.get(decision.released_artifact_id).content() == "GPA: 3.2"
    assert len(decision.authorized_matches) == 1
    assert not decision.unauthorized_matches


def test_no_entitlement_redacts_private_value() -> None:
    text = "Đọc DOC_PRIVATE và tóm tắt"
    store, index, user, proposal = build_fixture(text, "GPA: 3.2")
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    assert decision.effect == Effect.REDACT
    assert store.get(decision.released_artifact_id).content() == "GPA: [REDACTED]"
    assert len(decision.unauthorized_matches) == 1


def test_untrusted_origin_cannot_be_entitled() -> None:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = build_fixture(
        text, "GPA: 3.2", source_trust=Trust.UNTRUSTED
    )
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    assert decision.effect == Effect.REDACT
    assert store.get(decision.released_artifact_id).content() == "GPA: [REDACTED]"


def test_value_type_entitlement_redacts_other_private_type() -> None:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = build_fixture(
        text,
        "GPA: 3.2; email: private@example.test",
        source_content={"gpa": 3.2, "email": "private@example.test"},
    )
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    assert decision.effect == Effect.REDACT
    assert store.get(decision.released_artifact_id).content() == (
        "GPA: 3.2; email: [REDACTED]"
    )
    assert len(decision.authorized_matches) == 1
    assert len(decision.unauthorized_matches) == 1


def test_resource_entitlement_does_not_cross_source() -> None:
    text = "Trả GPA từ DOC_ALLOWED trong câu trả lời"
    store, index, user, proposal = build_fixture(text, "GPA: 3.2", source_id="DOC_OTHER")
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    assert decision.effect == Effect.REDACT
    assert store.get(decision.released_artifact_id).content() == "GPA: [REDACTED]"


def test_normalized_only_match_denies_without_offset_mapping() -> None:
    text = "Trả email từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = build_fixture(
        text,
        "private\u200b@example.test",
        source_content={"email": "private@example.test"},
    )
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    assert decision.effect == Effect.DENY
    assert store.get(decision.released_artifact_id).content() == ""


def test_missing_source_coverage_denies_and_keeps_proposal() -> None:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = build_fixture(text, "GPA: 3.2")
    source = next(a for a in store.all() if a.producer == "tool_source_snapshot")
    incomplete = ValueOriginIndex(store)
    incomplete.add_artifact(user, observed_step=0)
    decision = release_final_with_entitlement(
        incomplete, proposal, user, extract_final_entitlement(text)
    )
    assert decision.effect == Effect.DENY
    assert store.get(proposal).content() == "GPA: 3.2"
    assert source.artifact_id not in incomplete.snapshot()["source_sha256"]


def test_entitlement_hash_is_bound_to_raw_user() -> None:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = build_fixture(text, "GPA: 3.2")
    other = extract_final_entitlement("Trả GPA từ DOC_OTHER trong câu trả lời")
    with pytest.raises(EntitlementError, match="bound"):
        release_final_with_entitlement(index, proposal, user, other)
    assert len(store.all()) == 4


def test_public_final_without_known_match_is_allowed() -> None:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = build_fixture(
        text, "Không có dữ liệu riêng trong câu trả lời", source_content={"title": "Public record"}
    )
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    assert decision.effect == Effect.ALLOW
    assert store.get(decision.released_artifact_id).content() == (
        "Không có dữ liệu riêng trong câu trả lời"
    )


def test_release_is_serializable_and_preserves_conservative_labels() -> None:
    text = "Trả GPA từ DOC_PRIVATE trong câu trả lời"
    store, index, user, proposal = build_fixture(text, "GPA: 3.2")
    decision = release_final_with_entitlement(
        index, proposal, user, extract_final_entitlement(text)
    )
    assert EntitledFinalRelease.model_validate_json(decision.model_dump_json()) == decision
    released = store.get(decision.released_artifact_id)
    assert released.sensitivity == Sensitivity.CONFIDENTIAL
    assert released.trust == Trust.UNTRUSTED


def test_all_supported_value_cues_have_a_bounded_mapping() -> None:
    for cue, kind in (
        ("email", "EMAIL"),
        ("URL", "URL"),
        ("student id", "STUDENT_ID"),
        ("course code", "COURSE_CODE"),
        ("phone", "PHONE"),
        ("money", "MONEY"),
        ("date", "DATE"),
        ("identifier", "IDENTIFIER"),
    ):
        entitlement = extract_final_entitlement(f"Show {cue} from DOC_PRIVATE")
        assert entitlement.explicit and entitlement.value_types == (kind,)
