"""Synthetic CPU controls for exact final-literal proof; no runtime wiring."""

from __future__ import annotations

import json
from dataclasses import dataclass

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
from react_agent.security_v1.final_entitlements_v2 import (
    extract_final_entitlement,
    release_final_with_entitlement,
)
from react_agent.security_v1.final_literal_proof_v1 import (
    FinalLiteralProof,
    LiteralProofError,
    PublicFieldApproval,
    issue_literal_proof,
    release_final_with_literal_proof,
)
from react_agent.security_v1.value_origin_v4 import ValueOriginIndex

USER_TOKEN = "NAMESPACEX2037"  # noqa: S105 - synthetic public test fixture
PUBLIC_TOKEN = "FIELDMARKER2037"  # noqa: S105 - synthetic public test fixture


@dataclass
class Scene:
    store: ArtifactStore
    index: ValueOriginIndex
    user_id: str
    private_id: str
    public_id: str | None
    proposed_id: str
    user_text: str


def scene(
    user_text: str,
    private_text: str,
    final_text: str,
    *,
    public_content: object | None = None,
    public_sensitivity: Sensitivity = Sensitivity.PUBLIC,
    private_sensitivity: Sensitivity = Sensitivity.CONFIDENTIAL,
    private_trust: Trust = Trust.UNTRUSTED,
    include_public_parent: bool = True,
    index_public: bool = True,
) -> Scene:
    store = ArtifactStore("literal_proof_dev")
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
    private = store.create(
        {"content": private_text},
        artifact_type=ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.DOCUMENT,
        source_id="DOC_PRIVATE",
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=private_sensitivity,
        trust=private_trust,
    )
    public = None
    if public_content is not None:
        public = store.create(
            public_content,
            artifact_type=ArtifactType.DOCUMENT_CONTENT,
            source_type=SourceType.DOCUMENT,
            source_id="DOC_PUBLIC",
            producer="tool_source_snapshot",
            created_step=2,
            sensitivity=public_sensitivity,
            trust=Trust.UNTRUSTED,
        )
    index = ValueOriginIndex(store)
    index.add_artifact(user.artifact_id, observed_step=0)
    index.add_artifact(private.artifact_id, observed_step=1)
    if public is not None and index_public:
        index.add_artifact(public.artifact_id, observed_step=2)
    parents = [user.artifact_id, private.artifact_id]
    if public is not None and include_public_parent:
        parents.append(public.artifact_id)
    model = derive(
        store,
        "synthetic forced proposal",
        kind=ArtifactType.MODEL_OUTPUT,
        parents=tuple(parents),
        step=3,
    )
    proposed = derive(
        store,
        final_text,
        kind=ArtifactType.FINAL_RESPONSE,
        parents=(model.artifact_id,),
        step=4,
    )
    return Scene(
        store,
        index,
        user.artifact_id,
        private.artifact_id,
        public.artifact_id if public is not None else None,
        proposed.artifact_id,
        user_text,
    )


def approval() -> PublicFieldApproval:
    return PublicFieldApproval(
        source_id="DOC_PUBLIC", field_name="room_code", review_ref="synthetic-dev-review"
    )


def test_raw_user_exact_echo_with_s2_collision() -> None:
    task = f"Nhắc lại nhãn {USER_TOKEN}."
    private = f"Mã riêng {USER_TOKEN}."
    baseline_fixture = scene(task, private, USER_TOKEN)
    fixture = scene(task, private, USER_TOKEN)
    entitlement = extract_final_entitlement(fixture.user_text)
    baseline = release_final_with_entitlement(
        baseline_fixture.index,
        baseline_fixture.proposed_id,
        baseline_fixture.user_id,
        entitlement,
    )
    assert baseline.effect == Effect.REDACT
    proof = issue_literal_proof(fixture.index, fixture.user_id, fixture.user_id)
    result = release_final_with_literal_proof(
        fixture.index, fixture.proposed_id, fixture.user_id, entitlement, proof
    )
    assert result.effect == Effect.ALLOW
    assert result.profile == "final_literal_proof_release_v1_dev"
    released = fixture.store.get(result.released_artifact_id)
    assert released.content() == USER_TOKEN
    assert released.sensitivity == Sensitivity.CONFIDENTIAL
    assert json.loads(released.metadata_json)["proof_sha256"] == proof.identity
    assert fixture.store.get(fixture.proposed_id).content() == USER_TOKEN


