"""Opt-in exact-literal final proof; never a general S2 declassification rule."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import Field

from react_agent.foundation.artifacts import (
    ArtifactType,
    Immutable,
    ParentLink,
    Relation,
    Sensitivity,
    SourceType,
    canonical_json,
    join_sensitivity,
    join_trust,
)
from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.contracts import Effect, Reason
from react_agent.security_v1.final_entitlements import (
    EntitledFinalRelease,
    EntitlementError,
    _coverage,
    _raw_user,
)
from react_agent.security_v1.final_entitlements_v2 import (
    FinalEntitlement,
    release_final_with_entitlement,
    strict_protected_matches,
    validate_entitlement,
)
from react_agent.security_v1.value_origin import OriginError, ValueType, canonical_value
from react_agent.security_v1.value_origin_v4 import ValueOriginIndex

PROOF_PROFILE: Literal["final_literal_proof_v1_dev"] = "final_literal_proof_v1_dev"
RELEASE_PROFILE = "final_literal_proof_release_v1_dev"
IDENTIFIER = r"[A-Za-z][A-Za-z0-9_-]{7,63}"
USER_ECHO = re.compile(rf"Nhắc lại nhãn ({IDENTIFIER})\.")
PUBLIC_FIELD = re.compile(r"Trả ([a-z][a-z0-9_]{1,31}) từ ([A-Z][A-Z0-9_]{2,63})\.")
HASH = r"^[0-9a-f]{64}$"


class LiteralProofError(ValueError):
    """The proof is absent, stale or inconsistent with host-observed roots."""


class PublicFieldApproval(Immutable):
    """Metadata-only host approval; chronology is external to this schema."""

    profile: Literal["public_final_field_approval_v1"] = "public_final_field_approval_v1"
    source_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,63}$")
    field_name: str = Field(pattern=r"^[a-z][a-z0-9_]{1,31}$")
    review_ref: str = Field(min_length=1, max_length=128)
    sensitivity: Literal[Sensitivity.PUBLIC] = Sensitivity.PUBLIC

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))


class FinalLiteralProof(Immutable):
    profile: Literal["final_literal_proof_v1_dev"] = PROOF_PROFILE
    kind: Literal["raw_user_literal", "reviewed_public_field"]
    literal: str = Field(min_length=8, max_length=64)
    raw_user_artifact_id: str
    raw_user_sha256: str = Field(pattern=HASH)
    source_artifact_id: str
    source_sha256: str = Field(pattern=HASH)
    approval_sha256: str | None = Field(default=None, pattern=HASH)

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))


def issue_literal_proof(
    index: ValueOriginIndex,
    user_artifact_id: str,
    source_artifact_id: str,
    *,
    approval: PublicFieldApproval | None = None,
    expected_approval_sha256: str | None = None,
) -> FinalLiteralProof:
    """Derive a proof from raw roots and an independently pinned S0 approval."""
    if not isinstance(index, ValueOriginIndex):
        raise LiteralProofError("opt-in v4 index required")
    user = _raw_user(index, user_artifact_id)
    raw_user = str(user.content())
    if approval is None:
        if expected_approval_sha256 is not None or source_artifact_id != user_artifact_id:
            raise LiteralProofError("raw-user proof has unexpected source or approval")
        match = USER_ECHO.fullmatch(raw_user)
        if match is None:
            raise LiteralProofError("exact raw-user echo authorization required")
        source = user
        kind: Literal["raw_user_literal", "reviewed_public_field"] = "raw_user_literal"
        literal = match.group(1)
        approval_sha256 = None
    else:
        if (
            expected_approval_sha256 is None
            or not re.fullmatch(r"[0-9a-f]{64}", expected_approval_sha256)
            or approval.identity != expected_approval_sha256
        ):
            raise LiteralProofError("external public approval hash mismatch")
        match = PUBLIC_FIELD.fullmatch(raw_user)
        if match is None or (match.group(1), match.group(2)) != (
            approval.field_name,
            approval.source_id,
        ):
            raise LiteralProofError("exact public field authorization required")
        source = index.store.get(source_artifact_id)
        content = source.content()
        if (
            source.artifact_type != ArtifactType.DOCUMENT_CONTENT
            or source.source_type != SourceType.DOCUMENT
            or source.producer != "tool_source_snapshot"
            or source.parents
            or source.transformations
            or source.source_id != approval.source_id
            or source.sensitivity != Sensitivity.PUBLIC
            or not isinstance(content, dict)
            or set(content) != {approval.field_name}
            or not isinstance(content[approval.field_name], str)
        ):
            raise LiteralProofError("reviewed S0 source shape or label mismatch")
        kind = "reviewed_public_field"
        literal = content[approval.field_name]
        approval_sha256 = approval.identity
    try:
        literal = canonical_value(literal, ValueType.IDENTIFIER)
    except ValueError as exc:
        raise LiteralProofError("proof literal outside identifier profile") from exc
    if not any(char.isdigit() for char in literal) or not USER_ECHO.fullmatch(
        f"Nhắc lại nhãn {literal}."
    ):
        raise LiteralProofError("proof literal outside narrow ASCII profile")
    return FinalLiteralProof(
        kind=kind,
        literal=literal,
        raw_user_artifact_id=user.artifact_id,
        raw_user_sha256=text_hash(raw_user),
        source_artifact_id=source.artifact_id,
        source_sha256=source.content_hash,
        approval_sha256=approval_sha256,
    )


def release_final_with_literal_proof(
    index: ValueOriginIndex,
    proposed_artifact_id: str,
    user_artifact_id: str,
    entitlement: FinalEntitlement,
    proof: FinalLiteralProof,
    *,
    approval: PublicFieldApproval | None = None,
    expected_approval_sha256: str | None = None,
) -> EntitledFinalRelease:
    """Permit only an exact already-public literal; otherwise retain v2 gate."""
    if not isinstance(proof, FinalLiteralProof):
        raise LiteralProofError("typed final literal proof required")
    user = _raw_user(index, user_artifact_id)
    validate_entitlement(str(user.content()), entitlement)
    verified = issue_literal_proof(
        index,
        user_artifact_id,
        proof.source_artifact_id,
        approval=approval,
        expected_approval_sha256=expected_approval_sha256,
    )
    if proof.model_dump(mode="json") != verified.model_dump(mode="json"):
        raise LiteralProofError("final literal proof does not match raw roots")
    store = index.store
    proposed = store.get(proposed_artifact_id)
    if (
        proposed.artifact_type != ArtifactType.FINAL_RESPONSE
        or proposed.source_type != SourceType.MODEL
        or not proposed.parents
        or not isinstance(proposed.content(), str)
        or proposed.created_step < index.last_observed_step
    ):
        raise EntitlementError("current model final proposal required")
    ancestors = {a.artifact_id for a in store.ancestors(proposed_artifact_id)}
    if (
        user_artifact_id not in ancestors
        or proof.source_artifact_id not in ancestors
        or not _coverage(index, proposed_artifact_id, user_artifact_id)
    ):
        raise LiteralProofError("proof source ancestry or index coverage incomplete")
    released = str(proposed.content())
    if released != proof.literal:
        return release_final_with_entitlement(
            index, proposed_artifact_id, user_artifact_id, entitlement
        )
    try:
        matches = strict_protected_matches(index, released)
    except OriginError:
        return release_final_with_entitlement(
            index, proposed_artifact_id, user_artifact_id, entitlement
        )
    if not matches or any(
        match.start != 0
        or match.end != len(released)
        or match.origin.value != proof.literal
        for match in matches
    ):
        return release_final_with_entitlement(
            index, proposed_artifact_id, user_artifact_id, entitlement
        )
    parent_ids = tuple(
        dict.fromkeys(
            (
                proposed.artifact_id,
                proof.source_artifact_id,
                *(m.origin.artifact_id for m in matches),
            )
        )
    )
    parents = [store.get(identity) for identity in parent_ids]
    entitlement_hash = text_hash(entitlement.model_dump_json())
    artifact = store.create(
        released,
        artifact_type=ArtifactType.FINAL_RESPONSE,
        source_type=SourceType.SYSTEM,
        source_id=proposed.artifact_id,
        producer=RELEASE_PROFILE,
        created_step=proposed.created_step,
        sensitivity=join_sensitivity(*(parent.sensitivity for parent in parents)),
        trust=join_trust(*(parent.trust for parent in parents)),
        parents=tuple(
            ParentLink(parent_id=parent.artifact_id, relation=Relation.DERIVED_FROM)
            for parent in parents
        ),
        transformations=(RELEASE_PROFILE,),
        metadata={
            "effect": Effect.ALLOW.value,
            "reason": Reason.PASS.value,
            "index_sha256": index.identity,
            "entitlement_sha256": entitlement_hash,
            "proof_sha256": proof.identity,
            "approval_sha256": proof.approval_sha256,
        },
    )
    return EntitledFinalRelease(
        profile=RELEASE_PROFILE,
        effect=Effect.ALLOW,
        reasons=(Reason.PASS,),
        proposed_artifact_id=proposed.artifact_id,
        released_artifact_id=artifact.artifact_id,
        proposed_sha256=proposed.content_hash,
        released_sha256=artifact.content_hash,
        index_sha256=index.identity,
        entitlement_sha256=entitlement_hash,
        matches=matches,
        authorized_matches=matches,
        unauthorized_matches=(),
        redacted_spans=(),
    )
