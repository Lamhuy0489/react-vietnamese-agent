"""Clause-bound final grants and complete raw/normalized residual screening.

Version 1 remains frozen for reproduction, not recommended for new runs.
No evaluator grants or model-produced authorizations enter this component.
"""

from __future__ import annotations

import re
from typing import Literal, cast

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
from react_agent.security_v1.final_entitlements import (
    _ENTITLEMENT_CUE,
    _REJECT_CLAUSE,
    _RESOURCE_ID,
    _TABLE_CUE,
    _VALUE_CUES,
    MAX_ENTITLEMENTS,
    REPLACEMENT,
    EntitledFinalRelease,
    EntitlementError,
    _coverage,
    _merge_spans,
    _raw_user,
)
from react_agent.security_v1.value_origin import (
    MAX_BYTES,
    OriginError,
    OriginRecord,
    ProtectedMatch,
    ValueOriginIndex,
    ValueType,
)

PROFILE: Literal["final_entitlement_v2"] = "final_entitlement_v2"
RELEASE_PROFILE = "final_entitlement_release_v2"
GrantSource = Literal[SourceType.DOCUMENT, SourceType.CACHED_PAGE, SourceType.DATABASE]


class SourceValueGrant(Immutable):
    source_type: GrantSource
    source_id: str = Field(min_length=1, max_length=64)
    value_type: ValueType


class FinalEntitlement(Immutable):
    profile: Literal["final_entitlement_v2"] = PROFILE
    grants: tuple[SourceValueGrant, ...] = Field(default=(), max_length=MAX_ENTITLEMENTS)
    explicit: bool = False
    raw_user_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def extract_final_entitlement(raw_user: str) -> FinalEntitlement:
    """Only one unambiguous source per affirmative clause can receive grants.

    Multiple types may be granted for that source. Multi-source clauses and
    quoted instructions fail closed rather than guessing a language parse.
    """
    if not isinstance(raw_user, str) or not raw_user.strip():
        raise EntitlementError("non-empty raw user instruction required")
    if len(raw_user.encode("utf-8")) > MAX_BYTES:
        raise EntitlementError("raw user instruction exceeds entitlement budget")
    grants: dict[tuple[str, str, str], SourceValueGrant] = {}
    # Reject at document level: splitting must not escape multiline quotes.
    clauses = (
        []
        if any(c in raw_user for c in ('"', "'", "`", "“", "”", ">"))
        else re.split(r"[\n;.!?]", raw_user)
    )
    for clause in clauses:
        if _REJECT_CLAUSE.search(clause) or not _ENTITLEMENT_CUE.search(clause):
            continue
        sources: set[tuple[SourceType, str]] = {
            (SourceType.DOCUMENT if name.startswith("DOC_") else SourceType.CACHED_PAGE, name)
            for name in _RESOURCE_ID.findall(_TABLE_CUE.sub("", clause))
        }
        sources.update(
            (SourceType.DATABASE, match.group(1).casefold())
            for match in _TABLE_CUE.finditer(clause)
        )
        if len(sources) != 1:
            continue
        source_type, source_id = next(iter(sources))
        if len(source_id) > 64:
            continue
        for kind, pattern in _VALUE_CUES:
            if pattern.search(clause):
                grant = SourceValueGrant(
                    source_type=cast(GrantSource, source_type), source_id=source_id, value_type=kind
                )
                grants[(source_type.value, source_id, kind.value)] = grant
        if len(grants) > MAX_ENTITLEMENTS:
            raise EntitlementError("entitlement budget exceeded")
    return FinalEntitlement(
        grants=tuple(grants[key] for key in sorted(grants)),
        explicit=bool(grants),
        raw_user_sha256=text_hash(raw_user),
    )


def validate_entitlement(raw_user: str, entitlement: FinalEntitlement) -> None:
    """Hash binding alone is not authorization; require canonical extraction."""
    if not isinstance(entitlement, FinalEntitlement) or (
        entitlement.model_dump() != extract_final_entitlement(raw_user).model_dump()
    ):
        raise EntitlementError("entitlement is not canonically bound to the raw user")


