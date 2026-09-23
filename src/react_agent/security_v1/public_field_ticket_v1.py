"""Opt-in proof-carrying public-field egress pilot; not an enabled A6 policy.

The host, never the model, issues a ticket from an admitted raw source. A PRE
check recomputes it from immutable artifacts. This narrow pilot admits only a
room code from one public document and one explicit raw-user webhook command.
"""

from __future__ import annotations

import json
import re

from react_agent.foundation.artifacts import (
    Artifact,
    ArtifactType,
    Immutable,
    Sensitivity,
    SourceType,
    canonical_json,
)
from react_agent.foundation.normalization import normalize, text_hash
from react_agent.schemas.agent_output import ActionTurn
from react_agent.schemas.tool import ToolResult
from react_agent.security_v1.authorization_anchors_v3 import extract_anchors
from react_agent.security_v1.contracts import Effect, Reason, SecurityDecision, Stage
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex
from react_agent.tools.registry import ToolRegistry

PROFILE = "public_field_ticket_v1"
ROOM_LINE = re.compile(r"Phòng hiện hành:[ \t]*([A-Z][A-Z0-9_-]{3,31})[ \t]*")
MAX_SCAN_WORK = 8_388_608


class PublicFieldTicket(Immutable):
    profile: str = PROFILE
    run_id: str
    index_sha256: str
    source_artifact_id: str
    source_sha256: str
    source_id: str
    observation_artifact_id: str
    observation_sha256: str
    read_action_artifact_id: str
    read_action_sha256: str
    field: str = "room"
    value_sha256: str


def _room(source: Artifact) -> str:
    content = source.content()
    body = content.get("content") if isinstance(content, dict) else None
    if (
        source.parents
        or source.transformations
        or source.producer != "tool_source_snapshot"
        or source.source_type != SourceType.DOCUMENT
        or source.artifact_type != ArtifactType.DOCUMENT_CONTENT
        or source.sensitivity != Sensitivity.PUBLIC
        or not source.source_id
        or re.fullmatch(r"AUX_[A-Z][A-Z0-9_]{0,63}", source.source_id) is None
        or not isinstance(body, str)
    ):
        raise ValueError("public raw document required for room ticket")
    if len(body.encode("utf-8")) > 32768:
        raise ValueError("room source exceeds bounded profile")
    match = ROOM_LINE.fullmatch(body)
    if match is None:
        raise ValueError("entire content must be one bounded room line")
    return match.group(1)


def issue_room_ticket(
    index: ValueOriginIndex, source_artifact_id: str, observation_artifact_id: str
) -> PublicFieldTicket:
    """Issue from a host-admitted source; metadata approval is an external gate."""
    source = index.store.get(source_artifact_id)
    observation = index.store.get(observation_artifact_id)
    if (
        not index.complete
        or index.snapshot()["source_sha256"].get(source_artifact_id) != source.content_hash
    ):
        raise ValueError("admitted complete source index required")
    value = _room(source)
    if source.source_id is None:
        raise ValueError("host source identity required")
    if (
        observation.artifact_type != ArtifactType.TOOL_RESULT
        or observation.source_type != SourceType.TOOL
        or observation.producer != "record_only_post"
        or observation.transformations
        or source.created_step != observation.created_step
        or len(observation.parents) != 2
        or source.artifact_id not in {p.parent_id for p in observation.parents}
        or not isinstance(observation.content(), str)
    ):
        raise ValueError("exact raw POST observation required")
    read_id = next(p.parent_id for p in observation.parents if p.parent_id != source.artifact_id)
    read_action = index.store.get(read_id)
    if (
        read_action.artifact_type != ArtifactType.MODEL_OUTPUT
        or read_action.source_type != SourceType.MODEL
        or not read_action.parents
        or read_action.transformations
        or read_action.created_step != source.created_step
        or not isinstance(read_action.content(), str)
    ):
        raise ValueError("exact read action parent required")
    parsed = ActionTurn.model_validate_json(str(read_action.content())).action
    if parsed.name != "doc_read" or parsed.arguments != {"doc_id": source.source_id}:
        raise ValueError("read action differs from ticket source")
    result = ToolResult.model_validate_json(str(observation.content()))
    source_metadata = json.loads(source.metadata_json)
    if (
        not result.ok
        or result.tool_name != "doc_read"
        or canonical_json(result.content) != canonical_json(source.content())
        or source_metadata.get("call_id") != result.call_id
        or source_metadata.get("tool") != "doc_read"
        or source_metadata.get("ok") is not True
    ):
        raise ValueError("POST result differs from ticket source")
    return PublicFieldTicket(
        run_id=index.store.run_id,
        index_sha256=index.identity,
        source_artifact_id=source.artifact_id,
        source_sha256=source.content_hash,
        source_id=source.source_id,
        observation_artifact_id=observation.artifact_id,
        observation_sha256=observation.content_hash,
        read_action_artifact_id=read_action.artifact_id,
        read_action_sha256=read_action.content_hash,
        value_sha256=text_hash(value),
    )


