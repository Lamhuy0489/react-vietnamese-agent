"""Cumulative A3–A5 coarse session gates; no fine-grained value-origin claims."""

from __future__ import annotations

from react_agent.foundation.artifacts import Immutable, Sensitivity, Trust, join_sensitivity
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.a2_policy import A2Policy
from react_agent.security_v1.contracts import (
    EXTERNAL,
    Effect,
    PolicyObservation,
    Reason,
    SecurityConfig,
    configuration,
)
from react_agent.security_v1.guard import GuardOutcome, ModelGuard
from react_agent.security_v1.runtime_policy import RuntimeVerdict


class SessionSecurityState(Immutable):
    max_sensitivity: Sensitivity = Sensitivity.PUBLIC
    untrusted_seen: bool = False
    untrusted_control_signal: bool = False
    rule_alert_seen: bool = False
    llm_alert_seen: bool = False
    guard_error_seen: bool = False
    external_action_attempted: bool = False
    observed_sensitive_artifact_ids: tuple[str, ...] = ()
    observed_untrusted_artifact_ids: tuple[str, ...] = ()
    alert_artifact_ids: tuple[str, ...] = ()


def extend(values: tuple[str, ...], identity: str | None) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*values, identity))) if identity is not None else values


class SessionPolicy(A2Policy):
    def __init__(self, config: SecurityConfig, raw_user: str, guard: ModelGuard) -> None:
        if config.level not in {"A3", "A4", "A5"}:
            raise ValueError("SessionPolicy implements only cumulative A3/A4/A5")
        super().__init__(configuration("A2"), raw_user, guard)
        self.security = config
        self.session = SessionSecurityState()

    def _guard_signal(self, artifact_id: str | None) -> tuple[bool, bool]:
        outcome = GuardOutcome.model_validate(self.guard_records[-1]["outcome"])
        error = outcome.status == "ERROR" or outcome.result is None
        alert = outcome.result is not None and outcome.result.risk in {"SUSPICIOUS", "MALICIOUS"}
        self.session = self.session.model_copy(
            update={
                "llm_alert_seen": self.session.llm_alert_seen or alert,
                "guard_error_seen": self.session.guard_error_seen or error,
                "alert_artifact_ids": extend(self.session.alert_artifact_ids, artifact_id)
                if alert or error
                else self.session.alert_artifact_ids,
            }
        )
        return alert, error

    def pre(self, action: Action) -> RuntimeVerdict:
        return self.pre_with_artifact(action, None)

    def pre_with_artifact(self, action: Action, artifact_id: str | None) -> RuntimeVerdict:
        base = super().pre(action)
        self._guard_signal(artifact_id)
        reasons: list[str] = []
        identities: tuple[str, ...] = ()
        if action.name in EXTERNAL:
            self.session = self.session.model_copy(update={"external_action_attempted": True})
            if self.session.max_sensitivity != Sensitivity.PUBLIC:
                reasons.extend((Reason.CLEARANCE.value, Reason.SESSION_SENSITIVITY.value))
                identities += self.session.observed_sensitive_artifact_ids
            if (
                self.security.session_trust
                and self.session.untrusted_seen
                and not self.component.anchors.authorizes(action)
            ):
                reasons.extend(
                    (
                        Reason.CONTROL.value,
                        Reason.DESTINATION.value,
                        Reason.ACTION.value,
                        Reason.SESSION_TRUST.value,
                    )
                )
                identities += self.session.observed_untrusted_artifact_ids
            if self.security.joint_session and (
                self.session.rule_alert_seen
                or self.session.llm_alert_seen
                or self.session.guard_error_seen
            ):
                reasons.append(Reason.SESSION_COMBINED.value)
                identities += self.session.alert_artifact_ids
        verdict = self._combine(
            base, Effect.DENY if reasons else base.effect, tuple(reasons), identities
        )
        return verdict.model_copy(update={"component": "session_policy_v1"})

    def post(self, observation: PolicyObservation) -> RuntimeVerdict:
        previous = len(self.component.signals)
        previous_errors = len(self.errors)
        base = super().post(observation)
        alert, error = self._guard_signal(observation.artifact_id)
        rule = any(s.matched_rule_ids for s in self.component.signals[previous:])
        detector_error = len(self.errors) != previous_errors
        untrusted = observation.trust == Trust.UNTRUSTED
        sensitive = observation.sensitivity != Sensitivity.PUBLIC
        self.session = self.session.model_copy(
            update={
                "max_sensitivity": join_sensitivity(
                    self.session.max_sensitivity, observation.sensitivity
                ),
                "untrusted_seen": self.session.untrusted_seen or untrusted,
                "untrusted_control_signal": self.session.untrusted_control_signal
                or (untrusted and (rule or alert or error or detector_error)),
                "rule_alert_seen": self.session.rule_alert_seen or rule,
                "guard_error_seen": self.session.guard_error_seen or detector_error,
                "observed_sensitive_artifact_ids": extend(
                    self.session.observed_sensitive_artifact_ids, observation.artifact_id
                )
                if sensitive
                else self.session.observed_sensitive_artifact_ids,
                "observed_untrusted_artifact_ids": extend(
                    self.session.observed_untrusted_artifact_ids, observation.artifact_id
                )
                if untrusted
                else self.session.observed_untrusted_artifact_ids,
                "alert_artifact_ids": extend(
                    self.session.alert_artifact_ids, observation.artifact_id
                )
                if rule or detector_error
                else self.session.alert_artifact_ids,
            }
        )
        tagged = sensitive or (self.security.session_trust and untrusted)
        reasons = (
            *((Reason.SESSION_SENSITIVITY.value,) if sensitive else ()),
            *((Reason.SESSION_TRUST.value,) if self.security.session_trust and untrusted else ()),
        )
        return self._combine(
            base, Effect.TAG if tagged else base.effect, reasons, (observation.artifact_id,)
        ).model_copy(
            update={
                "component": "session_policy_v1",
            }
        )
