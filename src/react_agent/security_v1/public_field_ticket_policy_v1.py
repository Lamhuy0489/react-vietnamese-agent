"""A6 public-field ticket policy without CPU-only replay dependencies."""

from __future__ import annotations

from typing import cast

from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import Effect, Reason
from react_agent.security_v1.public_field_ticket_v1 import PROFILE as TICKET_PROFILE
from react_agent.security_v1.public_field_ticket_v1 import issue_room_ticket, verify_room_egress
from react_agent.security_v1.runtime_policy import RuntimeVerdict
from react_agent.security_v1.runtime_v12 import ClauseA6Policy
from react_agent.security_v1.value_gates import ValuePreDecision
from react_agent.security_v1.value_origin import ValueOriginIndex
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex as HostIndex
from react_agent.tools.registry import ToolRegistry

RUNTIME_VERSION = "security_runtime_v13_ticket_ablation_v1"
COARSE_DISCHARGE = frozenset(
    {Reason.PASS.value, Reason.CLEARANCE.value, Reason.SESSION_SENSITIVITY.value}
)


class TicketA6Policy(ClauseA6Policy):
    def pre_bound(
        self,
        action: Action,
        proposal_id: str,
        user_id: str,
        index: ValueOriginIndex,
        registry: ToolRegistry,
    ) -> RuntimeVerdict:
        baseline = cast(
            RuntimeVerdict,
            super().pre_bound(action, proposal_id, user_id, index, registry),
        )
        if (
            action.name != "post_webhook_mock"
            or baseline.effect != Effect.DENY
            or not isinstance(index, HostIndex)
        ):
            return baseline
        record = self.value_records[-1]
        coarse = RuntimeVerdict.model_validate(record["coarse"])
        value = ValuePreDecision.model_validate(record["value"])
        coarse_reasons = set(coarse.reasons)
        explained_coarse = (
            (coarse.effect == Effect.ALLOW and coarse_reasons == {Reason.PASS.value})
            or (
                coarse.effect == Effect.DENY
                and bool(
                    coarse_reasons & {Reason.CLEARANCE.value, Reason.SESSION_SENSITIVITY.value}
                )
                and coarse_reasons <= COARSE_DISCHARGE
            )
        )
        if (
            value.effect != Effect.DENY
            or set(value.reasons) != {Reason.UNKNOWN_FIELD}
            or not explained_coarse
        ):
            return baseline
        ancestors = index.store.ancestors(proposal_id)
        observations = tuple(a for a in ancestors if a.producer == "record_only_post")
        admitted = set(index.snapshot()["source_sha256"])
        proven = []
        for source in ancestors:
            if source.artifact_id not in admitted or source.producer != "tool_source_snapshot":
                continue
            for observation in observations:
                if source.artifact_id not in {p.parent_id for p in observation.parents}:
                    continue
                try:
                    ticket = issue_room_ticket(index, source.artifact_id, observation.artifact_id)
                    decision = verify_room_egress(index, ticket, user_id, proposal_id, registry)
                except ValueError:
                    continue
                if decision.effect == Effect.ALLOW:
                    proven.append((ticket, decision))
        record["ticket_ablation"] = {
            "profile": TICKET_PROFILE,
            "eligible_proof_count": len(proven),
            "effect": Effect.ALLOW.value if len(proven) == 1 else Effect.DENY.value,
        }
        if len(proven) != 1:
            return baseline
        ticket, decision = proven[0]
        result = RuntimeVerdict(
            stage=baseline.stage,
            effect=Effect.ALLOW,
            reasons=(Reason.PASS.value,),
            related_artifact_ids=tuple(
                dict.fromkeys((*baseline.related_artifact_ids, *decision.related_artifact_ids))
            ),
            component=RUNTIME_VERSION,
        )
        record["baseline_composed"] = record["composed"]
        record["composed"] = result.model_dump(mode="json")
        record["ticket_ablation"].update(
            source_artifact_id=ticket.source_artifact_id,
            observation_artifact_id=ticket.observation_artifact_id,
            index_sha256=ticket.index_sha256,
            value_sha256=ticket.value_sha256,
        )
        return result
