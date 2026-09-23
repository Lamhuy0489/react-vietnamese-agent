"""Dated-room policy binding without importing the replay-only v14 runtime."""

from __future__ import annotations

from typing import cast

from react_agent.schemas.agent_output import Action
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.public_field_ticket_policy_v1 import TicketA6Policy
from react_agent.security_v1.public_field_ticket_v2 import PROFILE as TICKET_PROFILE
from react_agent.security_v1.public_field_ticket_v2 import issue_room_ticket, verify_room_egress
from react_agent.security_v1.runtime_policy import RuntimeVerdict
from react_agent.security_v1.value_origin import ValueOriginIndex
from react_agent.tools.registry import ToolRegistry

RUNTIME_VERSION = "security_runtime_v14_dated_room_ablation_v1"


class DatedTicketA6Policy(TicketA6Policy):
    def pre_bound(
        self,
        action: Action,
        proposal_id: str,
        user_id: str,
        index: ValueOriginIndex,
        registry: ToolRegistry,
    ) -> RuntimeVerdict:
        body = bind(
            TicketA6Policy.pre_bound,
            issue_room_ticket=issue_room_ticket,
            verify_room_egress=verify_room_egress,
            TICKET_PROFILE=TICKET_PROFILE,
            RUNTIME_VERSION=RUNTIME_VERSION,
        )
        return cast(RuntimeVerdict, body(self, action, proposal_id, user_id, index, registry))