def _decision(effect: Effect, reason: Reason, *artifacts: str) -> SecurityDecision:
    return SecurityDecision(
        stage=Stage.PRE,
        effect=effect,
        reasons=(reason,),
        related_artifact_ids=tuple(dict.fromkeys(artifacts)),
        component=PROFILE,
    )


def verify_room_egress(
    index: ValueOriginIndex,
    ticket: PublicFieldTicket,
    user_artifact_id: str,
    proposal_artifact_id: str,
    registry: ToolRegistry,
) -> SecurityDecision:
    """Component-level PRE verdict; A1–A6 and Broker are still mandatory."""
    store = index.store
    if ticket.profile != PROFILE or ticket.field != "room" or ticket.run_id != store.run_id:
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, proposal_artifact_id)
    try:
        source = store.get(ticket.source_artifact_id)
        observation = store.get(ticket.observation_artifact_id)
        read_action = store.get(ticket.read_action_artifact_id)
        user = store.get(user_artifact_id)
        proposal = store.get(proposal_artifact_id)
        expected = issue_room_ticket(index, source.artifact_id, observation.artifact_id)
    except (KeyError, ValueError):
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, proposal_artifact_id)
    if ticket != expected or ticket.index_sha256 != index.identity:
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, proposal_artifact_id)
    if (
        user.artifact_type != ArtifactType.USER_INPUT
        or user.source_type != SourceType.USER
        or user.producer != "host_context"
        or user.parents
        or user.transformations
        or user.sensitivity != Sensitivity.PUBLIC
        or not isinstance(user.content(), str)
        or proposal.artifact_type != ArtifactType.MODEL_OUTPUT
        or proposal.source_type != SourceType.MODEL
        or not proposal.parents
        or proposal.transformations
        or proposal.created_step < index.last_observed_step
        or not isinstance(proposal.content(), str)
    ):
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, proposal_artifact_id)
    ancestors = {a.artifact_id for a in store.ancestors(proposal_artifact_id)}
    admitted = set(index.snapshot()["source_sha256"])
    roots = {
        a.artifact_id
        for a in store.ancestors(proposal_artifact_id)
        if not a.parents
        and (a.producer == "tool_source_snapshot" or a.source_type == SourceType.USER)
    }
    if (
        {
            user_artifact_id,
            source.artifact_id,
            observation.artifact_id,
            read_action.artifact_id,
        }
        - ancestors
        or roots != admitted
        or admitted - ancestors
    ):
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, proposal_artifact_id)
    try:
        action = ActionTurn.model_validate_json(str(proposal.content())).action
    except ValueError:
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, proposal_artifact_id)
    if action.name != "post_webhook_mock" or set(action.arguments) != {"endpoint", "payload"}:
        return _decision(Effect.DENY, Reason.ACTION, proposal_artifact_id)
    endpoint, payload = action.arguments["endpoint"], action.arguments["payload"]
    if (
        not isinstance(endpoint, str)
        or not isinstance(payload, dict)
        or set(payload) != {"room"}
        or not isinstance(payload["room"], str)
    ):
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, proposal_artifact_id)
    tool = registry.get(action.name)
    if tool is None:
        return _decision(Effect.DENY, Reason.ACTION, proposal_artifact_id)
    try:
        validated = tool.input_model.model_validate(action.arguments, strict=True)
        if canonical_json(validated.model_dump(mode="json", exclude_unset=True)) != canonical_json(
            action.arguments
        ):
            raise ValueError("tool arguments changed during validation")
    except ValueError:
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, proposal_artifact_id)
    raw_user = str(user.content())
    documents = [
        store.get(identity)
        for identity in admitted - {user_artifact_id}
        if store.get(identity).producer == "tool_source_snapshot"
    ]
    if not documents or any(
        item.source_type != SourceType.DOCUMENT or item.source_id is None for item in documents
    ):
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, user_artifact_id)
    names = [item.source_id for item in documents if item.source_id is not None]
    if len(names) != len(set(names)):
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, user_artifact_id)
    grant = f"Đọc {' và '.join(sorted(names))}. Post webhook to {endpoint} payload room."
    if raw_user != grant or not extract_anchors(raw_user).authorizes(action):
        return _decision(Effect.DENY, Reason.DESTINATION, user_artifact_id)
    value = _room(source)
    if payload["room"] != value or text_hash(value) != ticket.value_sha256:
        return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, source.artifact_id)
    # A value that occurs anywhere in an admitted sensitive source cannot be
    # treated as exclusively public, even when the public document also has it.
    work = 0
    for identity in admitted - {user_artifact_id, source.artifact_id}:
        other = store.get(identity)
        if other.sensitivity == Sensitivity.PUBLIC:
            continue
        raw = canonical_json(other.content())
        work += len(raw) + len(value)
        if work > MAX_SCAN_WORK:
            return _decision(Effect.DENY, Reason.UNKNOWN_FIELD, identity)
        if (
            value in raw
            or normalize(value, "security_v1").normalized_text
            in normalize(raw, "security_v1").normalized_text
        ):
            return _decision(Effect.DENY, Reason.SENSITIVE_PAYLOAD, identity)
    return _decision(
        Effect.ALLOW, Reason.PASS, user.artifact_id, source.artifact_id, proposal.artifact_id
    )
