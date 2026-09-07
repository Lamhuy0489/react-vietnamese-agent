"""Host-bound A6 value gate and explicit data views; not a complete runtime policy."""

from __future__ import annotations

import json
from typing import Any

from react_agent.foundation.artifacts import (
    Artifact,
    ArtifactStore,
    ArtifactType,
    Immutable,
    ParentLink,
    Relation,
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
)
from react_agent.schemas.agent_output import ActionTurn
from react_agent.security_v1.contracts import EXTERNAL, Effect, Reason
from react_agent.security_v1.rules import extract_anchors
from react_agent.security_v1.value_origin import (
    FIELDS,
    MAX_BYTES,
    OriginError,
    OriginRecord,
    ProtectedMatch,
    ValueOriginIndex,
    ValueType,
    canonical_value,
)
from react_agent.tools.registry import ToolRegistry

READ_TOOLS = frozenset(
    {"doc_search", "doc_read", "db_query", "cached_search", "cached_fetch", "calculator"}
)
PAYLOAD_KEYS = frozenset({"message", "content", "text", "data", "items", *FIELDS})
MAX_LEAVES = 256
MAX_DEPTH = 16


class FieldOrigin(Immutable):
    pointer: str
    value_sha256: str
    origins: tuple[OriginRecord, ...] = ()


class ValuePreDecision(Immutable):
    profile: str = "value_pre_gate_v1"
    effect: Effect
    reasons: tuple[Reason, ...]
    proposal_artifact_id: str
    proposal_sha256: str
    user_artifact_id: str
    user_sha256: str
    index_sha256: str
    related_artifact_ids: tuple[str, ...] = ()
    fields: tuple[FieldOrigin, ...] = ()
    protected_matches: tuple[ProtectedMatch, ...] = ()


def _user(store: ArtifactStore, identity: str) -> Artifact:
    value = store.get(identity)
    if (
        value.artifact_type != ArtifactType.USER_INPUT
        or value.source_type != SourceType.USER
        or value.producer != "host_context"
        or value.parents
        or value.transformations
        or not isinstance(value.content(), str)
    ):
        raise ValueError("raw host user root required")
    return value


def _leaves(value: Any, pointer: str, key: str, depth: int = 0) -> list[tuple[str, str, object]]:
    if depth > MAX_DEPTH:
        raise OriginError("payload nesting exceeds profile")
    if isinstance(value, dict):
        if not value or not all(k in PAYLOAD_KEYS for k in value):
            raise OriginError("empty or unsupported payload structure")
        rows = [
            leaf for k, v in value.items() for leaf in _leaves(v, pointer + "/" + k, k, depth + 1)
        ]
    elif isinstance(value, list):
        if not value:
            raise OriginError("empty critical container")
        rows = [
            leaf
            for i, v in enumerate(value)
            for leaf in _leaves(v, pointer + "/" + str(i), key, depth + 1)
        ]
    else:
        rows = [(pointer, key, value)]
    if len(rows) > MAX_LEAVES:
        raise OriginError("payload leaf count exceeds profile")
    return rows


def _origins(index: ValueOriginIndex, value: object, key: str) -> tuple[OriginRecord, ...]:
    kinds: tuple[ValueType, ...]
    if key in {"to", "endpoint"}:
        kinds = (ValueType.EMAIL if key == "to" else ValueType.URL,)
    elif isinstance(value, str):
        kinds = tuple(k for k in ValueType if k not in {ValueType.GPA, ValueType.MONEY})
        if key.casefold() in FIELDS:
            kinds = tuple(dict.fromkeys((*kinds, FIELDS[key.casefold()])))
    elif not isinstance(value, bool) and key.casefold() in FIELDS:
        kinds = (FIELDS[key.casefold()],)
    else:
        return ()
    records: list[OriginRecord] = []
    for kind in kinds:
        try:
            canonical_value(value, kind)
        except ValueError:
            continue
        records.extend(index.find_origins(value, kind).origins)
    return tuple(records)


