"""A2 cumulative run-local policy; coarse sticky source risk, not value lineage."""

from __future__ import annotations

import time

from react_agent.foundation.artifacts import canonical_json
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import (
    EXTERNAL,
    Effect,
    PolicyObservation,
    SecurityConfig,
    Stage,
    configuration,
)
from react_agent.security_v1.guard import GuardInput, GuardOutcome, ModelGuard, guard_pre_decision
from react_agent.security_v1.runtime_policy import RuntimePolicy, RuntimeVerdict


class A2Policy(RuntimePolicy):
    def __init__(self, config: SecurityConfig, raw_user: str, guard: ModelGuard) -> None:
        if config.level != "A2":
            raise ValueError("A2Policy requires A2; no silent level fallback")
        super().__init__(configuration("A1"), raw_user)
        self.raw_user = raw_user
        self.guard = guard
        self.guard_records: list[dict[str, object]] = []
        self.source_risks: list[tuple[str, str]] = []

    def _classify(self, request: GuardInput, stage: Stage, artifact_id: str | None) -> str:
        started = time.monotonic()
        outcome = self.guard.classify(request)
        risk = outcome.result.risk if outcome.status == "OK" and outcome.result else "ERROR"
        self.guard_records.append(
            {
                "sequence": len(self.guard_records) + 1,
                "stage": stage.value,
                "artifact_id": artifact_id,
                "input": request.model_dump(mode="json"),
                "outcome": outcome.model_dump(mode="json"),
                "elapsed_seconds": time.monotonic() - started,
            }
        )
        return risk

    @staticmethod
    def _combine(
        base: RuntimeVerdict, effect: Effect, reasons: tuple[str, ...], ids: tuple[str, ...] = ()
    ) -> RuntimeVerdict:
        return RuntimeVerdict(
            stage=base.stage,
            effect=Effect.DENY if base.effect == Effect.DENY else effect,
            reasons=tuple(
                dict.fromkeys(r for r in (*base.reasons, *reasons) if r != "PASS_THROUGH")
            )
            or ("PASS_THROUGH",),
            related_artifact_ids=tuple(dict.fromkeys((*base.related_artifact_ids, *ids))),
            component="a2_policy_v2",
        )

    def pre(self, action: Action) -> RuntimeVerdict:
        base = super().pre(action)
        self._classify(
            GuardInput(
                user_instruction=self.raw_user,
                source_type="model_action",
                candidate_action_json=canonical_json(action.model_dump(mode="json")),
            ),
            Stage.PRE,
            None,
        )
        # Reuse the frozen risk-to-action mapping, including fail-open reads.
        outcome = GuardOutcome.model_validate(self.guard_records[-1]["outcome"])
        current = guard_pre_decision(action, outcome)
        sticky = [(a, r) for a, r in self.source_risks if r in {"MALICIOUS", "ERROR"}]
        deny = current.effect == Effect.DENY or (action.name in EXTERNAL and bool(sticky))
        reasons = tuple(r.value for r in current.reasons)
        if action.name in EXTERNAL:
            reasons += tuple("LLM_GUARD_" + r for _, r in sticky)
        return self._combine(
            base,
            Effect.DENY if deny else Effect.ALLOW,
            reasons,
            tuple(a for a, _ in sticky) if action.name in EXTERNAL else (),
        )

    def post(self, observation: PolicyObservation) -> RuntimeVerdict:
        base = super().post(observation)
        risk = self._classify(
            GuardInput(
                user_instruction=self.raw_user,
                source_type=observation.source_type.value,
                candidate_content=observation.content,
            ),
            Stage.POST,
            observation.artifact_id,
        )
        if risk != "SAFE":
            self.source_risks.append((observation.artifact_id, risk))
        return self._combine(
            base,
            Effect.TAG if risk != "SAFE" or base.effect == Effect.TAG else Effect.ALLOW,
            ("LLM_GUARD_" + risk,) if risk != "SAFE" else (),
            (observation.artifact_id,),
        )
