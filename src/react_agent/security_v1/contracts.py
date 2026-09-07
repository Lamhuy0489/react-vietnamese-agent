"""Strict public-only policy inputs and cumulative configuration."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator

from react_agent.foundation.artifacts import (
    Immutable,
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
)
from react_agent.foundation.normalization import text_hash

Level = Literal["A0", "A1", "A2", "A3", "A4", "A5", "A6"]
EXTERNAL = frozenset({"send_email_mock", "post_webhook_mock"})


class SecurityConfig(Immutable):
    version: Literal["security_config_v1"] = "security_config_v1"
    level: Level
    rule: bool
    llm_guard: bool
    session_sensitivity: bool
    session_trust: bool
    joint_session: bool
    value_origin: bool
    rule_version: Literal["rules_v1"] = "rules_v1"
    detector_profile: Literal["security_v1"] = "security_v1"
    model_input_profile: Literal["raw_v1"] = "raw_v1"

    @model_validator(mode="after")
    def cumulative(self) -> Self:
        rank = int(self.level[1])
        actual = (
            self.rule,
            self.llm_guard,
            self.session_sensitivity,
            self.session_trust,
            self.joint_session,
            self.value_origin,
        )
        if actual != tuple(rank >= i for i in range(1, 7)):
            raise ValueError("component switches contradict cumulative level")
        return self

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))


def configuration(level: Level) -> SecurityConfig:
    rank = int(level[1])
    return SecurityConfig(
        level=level,
        rule=rank >= 1,
        llm_guard=rank >= 2,
        session_sensitivity=rank >= 3,
        session_trust=rank >= 4,
        joint_session=rank >= 5,
        value_origin=rank >= 6,
    )


class Stage(StrEnum):
    PRE = "PRE"
    POST = "POST"
    FINAL = "FINAL"


class Effect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    TAG = "TAG"
    QUARANTINE = "QUARANTINE"
    SANITIZE = "SANITIZE"
    REDACT = "REDACT"


class Reason(StrEnum):
    PASS = "PASS_THROUGH"  # noqa: S105 - decision reason, not a password
    RULE = "RULE_INJECTION_SIGNAL"
    EXTERNAL = "RULE_EXTERNAL_ACTION_SIGNAL"
    GUARD_MALICIOUS = "LLM_GUARD_MALICIOUS"
    GUARD_SUSPICIOUS = "LLM_GUARD_SUSPICIOUS"
    GUARD_ERROR = "LLM_GUARD_ERROR"
    CLEARANCE = "SENSITIVITY_EXCEEDS_SINK_CLEARANCE"
    CONTROL = "UNTRUSTED_CONTROL_INFLUENCE"
    DESTINATION = "UNAUTHORIZED_DESTINATION"
    ACTION = "UNAUTHORIZED_EXTERNAL_ACTION"
    SESSION_SENSITIVITY = "SESSION_SENSITIVITY_RISK"
    SESSION_TRUST = "SESSION_TRUST_RISK"
    SESSION_COMBINED = "SESSION_COMBINED_RISK"
    SENSITIVE_PAYLOAD = "PROVENANCE_SENSITIVE_PAYLOAD"
    UNTRUSTED_DESTINATION = "PROVENANCE_UNTRUSTED_DESTINATION"
    UNTRUSTED_CONTROL = "PROVENANCE_UNTRUSTED_CONTROL"
    UNKNOWN_FIELD = "PROVENANCE_UNKNOWN_CRITICAL_FIELD"
    FINAL_LINEAGE = "FINAL_SENSITIVE_LINEAGE"
    FINAL_VALUE = "FINAL_SENSITIVE_VALUE_MATCH"
    UNKNOWN = "UNKNOWN_LINEAGE_FAIL_CLOSED"


class SecurityDecision(Immutable):
    stage: Stage
    effect: Effect
    reasons: tuple[Reason, ...] = Field(min_length=1)
    related_artifact_ids: tuple[str, ...] = ()
    component: str = Field(min_length=1)


class PolicyObservation(Immutable):
    artifact_id: str = Field(min_length=1)
    content: str
    source_type: SourceType
    sensitivity: Sensitivity
    trust: Trust


class RuleSignal(Immutable):
    artifact_id: str
    matched_rule_ids: tuple[str, ...] = ()
    raw_sha256: str
    detector_sha256: str