def value_pre_check(
    index: ValueOriginIndex,
    proposal_artifact_id: str,
    user_artifact_id: str,
    registry: ToolRegistry,
) -> ValuePreDecision:
    from react_agent.foundation.normalization import text_hash

    store = index.store
    user = _user(store, user_artifact_id)
    proposal = store.get(proposal_artifact_id)
    if (
        proposal.artifact_type != ArtifactType.MODEL_OUTPUT
        or proposal.source_type != SourceType.MODEL
        or not proposal.parents
        or proposal.transformations
        or proposal.created_step < index.last_observed_step
    ):
        raise ValueError("current raw derived model action artifact required")
    ancestors = {a.artifact_id for a in store.ancestors(proposal_artifact_id)}
    if user.artifact_id not in ancestors:
        raise ValueError("proposal does not descend from the raw user")
    content = proposal.content()
    if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_BYTES:
        raise ValueError("bounded raw ActionTurn text required")
    action = ActionTurn.model_validate_json(content).action
    tool = registry.get(action.name)
    if tool is None or action.name not in EXTERNAL | READ_TOOLS:
        raise ValueError("unknown fixed tool")
    validated = tool.input_model.model_validate(action.arguments, strict=True)
    if canonical_json(validated.model_dump(mode="json", exclude_unset=True)) != canonical_json(
        action.arguments
    ):
        raise ValueError("tool validation must not transform proposed arguments")
    reasons: list[Reason] = []
    fields = []
    matches: tuple[ProtectedMatch, ...] = ()
    if action.name in EXTERNAL:
        try:
            if not index.complete:
                raise OriginError("incomplete origin evidence")
            admitted = set(index.snapshot()["source_sha256"])
            if not admitted <= ancestors:
                raise OriginError("index includes unexposed source")
            observed_roots = {
                a.artifact_id
                for a in store.ancestors(proposal_artifact_id)
                if not a.parents
                and (a.producer == "tool_source_snapshot" or a.source_type == SourceType.USER)
            }
            if not observed_roots <= admitted:
                raise OriginError("observed source missing from index")
            authorized = extract_anchors(str(user.content())).authorizes(action)
            if not authorized:
                reasons.extend((Reason.ACTION, Reason.DESTINATION))
            # Include JSON keys before structural traversal can reject them.
            matches = index.protected_matches(canonical_json(action.arguments))
            if matches:
                reasons.append(Reason.SENSITIVE_PAYLOAD)
            leaves = []
            for key, value in action.arguments.items():
                if key == "payload":
                    leaves.extend(_leaves(value, "/payload", key))
                else:
                    leaves.append(("/" + key, key, value))
            if len(leaves) > MAX_LEAVES:
                raise OriginError("critical field budget exceeded")
            for pointer, key, value in leaves:
                origins = _origins(index, value, key)
                fields.append(
                    FieldOrigin(
                        pointer=pointer,
                        value_sha256=text_hash(canonical_json(value)),
                        origins=origins,
                    )
                )
                if not origins:
                    reasons.append(Reason.UNKNOWN_FIELD)
                if any(o.sensitivity != Sensitivity.PUBLIC for o in origins):
                    reasons.append(Reason.SENSITIVE_PAYLOAD)
                if (
                    key in {"to", "endpoint"}
                    and not authorized
                    and any(o.trust == Trust.UNTRUSTED for o in origins)
                ):
                    reasons.append(Reason.UNTRUSTED_DESTINATION)
        except OriginError:
            reasons.append(Reason.UNKNOWN_FIELD)
    related = tuple(
        dict.fromkeys(
            (
                user.artifact_id,
                *(o.artifact_id for f in fields for o in f.origins),
                *(m.origin.artifact_id for m in matches),
            )
        )
    )
    return ValuePreDecision(
        effect=Effect.DENY if reasons else Effect.ALLOW,
        reasons=tuple(dict.fromkeys(reasons)) or (Reason.PASS,),
        proposal_artifact_id=proposal.artifact_id,
        proposal_sha256=proposal.content_hash,
        user_artifact_id=user.artifact_id,
        user_sha256=user.content_hash,
        index_sha256=index.identity,
        fields=tuple(fields),
        protected_matches=matches,
        related_artifact_ids=related,
    )


def post_data_view(store: ArtifactStore, source_id: str, observation_id: str) -> Artifact:
    source, observation = store.get(source_id), store.get(observation_id)
    if (
        source.parents
        or source.transformations
        or source.producer != "tool_source_snapshot"
        or source.source_type in {SourceType.USER, SourceType.SYSTEM, SourceType.MODEL}
        or source.artifact_type
        in {
            ArtifactType.MODEL_OUTPUT,
            ArtifactType.FINAL_RESPONSE,
            ArtifactType.TOOL_ARGUMENT,
            ArtifactType.NORMALIZED_VIEW,
        }
        or observation.artifact_type != ArtifactType.TOOL_RESULT
        or observation.producer != "record_only_post"
        or observation.transformations
        or source_id not in {p.parent_id for p in observation.parents}
        or source.created_step != observation.created_step
    ):
        raise ValueError("host source and exact raw tool observation required")
    if not isinstance(observation.content(), str):
        raise ValueError("raw serialized ToolResult required")
    # Validate the content/source binding, not just an arbitrary caller-provided edge.
    from react_agent.schemas.tool import ToolResult

    result = ToolResult.model_validate_json(str(observation.content()))
    expected = result.content if result.ok else result.model_dump(mode="json")
    if canonical_json(source.content()) != canonical_json(expected):
        raise ValueError("tool observation content differs from source snapshot")
    if source.trust == Trust.TRUSTED:
        return observation
    envelope = canonical_json(
        {
            "representation": "untrusted_data_view_v1",
            "trust": "UNTRUSTED",
            "source_artifact_id": source_id,
            "data": json.loads(str(observation.content())),
        }
    )
    return store.create(
        envelope,
        artifact_type=ArtifactType.TOOL_RESULT,
        source_type=SourceType.TOOL,
        source_id=source_id,
        producer="untrusted_data_view_v1",
        created_step=observation.created_step,
        sensitivity=observation.sensitivity,
        trust=observation.trust,
        parents=(ParentLink(parent_id=observation.artifact_id, relation=Relation.DERIVED_FROM),),
        transformations=("untrusted_data_view_v1",),
    )