@pytest.mark.parametrize("private_trust", list(Trust))
def test_reviewed_public_field_with_s2_collision(private_trust: Trust) -> None:
    fixture = scene(
        "Trả room_code từ DOC_PUBLIC.",
        f"Mã riêng {PUBLIC_TOKEN}.",
        PUBLIC_TOKEN,
        public_content={"room_code": PUBLIC_TOKEN},
        private_trust=private_trust,
    )
    grant = approval()
    proof = issue_literal_proof(
        fixture.index,
        fixture.user_id,
        str(fixture.public_id),
        approval=grant,
        expected_approval_sha256=grant.identity,
    )
    result = release_final_with_literal_proof(
        fixture.index,
        fixture.proposed_id,
        fixture.user_id,
        extract_final_entitlement(fixture.user_text),
        proof,
        approval=grant,
        expected_approval_sha256=grant.identity,
    )
    assert result.effect == Effect.ALLOW
    assert fixture.store.get(result.released_artifact_id).content() == PUBLIC_TOKEN
    assert json.loads(fixture.store.get(result.released_artifact_id).metadata_json)[
        "approval_sha256"
    ] == grant.identity


def test_extra_private_context_falls_back_to_existing_redaction() -> None:
    fixture = scene(
        f"Nhắc lại nhãn {USER_TOKEN}.",
        f"Mã riêng {USER_TOKEN}.",
        f"Mã riêng: {USER_TOKEN}",
    )
    proof = issue_literal_proof(fixture.index, fixture.user_id, fixture.user_id)
    result = release_final_with_literal_proof(
        fixture.index,
        fixture.proposed_id,
        fixture.user_id,
        extract_final_entitlement(fixture.user_text),
        proof,
    )
    assert result.effect == Effect.REDACT
    assert USER_TOKEN not in fixture.store.get(result.released_artifact_id).content()


def test_private_only_literal_cannot_obtain_raw_user_proof() -> None:
    fixture = scene("Đọc DOC_PRIVATE rồi trả lời.", f"Mã riêng {USER_TOKEN}.", USER_TOKEN)
    with pytest.raises(LiteralProofError, match="echo authorization"):
        issue_literal_proof(fixture.index, fixture.user_id, fixture.user_id)
    baseline = release_final_with_entitlement(
        fixture.index,
        fixture.proposed_id,
        fixture.user_id,
        extract_final_entitlement(fixture.user_text),
    )
    assert baseline.effect == Effect.REDACT
    assert USER_TOKEN not in fixture.store.get(baseline.released_artifact_id).content()


@pytest.mark.parametrize(
    "user_text",
    [
        f"Không nhắc lại nhãn {USER_TOKEN}.",
        f"Nhắc lại nhãn '{USER_TOKEN}'.",
        f"Nhắc lại nhãn {USER_TOKEN}. Đọc DOC_PRIVATE.",
    ],
)
def test_noncanonical_or_negated_user_request_cannot_issue(user_text: str) -> None:
    fixture = scene(user_text, f"Mã riêng {USER_TOKEN}.", USER_TOKEN)
    with pytest.raises(LiteralProofError, match="echo authorization"):
        issue_literal_proof(fixture.index, fixture.user_id, fixture.user_id)


def test_forged_or_stale_proof_rejected_before_release() -> None:
    fixture = scene(f"Nhắc lại nhãn {USER_TOKEN}.", f"Mã riêng {USER_TOKEN}.", USER_TOKEN)
    proof = issue_literal_proof(fixture.index, fixture.user_id, fixture.user_id)
    before = len(fixture.store.all())
    forged = FinalLiteralProof.model_validate(
        {**proof.model_dump(mode="json"), "source_sha256": "0" * 64}
    )
    with pytest.raises(LiteralProofError, match="does not match"):
        release_final_with_literal_proof(
            fixture.index,
            fixture.proposed_id,
            fixture.user_id,
            extract_final_entitlement(fixture.user_text),
            forged,
        )
    assert len(fixture.store.all()) == before


def test_public_approval_pin_and_s0_are_independent_gates() -> None:
    fixture = scene(
        "Trả room_code từ DOC_PUBLIC.",
        f"Mã riêng {PUBLIC_TOKEN}.",
        PUBLIC_TOKEN,
        public_content={"room_code": PUBLIC_TOKEN},
    )
    grant = approval()
    with pytest.raises(LiteralProofError, match="approval hash"):
        issue_literal_proof(
            fixture.index,
            fixture.user_id,
            str(fixture.public_id),
            approval=grant,
            expected_approval_sha256="0" * 64,
        )
    proof = issue_literal_proof(
        fixture.index,
        fixture.user_id,
        str(fixture.public_id),
        approval=grant,
        expected_approval_sha256=grant.identity,
    )
    with pytest.raises(LiteralProofError, match="approval hash"):
        release_final_with_literal_proof(
            fixture.index,
            fixture.proposed_id,
            fixture.user_id,
            extract_final_entitlement(fixture.user_text),
            proof,
            approval=grant,
            expected_approval_sha256="0" * 64,
        )
    mislabeled = scene(
        "Trả room_code từ DOC_PUBLIC.",
        f"Mã riêng {PUBLIC_TOKEN}.",
        PUBLIC_TOKEN,
        public_content={"room_code": PUBLIC_TOKEN},
        public_sensitivity=Sensitivity.CONFIDENTIAL,
    )
    with pytest.raises(LiteralProofError, match="S0 source"):
        issue_literal_proof(
            mislabeled.index,
            mislabeled.user_id,
            str(mislabeled.public_id),
            approval=grant,
            expected_approval_sha256=grant.identity,
        )


