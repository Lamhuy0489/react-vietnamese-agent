"""Deterministic final-value release component, not an enabled A6 runtime gate."""

from __future__ import annotations

from react_agent.foundation.artifacts import (
    ArtifactType,
    Immutable,
    ParentLink,
    Relation,
    Sensitivity,
    SourceType,
    join_sensitivity,
    join_trust,
)
from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.contracts import Effect, Reason
from react_agent.security_v1.value_origin import OriginError, ProtectedMatch, ValueOriginIndex

REPLACEMENT = "[REDACTED]"


class FinalValueRelease(Immutable):
    profile: str = "final_value_release_v1"
    effect: Effect
    reasons: tuple[Reason, ...]
    proposed_artifact_id: str
    released_artifact_id: str
    proposed_sha256: str
    released_sha256: str
    index_sha256: str
    matches: tuple[ProtectedMatch, ...] = ()
    redacted_spans: tuple[tuple[int, int], ...] = ()


def merge_spans(matches: tuple[ProtectedMatch, ...]) -> tuple[tuple[int, int], ...]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted({(m.start, m.end) for m in matches if m.view == "raw_v1"}):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return tuple(merged)


def release_final(index: ValueOriginIndex, proposed_artifact_id: str) -> FinalValueRelease:
    store = index.store
    proposed = store.get(proposed_artifact_id)
    content = proposed.content()
    if (
        proposed.artifact_type != ArtifactType.FINAL_RESPONSE
        or proposed.source_type != SourceType.MODEL
        or not proposed.parents
        or not isinstance(content, str)
        or proposed.producer == "final_value_release_v1"
        or proposed.created_step < index.last_observed_step
    ):
        raise ValueError("current proposed final string required")
    identity = index.identity
    matches: tuple[ProtectedMatch, ...] = ()
    removed: tuple[tuple[int, int], ...] = ()
    released = content
    effect, reason = Effect.ALLOW, Reason.PASS
    try:
        matches = index.protected_matches(content)
        if any(m.view != "raw_v1" for m in matches):
            # No raw span mapping: never redact using normalized offsets.
            effect, reason, released = Effect.DENY, Reason.FINAL_VALUE, ""
        elif matches:
            removed = merge_spans(matches)
            for start, end in reversed(removed):
                released = released[:start] + REPLACEMENT + released[end:]
            if index.protected_matches(released):
                effect, reason, released = Effect.DENY, Reason.FINAL_VALUE, ""
            else:
                effect, reason = Effect.REDACT, Reason.FINAL_VALUE
    except OriginError:
        effect, reason, released = Effect.DENY, Reason.UNKNOWN, ""
    parent_ids = tuple(
        dict.fromkeys((proposed.artifact_id, *(m.origin.artifact_id for m in matches)))
    )
    parents = [store.get(p) for p in parent_ids]
    artifact = store.create(
        released,
        artifact_type=ArtifactType.FINAL_RESPONSE,
        source_type=SourceType.SYSTEM,
        source_id=proposed.artifact_id,
        producer="final_value_release_v1",
        created_step=proposed.created_step,
        sensitivity=join_sensitivity(Sensitivity.PUBLIC, *(p.sensitivity for p in parents)),
        trust=join_trust(*(p.trust for p in parents)),
        parents=tuple(ParentLink(parent_id=p, relation=Relation.DERIVED_FROM) for p in parent_ids),
        transformations=("final_value_release_v1",),
        metadata={
            "effect": effect.value,
            "reason": reason.value,
            "index_sha256": identity,
            "proposed_text_sha256": text_hash(content),
            "released_text_sha256": text_hash(released),
        },
    )
    return FinalValueRelease(
        effect=effect,
        reasons=(reason,),
        proposed_artifact_id=proposed.artifact_id,
        released_artifact_id=artifact.artifact_id,
        proposed_sha256=proposed.content_hash,
        released_sha256=artifact.content_hash,
        index_sha256=identity,
        matches=matches,
        redacted_spans=removed,
    )
