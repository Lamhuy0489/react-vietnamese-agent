"""Exact final proof for an approved field of the original doc_read snapshot.

No projected artifact, inferred source label, or evaluator input is admitted.
The metadata approval's real review timing must be established outside this API.
"""

from __future__ import annotations

import json
import re
from typing import Literal, cast

from pydantic import Field

from react_agent.foundation.artifacts import (
    ArtifactType,
    Immutable,
    Sensitivity,
    SourceType,
    canonical_json,
)
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.final_entitlements import EntitledFinalRelease, _raw_user
from react_agent.security_v1.final_entitlements_v2 import FinalEntitlement
from react_agent.security_v1.final_literal_proof_v1 import (
    HASH,
    IDENTIFIER,
    LiteralProofError,
    release_final_with_literal_proof,
)
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.value_origin_v4 import ValueOriginIndex

PROFILE = "doc_read_final_literal_proof_v1"
RELEASE_PROFILE = "doc_read_final_literal_release_v1"
SOURCE_ID = r"[A-Z][A-Z0-9_]{2,63}"
REQUEST = re.compile(
    rf"(?:Đọc (?P<reads>{SOURCE_ID}(?: và {SOURCE_ID}){{0,7}})\. )?"
    rf"Trả content từ (?P<source>{SOURCE_ID})\."
)


class DocReadApproval(Immutable):
    profile: Literal["doc_read_content_approval_v1"] = "doc_read_content_approval_v1"
    source_id: str = Field(pattern=rf"^{SOURCE_ID}$")
    tool: Literal["doc_read"] = "doc_read"
    field_path: Literal["/content"] = "/content"
    sensitivity: Literal[Sensitivity.PUBLIC] = Sensitivity.PUBLIC
    review_ref: str = Field(min_length=1, max_length=128)

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))


class DocReadLiteralProof(Immutable):
    profile: Literal["doc_read_final_literal_proof_v1"] = "doc_read_final_literal_proof_v1"
    kind: Literal["raw_doc_read_content"] = "raw_doc_read_content"
    literal: str = Field(min_length=8, max_length=64)
    raw_user_artifact_id: str
    raw_user_sha256: str = Field(pattern=HASH)
    source_artifact_id: str
    source_sha256: str = Field(pattern=HASH)
    source_call_id: str = Field(min_length=1, max_length=128)
    field_path: Literal["/content"] = "/content"
    approval_sha256: str = Field(pattern=HASH)

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))


def validate_approval(approval: DocReadApproval | None, expected: str | None) -> DocReadApproval:
    if not isinstance(approval, DocReadApproval):
        raise LiteralProofError("typed doc_read approval required")
    # Revalidate even model_copy/model_construct objects before accepting pins.
    validated = DocReadApproval.model_validate(approval.model_dump(mode="json"))
    if expected is None or not re.fullmatch(HASH, expected) or validated.identity != expected:
        raise LiteralProofError("external doc_read approval hash mismatch")
    return validated


def requested_source(raw_user: str) -> str | None:
    match = REQUEST.fullmatch(raw_user)
    if match is None:
        return None
    reads = match.group("reads")
    if reads is not None:
        ids = reads.split(" và ")
        if len(set(ids)) != len(ids) or match.group("source") not in ids:
            return None
    return match.group("source")


def validate_catalog(approval: DocReadApproval, expected: str, catalog: SourceCatalog) -> None:
    approved = validate_approval(approval, expected)
    label = catalog.resolve(Action(name="doc_read", arguments={"doc_id": approved.source_id}))
    if (label.source_type, label.source_id, label.sensitivity) != (
        SourceType.DOCUMENT, approved.source_id, Sensitivity.PUBLIC,
    ):
        raise LiteralProofError("approved doc_read source requires matching S0 host catalog")


def issue_doc_read_proof(
    index: ValueOriginIndex,
    user_artifact_id: str,
    source_artifact_id: str,
    *,
    approval: DocReadApproval | None = None,
    expected_approval_sha256: str | None = None,
) -> DocReadLiteralProof:
    approved = validate_approval(approval, expected_approval_sha256)
    if not isinstance(index, ValueOriginIndex) or not index.complete:
        raise LiteralProofError("complete opt-in v4 index required")
    user = _raw_user(index, user_artifact_id)
    raw_user = str(user.content())
    if requested_source(raw_user) != approved.source_id:
        raise LiteralProofError("exact raw-user doc_read field request required")
    source = index.store.get(source_artifact_id)
    content = source.content()
    metadata = json.loads(source.metadata_json)
    admitted = index.snapshot()["source_sha256"]
    if (
        source.artifact_type != ArtifactType.DOCUMENT_CONTENT
        or source.source_type != SourceType.DOCUMENT
        or source.producer != "tool_source_snapshot"
        or source.parents or source.transformations
        or source.source_id != approved.source_id
        or source.sensitivity != Sensitivity.PUBLIC
        or admitted.get(source_artifact_id) != source.content_hash
        or not isinstance(content, dict)
        or set(content) != {"doc_id", "title", "content"}
        or not all(isinstance(value, str) for value in content.values())
        or content["doc_id"] != approved.source_id
        or metadata.get("tool") != "doc_read"
        or metadata.get("ok") is not True
        or metadata.get("snapshot_root") is not True
        or metadata.get("label_origin") != "host_catalog"
        or not isinstance(metadata.get("call_id"), str)
        or not 1 <= len(metadata["call_id"]) <= 128
    ):
        raise LiteralProofError("raw successful approved doc_read snapshot required")
    observations = [
        identity for identity in admitted
        if index.store.get(identity).source_type == SourceType.DOCUMENT
        and index.store.get(identity).source_id == approved.source_id
    ]
    if observations != [source_artifact_id]:
        raise LiteralProofError("unique approved source observation required")
    literal = str(content["content"])
    if not re.fullmatch(IDENTIFIER, literal) or not any(c.isdigit() for c in literal):
        raise LiteralProofError("whole content must be a narrow ASCII identifier")
    return DocReadLiteralProof(
        literal=literal, raw_user_artifact_id=user.artifact_id,
        raw_user_sha256=text_hash(raw_user), source_artifact_id=source_artifact_id,
        source_sha256=source.content_hash, source_call_id=metadata["call_id"],
        approval_sha256=approved.identity,
    )


def release_doc_read_proof(
    index: ValueOriginIndex,
    proposed_artifact_id: str,
    user_artifact_id: str,
    entitlement: FinalEntitlement,
    proof: DocReadLiteralProof,
    *,
    approval: DocReadApproval,
    expected_approval_sha256: str,
) -> EntitledFinalRelease:
    """Reuse the exact-final/coverage gate, replacing only typed proof validation."""
    body = bind(
        release_final_with_literal_proof,
        FinalLiteralProof=DocReadLiteralProof,
        issue_literal_proof=issue_doc_read_proof,
        RELEASE_PROFILE=RELEASE_PROFILE,
    )
    return cast(EntitledFinalRelease, body(
        index, proposed_artifact_id, user_artifact_id, entitlement, proof,
        approval=approval, expected_approval_sha256=expected_approval_sha256,
    ))
