"""Run-local A0/A1 policy adapter with typed error fallback and sidecar records."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from react_agent.foundation.artifacts import Immutable
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import (
    EXTERNAL,
    Effect,
    PolicyObservation,
    SecurityConfig,
    SecurityDecision,
    Stage,
)
from react_agent.security_v1.rules import RulePolicy

DENIAL_FEEDBACK = (
    'POLICY_FEEDBACK: {"status":"denied","code":"SECURITY_POLICY_DENIED","tool_executed":false}'
)


class RuntimeVerdict(Immutable):
    stage: Stage
    effect: Effect
    reasons: tuple[str, ...] = Field(min_length=1)
    related_artifact_ids: tuple[str, ...] = ()
    component: str

    @classmethod
    def from_component(cls, decision: SecurityDecision) -> RuntimeVerdict:
        return cls.model_validate(decision.model_dump(mode="json"))


class SecurityEvent(Immutable):
    schema_version: Literal["security_trace_v1"] = "security_trace_v1"
    run_id: str
    task_id: str
    step: int = Field(ge=0)
    sequence: int = Field(ge=1)
    event: Literal[
        "proposal",
        "decision",
        "denied",
        "broker_result",
        "rule_signal",
        "detector_error",
        "proposed_final",
        "released_final",
    ]
    data_json: str


class RuntimePolicy:
    def __init__(self, config: SecurityConfig, raw_user: str) -> None:
        self.component = RulePolicy(config, raw_user)
        self.errors: list[tuple[str, str]] = []

    def pre(self, action: Action) -> RuntimeVerdict:
        base = RuntimeVerdict.from_component(self.component.pre(action))
        if self.errors and action.name in EXTERNAL:
            return RuntimeVerdict(
                stage=Stage.PRE,
                effect=Effect.DENY,
                reasons=tuple(
                    dict.fromkeys(
                        (*(r for r in base.reasons if r != "PASS_THROUGH"), "RULE_GUARD_ERROR")
                    )
                ),
                related_artifact_ids=tuple(
                    dict.fromkeys((*base.related_artifact_ids, *(a for a, _ in self.errors)))
                ),
                component="rules_v1",
            )
        return base

    def post(self, observation: PolicyObservation) -> RuntimeVerdict:
        try:
            return RuntimeVerdict.from_component(self.component.post(observation))
        except Exception as exc:  # Detector boundary: retain error class, never raw exception text.
            self.errors.append((observation.artifact_id, type(exc).__name__))
            return RuntimeVerdict(
                stage=Stage.POST,
                effect=Effect.TAG,
                reasons=("RULE_GUARD_ERROR",),
                related_artifact_ids=(observation.artifact_id,),
                component="rules_v1",
            )

    def final(self) -> RuntimeVerdict:
        return RuntimeVerdict.from_component(self.component.final())
