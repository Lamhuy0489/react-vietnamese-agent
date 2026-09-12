"""Host-bound private-record final entitlements for a future A6 runtime.

The component is intentionally independent of the frozen public-final release
policy and runtime v5.  It never accepts evaluator grants or model-origin
claims; a host must bind the entitlement to the raw user artifact and the
run-local value-origin index.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import Field

from react_agent.foundation.artifacts import (
    ArtifactType,
    Immutable,
    ParentLink,
    Relation,
    SourceType,
    Trust,
    join_sensitivity,
    join_trust,
)
from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.contracts import Effect, Reason
from react_agent.security_v1.value_origin import (
    MAX_BYTES,
    OriginError,
    OriginRecord,
    ProtectedMatch,
    ValueOriginIndex,
    ValueType,
)

PROFILE = "final_entitlement_v1"
RELEASE_PROFILE = "final_entitlement_release_v1"
REPLACEMENT = "[REDACTED]"
MAX_ENTITLEMENTS = 256

_RESOURCE_ID = re.compile(r"\b(?:DOC|CACHE)_[A-Za-z0-9][A-Za-z0-9_-]{0,63}\b")
_ENTITLEMENT_CUE = re.compile(
    r"\b(?:trả|trả|hiển\s+thị|hien\s+thi|show|include|report|provide|xem|"
    r"final\s+answer|câu\s+trả\s+lời|cau\s+tra\s+loi)\b",
    re.IGNORECASE,
)
_REJECT_CLAUSE = re.compile(
    r"\b(?:không|khong|đừng|dung|chớ|cho|nếu|neu|if|not|never|unless|ignore|"
    r"bỏ\s+qua|bo\s+qua)\b",
    re.IGNORECASE,
)
_TABLE_CUE = re.compile(
    r"\b(?:table|bảng)\s*[:#]?\s*([A-Za-z_][A-Za-z0-9_]*)\b", re.IGNORECASE
)
_VALUE_CUES: tuple[tuple[ValueType, re.Pattern[str]], ...] = (
    (
        ValueType.GPA,
        re.compile(r"\b(?:gpa|điểm\s+trung\s+bình|diem\s+trung\s+binh)\b", re.I),
    ),
    (
        ValueType.EMAIL,
        re.compile(r"\b(?:email|e-mail|địa\s+chỉ\s+email|dia\s+chi\s+email)\b", re.I),
    ),
    (ValueType.URL, re.compile(r"\b(?:url|endpoint|đường\s+dẫn|duong\s+dan)\b", re.I)),
    (
        ValueType.STUDENT_ID,
        re.compile(
            r"\b(?:student\s*[-_]?id|mã\s+sinh\s+viên|ma\s+sinh\s+vien)\b", re.I
        ),
    ),
    (
        ValueType.COURSE_CODE,
        re.compile(
            r"\b(?:course\s*[-_]?code|mã\s+học\s+phần|ma\s+hoc\s+phan)\b", re.I
        ),
    ),
    (ValueType.PHONE, re.compile(r"\b(?:phone|điện\s+thoại|dien\s+thoai)\b", re.I)),
    (ValueType.MONEY, re.compile(r"\b(?:amount|money|số\s+tiền|so\s+tien)\b", re.I)),
    (ValueType.DATE, re.compile(r"\b(?:date|ngày|ngay)\b", re.I)),
    (
        ValueType.IDENTIFIER,
        re.compile(
            r"\b(?:identifier|record\s*[-_]?id|mã\s+hồ\s+sơ|ma\s+ho\s+so)\b", re.I
        ),
    ),
)


class EntitlementError(ValueError):
    """Sanitized entitlement-integrity error; raw private values are excluded."""


class FinalEntitlement(Immutable):
    profile: str = PROFILE
    resource_ids: tuple[str, ...] = ()
    database_tables: tuple[str, ...] = ()
    value_types: tuple[ValueType, ...] = ()
    explicit: bool = False
    raw_user_sha256: str = Field(min_length=64, max_length=64)


class EntitledFinalRelease(Immutable):
    profile: str = RELEASE_PROFILE
    effect: Effect
    reasons: tuple[Reason, ...] = Field(min_length=1)
    proposed_artifact_id: str
    released_artifact_id: str
    proposed_sha256: str
    released_sha256: str
    index_sha256: str
    entitlement_sha256: str
    matches: tuple[ProtectedMatch, ...] = ()
    authorized_matches: tuple[ProtectedMatch, ...] = ()
    unauthorized_matches: tuple[ProtectedMatch, ...] = ()
    redacted_spans: tuple[tuple[int, int], ...] = ()


def extract_final_entitlement(raw_user: str) -> FinalEntitlement:
    """Extract explicit source/value grants from affirmative raw-user clauses."""

    if not isinstance(raw_user, str) or not raw_user.strip():
        raise EntitlementError("non-empty raw user instruction required")
    if len(raw_user.encode("utf-8")) > MAX_BYTES:
        raise EntitlementError("raw user instruction exceeds entitlement budget")
    resources: set[str] = set()
    tables: set[str] = set()
    value_types: set[ValueType] = set()
    for clause in re.split(r"[\n;.!?]", raw_user):
        if _REJECT_CLAUSE.search(clause) or not _ENTITLEMENT_CUE.search(clause):
            continue
        if any(mark in clause for mark in ('"', "'", "`", "“", "”", ">")):
            continue
        resources.update(_RESOURCE_ID.findall(clause))
        tables.update(match.group(1).casefold() for match in _TABLE_CUE.finditer(clause))
        value_types.update(kind for kind, pattern in _VALUE_CUES if pattern.search(clause))
    total = len(resources) + len(tables) + len(value_types)
    if total > MAX_ENTITLEMENTS:
        raise EntitlementError("entitlement budget exceeded")
    ordered_types = tuple(sorted(value_types, key=lambda value: value.value))
    return FinalEntitlement(
        resource_ids=tuple(sorted(resources)),
        database_tables=tuple(sorted(tables)),
        value_types=ordered_types,
        explicit=bool(resources or tables) and bool(ordered_types),
        raw_user_sha256=text_hash(raw_user),
    )


def _merge_spans(matches: tuple[ProtectedMatch, ...]) -> tuple[tuple[int, int], ...]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted({(m.start, m.end) for m in matches if m.view == "raw_v1"}):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return tuple(merged)


def _raw_user(index: ValueOriginIndex, identity: str) -> Any:
    user = index.store.get(identity)
    if (
        user.artifact_type != ArtifactType.USER_INPUT
        or user.source_type != SourceType.USER
        or user.producer != "host_context"
        or user.parents
        or user.transformations
        or not isinstance(user.content(), str)
    ):
        raise EntitlementError("raw host user root required")
    return user


def _coverage(index: ValueOriginIndex, proposal_id: str, user_id: str) -> bool:
    store = index.store
    proposal = store.get(proposal_id)
    observed = {
        artifact.artifact_id
        for artifact in store.ancestors(proposal_id)
        if not artifact.parents
        and (
            artifact.producer == "tool_source_snapshot"
            or (artifact.source_type == SourceType.USER and artifact.producer == "host_context")
        )
    }
    admitted = set(index.snapshot()["source_sha256"])
    return (
        index.complete
        and user_id in observed
        and observed == admitted
        and proposal.created_step >= index.last_observed_step
    )


def _authorized_origin(
    index: ValueOriginIndex, origin: OriginRecord, entitlement: FinalEntitlement
) -> bool:
    if origin.trust != Trust.TRUSTED or origin.value_type not in entitlement.value_types:
        return False
    artifact = index.store.get(origin.artifact_id)
    source_id = artifact.source_id
    if source_id is None:
        return False
    return source_id in entitlement.resource_ids or source_id.casefold() in set(
        entitlement.database_tables
    )


def release_final_with_entitlement(
    index: ValueOriginIndex,
    proposed_artifact_id: str,
    user_artifact_id: str,
    entitlement: FinalEntitlement,
) -> EntitledFinalRelease:
    """Release a final only when every retained private origin is entitled."""

    store = index.store
    proposed = store.get(proposed_artifact_id)
    user = _raw_user(index, user_artifact_id)
    if text_hash(str(user.content())) != entitlement.raw_user_sha256:
        raise EntitlementError("entitlement is not bound to the raw user")
    if (
        proposed.artifact_type != ArtifactType.FINAL_RESPONSE
        or proposed.source_type != SourceType.MODEL
        or not proposed.parents
        or not isinstance(proposed.content(), str)
        or proposed.created_step < index.last_observed_step
        or user_artifact_id not in {a.artifact_id for a in store.ancestors(proposed_artifact_id)}
    ):
        raise EntitlementError("current final and user ancestry required")
    identity = index.identity
    parent_ids: tuple[str, ...] = (proposed.artifact_id,)
    matches: tuple[ProtectedMatch, ...] = ()
    authorized: tuple[ProtectedMatch, ...] = ()
    unauthorized: tuple[ProtectedMatch, ...] = ()
    removed: tuple[tuple[int, int], ...] = ()
    released = str(proposed.content())
    effect, reason = Effect.ALLOW, Reason.PASS
    try:
        if not _coverage(index, proposed_artifact_id, user_artifact_id):
            raise OriginError("final source coverage incomplete")
        matches = index.protected_matches(released)
        if any(match.view != "raw_v1" for match in matches):
            raise OriginError("normalized-only final match")
        authorized = tuple(
            match for match in matches if _authorized_origin(index, match.origin, entitlement)
        )
        unauthorized = tuple(match for match in matches if match not in authorized)
        removed = _merge_spans(unauthorized)
        for start, end in reversed(removed):
            released = released[:start] + REPLACEMENT + released[end:]
        residual = tuple(
            match
            for match in index.protected_matches(released)
            if not _authorized_origin(index, match.origin, entitlement)
        )
        if residual:
            raise OriginError("unauthorized protected value remains")
        if unauthorized:
            effect, reason = Effect.REDACT, Reason.FINAL_VALUE
        parent_ids = tuple(
            dict.fromkeys((proposed.artifact_id, *(match.origin.artifact_id for match in matches)))
        )
    except OriginError:
        effect, reason, released = Effect.DENY, Reason.UNKNOWN, ""
        parent_ids = tuple(
            dict.fromkeys((proposed.artifact_id, *(match.origin.artifact_id for match in matches)))
        )
    parents = [store.get(identity_) for identity_ in parent_ids]
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
            "effect": effect.value,
            "reason": reason.value,
            "index_sha256": identity,
            "entitlement_sha256": text_hash(entitlement.model_dump_json()),
            "proposed_text_sha256": text_hash(str(proposed.content())),
            "released_text_sha256": text_hash(released),
        },
    )
    return EntitledFinalRelease(
        effect=effect,
        reasons=(reason,),
        proposed_artifact_id=proposed.artifact_id,
        released_artifact_id=artifact.artifact_id,
        proposed_sha256=proposed.content_hash,
        released_sha256=artifact.content_hash,
        index_sha256=identity,
        entitlement_sha256=text_hash(entitlement.model_dump_json()),
        matches=matches,
        authorized_matches=authorized,
        unauthorized_matches=unauthorized,
        redacted_spans=removed,
    )
