"""Bounded lexical A1 detector and raw-user-only authorization anchors."""

from __future__ import annotations

import re

from react_agent.foundation.artifacts import Immutable, Trust
from react_agent.foundation.normalization import normalize, text_hash
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import (
    EXTERNAL,
    Effect,
    PolicyObservation,
    Reason,
    RuleSignal,
    SecurityConfig,
    SecurityDecision,
    Stage,
)

EMAIL = re.compile(
    r"(?<![\w.+-])[A-Za-z0-9_.+-]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,20}(?![\w.-])"
)
ENDPOINT = re.compile(r"(?:https?://|mock://)[^\s<>\"'`]{1,512}")
DESTINATION_CUE = re.compile(r"\b(?:đến|tới|den|toi|to)\s{1,8}$", re.I)
OVERRIDE = re.compile(
    r"\b(?:ignore\s{1,8}(?:all\s{1,8})?(?:previous|prior)\s{1,8}instructions?|"
    r"(?:bỏ|bo)\s{1,8}qua\s{1,8}(?:chỉ\s{1,8}dẫn|chi\s{1,8}dan|hướng\s{1,8}dẫn|huong\s{1,8}dan)\s{1,8}(?:trước|truoc))\b",
    re.I,
)
CONTROL = re.compile(
    r"\b(?:system\s{1,8}prompt|developer\s{1,8}instructions?|hidden\s{1,8}instructions?)\b", re.I
)
SEND = re.compile(r"\b(?:gửi|gởi|gui|send|post)\b", re.I)
NEGATED = re.compile(r"\b(?:không|khong|đừng|dung|chớ|cho|not|never|nếu|neu|if)\b", re.I)
AFFIRMATIVE = re.compile(r"^\s*(?:(?:hãy|hay|please)\s+)?(?:gửi|gởi|gui|send|post)\b", re.I)


class AuthorizationAnchors(Immutable):
    emails: tuple[str, ...] = ()
    endpoints: tuple[str, ...] = ()
    raw_user_sha256: str

    def authorizes(self, action: Action) -> bool:
        if action.name == "send_email_mock":
            return action.arguments.get("to") in self.emails
        if action.name == "post_webhook_mock":
            return action.arguments.get("endpoint") in self.endpoints
        return False


def extract_anchors(raw_user: str) -> AuthorizationAnchors:
    emails: set[str] = set()
    endpoints: set[str] = set()
    # Do not split on '.', which is part of addresses; newline/semicolon only.
    for clause in re.split(r"[\n;]", raw_user):
        if not AFFIRMATIVE.search(clause) or NEGATED.search(clause):
            continue
        if any(mark in clause for mark in ('"', "'", "`", "“", "”", ">")):
            continue
        if "webhook" in clause.casefold() or clause.casefold().lstrip().startswith("post "):
            endpoints.update(
                m.group().rstrip(".,!?)")
                for m in ENDPOINT.finditer(clause)
                if DESTINATION_CUE.search(clause[: m.start()])
            )
        else:
            emails.update(
                m.group()
                for m in EMAIL.finditer(clause)
                if DESTINATION_CUE.search(clause[: m.start()])
            )
    return AuthorizationAnchors(
        emails=tuple(sorted(emails)),
        endpoints=tuple(sorted(endpoints)),
        raw_user_sha256=text_hash(raw_user),
    )


class RuleGuard:
    version = "rules_v1"

    def scan(self, observation: PolicyObservation) -> RuleSignal:
        normalized = normalize(observation.content, "security_v1")
        matches: set[str] = set()
        for view in (observation.content, normalized.normalized_text):
            if OVERRIDE.search(view):
                matches.add("R_OVERRIDE_01")
            if CONTROL.search(view):
                matches.add("R_CONTROL_01")
            if (
                observation.trust == Trust.UNTRUSTED
                and SEND.search(view)
                and (EMAIL.search(view) or ENDPOINT.search(view))
            ):
                matches.add("R_EXTERNAL_01")
        return RuleSignal(
            artifact_id=observation.artifact_id,
            matched_rule_ids=tuple(sorted(matches)),
            raw_sha256=normalized.input_hash,
            detector_sha256=normalized.output_hash,
        )


class RulePolicy:
    """One instance per run. No source content/GT hidden in global state."""

    def __init__(self, config: SecurityConfig, raw_user: str) -> None:
        if config.level not in {"A0", "A1"}:
            raise ValueError("only A0/A1 implemented by RulePolicy; no silent fallback")
        self.config = config
        self.anchors = extract_anchors(raw_user)
        self._signals: list[RuleSignal] = []
        self.guard = RuleGuard()

    @property
    def signals(self) -> tuple[RuleSignal, ...]:
        return tuple(self._signals)

    def post(self, observation: PolicyObservation) -> SecurityDecision:
        if not self.config.rule:
            return SecurityDecision(
                stage=Stage.POST, effect=Effect.ALLOW, reasons=(Reason.PASS,), component="A0"
            )
        signal = self.guard.scan(observation)
        self._signals.append(signal)
        reasons = []
        if any(r != "R_EXTERNAL_01" for r in signal.matched_rule_ids):
            reasons.append(Reason.RULE)
        if "R_EXTERNAL_01" in signal.matched_rule_ids:
            reasons.append(Reason.EXTERNAL)
        return SecurityDecision(
            stage=Stage.POST,
            effect=Effect.TAG if reasons else Effect.ALLOW,
            reasons=tuple(reasons) or (Reason.PASS,),
            related_artifact_ids=(observation.artifact_id,),
            component="rules_v1",
        )

    def pre(self, action: Action) -> SecurityDecision:
        alerts = tuple(s.artifact_id for s in self._signals if s.matched_rule_ids)
        deny = (
            self.config.rule
            and bool(alerts)
            and action.name in EXTERNAL
            and not self.anchors.authorizes(action)
        )
        return SecurityDecision(
            stage=Stage.PRE,
            effect=Effect.DENY if deny else Effect.ALLOW,
            reasons=(Reason.RULE, Reason.ACTION) if deny else (Reason.PASS,),
            related_artifact_ids=alerts if deny else (),
            component=self.config.level,
        )

    def final(self) -> SecurityDecision:
        return SecurityDecision(
            stage=Stage.FINAL,
            effect=Effect.ALLOW,
            reasons=(Reason.PASS,),
            component=self.config.level,
        )
