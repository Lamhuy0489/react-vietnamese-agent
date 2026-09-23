"""Opt-in synthetic A6 dated-room ablation; v12/v13 policies remain unchanged."""

from __future__ import annotations

from typing import Any, cast

from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.public_field_ticket_policy_v2 import (
    RUNTIME_VERSION,
    DatedTicketA6Policy,
)
from react_agent.security_v1.public_field_ticket_v2 import PROFILE as TICKET_PROFILE
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v13_ticket_v1 import SecurityRuntime as V13Runtime


class SecurityRuntime(V13Runtime):
    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        body = bind(
            V13Runtime._run_task,
            TicketA6Policy=DatedTicketA6Policy,
            TICKET_PROFILE=TICKET_PROFILE,
            RUNTIME_VERSION=RUNTIME_VERSION,
        )
        return cast(SecurityRun, body(self, task, **kwargs))
