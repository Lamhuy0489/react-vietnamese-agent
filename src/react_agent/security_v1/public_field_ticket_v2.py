"""Opt-in, bounded dated-room grammar over the v1 proof-carrying ticket."""

from __future__ import annotations

import re
from datetime import date
from typing import Literal, cast

from react_agent.foundation.artifacts import Artifact
from react_agent.security_v1.contracts import SecurityDecision
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.public_field_ticket_v1 import PublicFieldTicket
from react_agent.security_v1.public_field_ticket_v1 import _decision as v1_decision
from react_agent.security_v1.public_field_ticket_v1 import _room as v1_room
from react_agent.security_v1.public_field_ticket_v1 import issue_room_ticket as v1_issue
from react_agent.security_v1.public_field_ticket_v1 import verify_room_egress as v1_verify
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex
from react_agent.tools.registry import ToolRegistry

PROFILE: Literal["public_field_ticket_v2_dated_room"] = "public_field_ticket_v2_dated_room"
ROOM_LINE = re.compile(
    r"Phòng hiện hành:[ \t]*([A-Z][A-Z0-9_-]{3,31})[ \t]*"
    r"(?:\nCập nhật:[ \t]*([0-9]{4}-[0-9]{2}-[0-9]{2})[ \t]*)?"
)


class DatedRoomTicket(PublicFieldTicket):
    profile: Literal["public_field_ticket_v2_dated_room"] = PROFILE


def _room(source: Artifact) -> str:
    # Reuse every v1 artifact/source/bounds check; substitute only the grammar.
    value = cast(str, bind(v1_room, ROOM_LINE=ROOM_LINE)(source))
    content = source.content()
    if not isinstance(content, dict):
        raise ValueError("dated room content must be a string")
    body = content.get("content")
    if not isinstance(body, str):
        raise ValueError("dated room content must be a string")
    match = ROOM_LINE.fullmatch(body)
    if match is None:
        raise ValueError("dated room grammar mismatch")
    stamp = match.group(2)
    if stamp is not None:
        try:
            date.fromisoformat(stamp)
        except ValueError as exc:
            raise ValueError("invalid room update date") from exc
    return value


def issue_room_ticket(
    index: ValueOriginIndex, source_artifact_id: str, observation_artifact_id: str
) -> DatedRoomTicket:
    body = bind(v1_issue, _room=_room, PublicFieldTicket=DatedRoomTicket)
    return cast(DatedRoomTicket, body(index, source_artifact_id, observation_artifact_id))


def verify_room_egress(
    index: ValueOriginIndex,
    ticket: DatedRoomTicket,
    user_artifact_id: str,
    proposal_artifact_id: str,
    registry: ToolRegistry,
) -> SecurityDecision:
    decision = bind(v1_decision, PROFILE=PROFILE)
    body = bind(
        v1_verify,
        PROFILE=PROFILE,
        issue_room_ticket=issue_room_ticket,
        _room=_room,
        _decision=decision,
    )
    return cast(
        SecurityDecision,
        body(index, ticket, user_artifact_id, proposal_artifact_id, registry),
    )