def strict_protected_matches(index: ValueOriginIndex, text: str) -> tuple[ProtectedMatch, ...]:
    matches = index.protected_matches(text)
    # Screening only: mask ALL exact occurrences, including authorized ones.
    # Keep length/word separation, so a raw occurrence cannot hide an encoded
    # copy of the same origin from the frozen index's normalized fallback.
    residual = text
    for start, end in reversed(_merge_spans(matches)):
        residual = residual[:start] + " " * (end - start) + residual[end:]
    if residual != text and index.protected_matches(residual):
        raise OriginError("protected value remains outside exact raw spans")
    if any(match.view != "raw_v1" for match in matches):
        raise OriginError("normalized-only final match")
    return matches


def authorized_origin(
    index: ValueOriginIndex, origin: OriginRecord, entitlement: FinalEntitlement
) -> bool:
    if not entitlement.explicit or origin.trust != Trust.TRUSTED:
        return False
    artifact = index.store.get(origin.artifact_id)
    identity = artifact.source_id
    if identity is None:
        return False
    if artifact.source_type == SourceType.DATABASE:
        identity = identity.casefold()
    return any(
        (grant.source_type, grant.source_id, grant.value_type)
        == (artifact.source_type, identity, origin.value_type)
        for grant in entitlement.grants
    )


def release_final_with_entitlement(
    index: ValueOriginIndex,
    proposed_artifact_id: str,
    user_artifact_id: str,
    entitlement: FinalEntitlement,
) -> EntitledFinalRelease:
    store = index.store
    proposed = store.get(proposed_artifact_id)
    user = _raw_user(index, user_artifact_id)
    validate_entitlement(str(user.content()), entitlement)
    if (
        proposed.artifact_type != ArtifactType.FINAL_RESPONSE
        or proposed.source_type != SourceType.MODEL
        or not proposed.parents
        or not isinstance(proposed.content(), str)
        or proposed.created_step < index.last_observed_step
        or user_artifact_id not in {a.artifact_id for a in store.ancestors(proposed_artifact_id)}
    ):
        raise EntitlementError("current final and user ancestry required")
    matches: tuple[ProtectedMatch, ...] = ()
    authorized: tuple[ProtectedMatch, ...] = ()
    unauthorized: tuple[ProtectedMatch, ...] = ()
    removed: tuple[tuple[int, int], ...] = ()
    released = str(proposed.content())
    effect, reason = Effect.ALLOW, Reason.PASS
    try:
        if not _coverage(index, proposed_artifact_id, user_artifact_id):
            raise OriginError("final source coverage incomplete")
        matches = strict_protected_matches(index, released)
        authorized = tuple(m for m in matches if authorized_origin(index, m.origin, entitlement))
        unauthorized = tuple(m for m in matches if m not in authorized)
        removed = _merge_spans(unauthorized)
        for start, end in reversed(removed):
            released = released[:start] + REPLACEMENT + released[end:]
        residual = strict_protected_matches(index, released)
        if any(not authorized_origin(index, m.origin, entitlement) for m in residual):
            raise OriginError("unauthorized protected value remains")
        if unauthorized:
            effect, reason = Effect.REDACT, Reason.FINAL_VALUE
    except OriginError:
        effect, reason, released = Effect.DENY, Reason.UNKNOWN, ""
    parent_ids = tuple(
        dict.fromkeys((proposed.artifact_id, *(m.origin.artifact_id for m in matches)))
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
        sensitivity=join_sensitivity(*(p.sensitivity for p in parents)),
        trust=join_trust(*(p.trust for p in parents)),
        parents=tuple(
            ParentLink(parent_id=p.artifact_id, relation=Relation.DERIVED_FROM) for p in parents
        ),
        transformations=(RELEASE_PROFILE,),
        metadata={
            "effect": effect.value,
            "reason": reason.value,
            "index_sha256": index.identity,
            "entitlement_sha256": entitlement_hash,
        },
    )
    return EntitledFinalRelease(
        profile=RELEASE_PROFILE,
        effect=effect,
        reasons=(reason,),
        proposed_artifact_id=proposed.artifact_id,
        released_artifact_id=artifact.artifact_id,
        proposed_sha256=proposed.content_hash,
        released_sha256=artifact.content_hash,
        index_sha256=index.identity,
        entitlement_sha256=entitlement_hash,
        matches=matches,
        authorized_matches=authorized,
        unauthorized_matches=unauthorized,
        redacted_spans=removed,
    )