@pytest.mark.parametrize(
    ("user_text", "public_content"),
    [
        ("Trả other_code từ DOC_PUBLIC.", {"room_code": PUBLIC_TOKEN}),
        ("Trả room_code từ DOC_WRONG.", {"room_code": PUBLIC_TOKEN}),
        ("Trả room_code từ DOC_PUBLIC.", {"room_code": PUBLIC_TOKEN, "extra": "x"}),
    ],
)
def test_public_field_wrong_scope_or_shape_rejected(
    user_text: str, public_content: object
) -> None:
    fixture = scene(
        user_text,
        f"Mã riêng {PUBLIC_TOKEN}.",
        PUBLIC_TOKEN,
        public_content=public_content,
    )
    grant = approval()
    with pytest.raises(LiteralProofError, match="authorization|shape"):
        issue_literal_proof(
            fixture.index,
            fixture.user_id,
            str(fixture.public_id),
            approval=grant,
            expected_approval_sha256=grant.identity,
        )


def test_missing_public_ancestry_or_index_coverage_rejected() -> None:
    grant = approval()
    for include_parent, index_public in ((False, True), (True, False)):
        fixture = scene(
            "Trả room_code từ DOC_PUBLIC.",
            f"Mã riêng {PUBLIC_TOKEN}.",
            PUBLIC_TOKEN,
            public_content={"room_code": PUBLIC_TOKEN},
            include_public_parent=include_parent,
            index_public=index_public,
        )
        proof = issue_literal_proof(
            fixture.index,
            fixture.user_id,
            str(fixture.public_id),
            approval=grant,
            expected_approval_sha256=grant.identity,
        )
        with pytest.raises(LiteralProofError, match="ancestry or index coverage"):
            release_final_with_literal_proof(
                fixture.index,
                fixture.proposed_id,
                fixture.user_id,
                extract_final_entitlement(fixture.user_text),
                proof,
                approval=grant,
                expected_approval_sha256=grant.identity,
            )


def test_public_label_without_reviewed_approval_is_not_a_proof() -> None:
    fixture = scene(
        "Trả room_code từ DOC_PUBLIC.",
        f"Mã riêng {PUBLIC_TOKEN}.",
        PUBLIC_TOKEN,
        public_content={"room_code": PUBLIC_TOKEN},
    )
    with pytest.raises(LiteralProofError, match="unexpected source or approval"):
        issue_literal_proof(fixture.index, fixture.user_id, str(fixture.public_id))


def test_proof_cannot_release_different_private_literal() -> None:
    fixture = scene(
        "Trả room_code từ DOC_PUBLIC.",
        f"Mã riêng {USER_TOKEN}.",
        USER_TOKEN,
        public_content={"room_code": PUBLIC_TOKEN},
    )
    grant = approval()
    proof = issue_literal_proof(
        fixture.index,
        fixture.user_id,
        str(fixture.public_id),
        approval=grant,
        expected_approval_sha256=grant.identity,
    )
    result = release_final_with_literal_proof(
        fixture.index,
        fixture.proposed_id,
        fixture.user_id,
        extract_final_entitlement(fixture.user_text),
        proof,
        approval=grant,
        expected_approval_sha256=grant.identity,
    )
    assert result.effect == Effect.REDACT
    assert USER_TOKEN not in fixture.store.get(result.released_artifact_id).content()


def test_normalized_only_private_copy_does_not_use_proof() -> None:
    fixture = scene(
        f"Nhắc lại nhãn {USER_TOKEN}.",
        f"Mã riêng {USER_TOKEN}.",
        "NAMESPACEX\u200b2037",
    )
    proof = issue_literal_proof(fixture.index, fixture.user_id, fixture.user_id)
    result = release_final_with_literal_proof(
        fixture.index,
        fixture.proposed_id,
        fixture.user_id,
        extract_final_entitlement(fixture.user_text),
        proof,
    )
    assert result.effect == Effect.DENY
    assert fixture.store.get(result.released_artifact_id).content() == ""


def test_non_numeric_echo_literal_cannot_issue() -> None:
    fixture = scene(
        "Nhắc lại nhãn NAMESPACEXTRA.",
        "Ghi chú riêng NAMESPACEXTRA.",
        "NAMESPACEXTRA",
    )
    with pytest.raises(LiteralProofError, match="narrow ASCII profile"):
        issue_literal_proof(fixture.index, fixture.user_id, fixture.user_id)
