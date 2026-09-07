"""Host-bound composition; preserve A5 vetoes except proven unrelated sensitivity."""

from __future__ import annotations

from typing import Any

from react_agent.foundation.artifacts import (
    ArtifactType,
    Sensitivity,
    SourceType,
)
from react_agent.foundation.runtime_hooks import derive
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import Effect, Reason, SecurityConfig, Stage, configuration
from react_agent.security_v1.guard import ModelGuard
from react_agent.security_v1.runtime_policy import RuntimeVerdict
from react_agent.security_v1.session_policy import SessionPolicy
from react_agent.security_v1.value_gates import value_pre_check
from react_agent.security_v1.value_origin import OriginError, ValueOriginIndex
from react_agent.security_v1.value_release import FinalValueRelease, release_final
from react_agent.tools.registry import ToolRegistry

COARSE_SENSITIVITY = frozenset({Reason.CLEARANCE.value, Reason.SESSION_SENSITIVITY.value})
FINAL_POLICY = "a6_public_final_v1"


class A6Policy(SessionPolicy):
    def __init__(self, config: SecurityConfig, raw_user: str, guard: ModelGuard) -> None:
        if config.level != "A6":
            raise ValueError("A6 config required")
        super().__init__(configuration("A5"), raw_user, guard)
        self.security = config
        self.value_records: list[dict[str, Any]] = []

    def pre(self, action: Action) -> RuntimeVerdict:
        raise ValueError("A6 requires pre_bound with host origin evidence")

    def pre_with_artifact(self, action: Action, artifact_id: str | None) -> RuntimeVerdict:
        raise ValueError("A6 requires pre_bound with host origin evidence")

    def pre_bound(
        self,
        action: Action,
        proposal_id: str,
        user_id: str,
        index: ValueOriginIndex,
        registry: ToolRegistry,
    ) -> RuntimeVerdict:
        # Validate the host-bound action before any classification or execution.
        value = value_pre_check(index, proposal_id, user_id, registry)
        from react_agent.schemas.agent_output import ActionTurn

        proposed = ActionTurn.model_validate_json(str(index.store.get(proposal_id).content()))
        if proposed.action != action:
            raise ValueError("proposed action differs from gate input")
        coarse = super().pre_with_artifact(action, proposal_id)
        remaining = tuple(r for r in coarse.reasons if r not in COARSE_SENSITIVITY)
        # Never infer ALLOW merely from filtering reason text on an unexplained DENY.
        discharged = (
            value.effect == Effect.ALLOW
            and coarse.effect == Effect.DENY
            and bool(set(coarse.reasons) & COARSE_SENSITIVITY)
            and not remaining
        )
        denied = value.effect == Effect.DENY or (coarse.effect == Effect.DENY and not discharged)
        reasons = tuple(
            dict.fromkeys(
                r
                for r in (
                    *(remaining if discharged else coarse.reasons),
                    *(r.value for r in value.reasons),
                )
                if r != Reason.PASS.value
            )
        ) or (Reason.PASS.value,)
        result = RuntimeVerdict(
            stage=Stage.PRE,
            effect=Effect.DENY if denied else Effect.ALLOW,
            reasons=reasons,
            related_artifact_ids=tuple(
                dict.fromkeys((*coarse.related_artifact_ids, *value.related_artifact_ids))
            ),
            component="a6_composition_v1",
        )
        self.value_records.append(
            {
                "coarse": coarse.model_dump(mode="json"),
                "value": value.model_dump(mode="json"),
                "coarse_sensitivity_discharged": discharged,
                "composed": result.model_dump(mode="json"),
            }
        )
        return result


def admit(index: ValueOriginIndex, artifact_id: str, step: int) -> str | None:
    """Expected extraction limits are sticky failures, never silent truncation."""
    try:
        index.add_artifact(artifact_id, observed_step=step)
    except OriginError as exc:
        if index.complete:
            raise ValueError("failed admission must invalidate coverage") from exc
        return type(exc).__name__
    return None


def final_bound(index: ValueOriginIndex, proposal_id: str, user_id: str) -> FinalValueRelease:
    store = index.store
    proposal = store.get(proposal_id)
    if (
        proposal.artifact_type != ArtifactType.FINAL_RESPONSE
        or proposal.source_type != SourceType.MODEL
        or not proposal.parents
        or not isinstance(proposal.content(), str)
    ):
        raise ValueError("host proposed final required")
    ancestors = store.ancestors(proposal_id)
    observed = {
        a.artifact_id
        for a in ancestors
        if not a.parents
        and (
            a.producer == "tool_source_snapshot"
            or (a.source_type == SourceType.USER and a.producer == "host_context")
        )
    }
    admitted = set(index.snapshot()["source_sha256"])
    if (
        index.complete
        and user_id in observed
        and observed == admitted
        and proposal.created_step >= index.last_observed_step
    ):
        return release_final(index, proposal_id)
    released = derive(
        store,
        "",
        kind=ArtifactType.FINAL_RESPONSE,
        parents=(proposal_id,),
        step=proposal.created_step,
        source_type=SourceType.SYSTEM,
        producer="a6_coverage_denial_v1",
        sensitivity=Sensitivity.PUBLIC,
    )
    return FinalValueRelease(
        profile="a6_coverage_denial_v1",
        effect=Effect.DENY,
        reasons=(Reason.UNKNOWN,),
        proposed_artifact_id=proposal_id,
        released_artifact_id=released.artifact_id,
        proposed_sha256=proposal.content_hash,
        released_sha256=released.content_hash,
        index_sha256=index.identity,
    )
