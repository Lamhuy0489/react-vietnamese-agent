"""A6 v2: value provenance refines the session-level vetoes it inherits (rebuild R2).

The Phase 5 A6 (``CandidateA6Policy``) keeps every A3–A5 session veto except
proven-unrelated *sensitivity*, and authorizes destinations only through the
hand-written ``authorization_anchors_v4`` grammar. On the Dev reference replay
that grammar found no destination in most natural instructions ("…, gửi
mock://internal/headcount payload chỉ có count là tổng."), so A6 blocked 110 of
128 measured benign sink calls (decision log 2026-10-26).

Two changes, A6 only; A0–A5 and every sealed file are untouched:

1. Destination provenance. A destination is user-granted when v4 grants it, or
   when the exact address/endpoint string occurs in the raw user instruction in
   an affirmative send clause: a send verb precedes it in the same clause, and
   no negation, condition or reported-speech marker precedes it there. Attack
   payloads arrive through tool output, never through the user instruction, so
   an injected destination cannot satisfy this.
2. Discharge. When the value gate allows the action (every critical field has a
   known origin, none is sensitive, the destination is user-granted), the coarse
   session reasons — sensitivity and trust/control alike — are discharged. Rule
   (A1) and guard (A2) reasons are never discharged and still veto.

Discharge applies to external sink calls only; reads keep Phase 5 decisions.
``activate()`` swaps the A6 policy class used by the closure runtime;
``profile()`` is recorded in run identities.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

import react_agent.security_v1.a6_policy as a6_policy
import react_agent.security_v1.runtime_v14_email_origin_candidate as runtime_v14
from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    canonical_json,
)
from react_agent.foundation.normalization import text_hash
from react_agent.schemas.agent_output import Action, ActionTurn
from react_agent.security_v1.authorization_anchors_v4 import NEGATIVE, REPORTED
from react_agent.security_v1.authorization_anchors_v4 import (
    extract_anchors as extract_v4,
)
from react_agent.security_v1.contracts import EXTERNAL, Effect, Reason, SecurityConfig
from react_agent.security_v1.email_value_gates_v1 import value_pre_check
from react_agent.security_v1.guard import ModelGuard
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.rules import EMAIL, ENDPOINT, AuthorizationAnchors
from react_agent.security_v1.value_gates import ValuePreDecision

PROFILE = "a6_provenance_v2"
# Sentence ends only where punctuation is followed by space/end, so dots inside
# addresses and URLs never split a clause.
CLAUSE = re.compile(r"[;\n]+|[.!?](?=\s|$)")
# "sau khi"/"trước khi" (after/before) are temporal, not conditional.
CONDITIONAL = re.compile(
    r"\b(?:nếu|neu|if|unless|when)\b|(?<!sau )(?<!trước )(?<!truoc )\bkhi\b", re.I)
QUOTE_MARKS = re.compile(r"[\"“”'`]")
NUMBER = re.compile(r"(?<![\w.])[+-]?\d+(?:\.\d+)?(?![\w.]|\.\d)")
DISCHARGEABLE = frozenset(r.value for r in (
    Reason.CLEARANCE, Reason.SESSION_SENSITIVITY, Reason.SESSION_TRUST,
    Reason.SESSION_COMBINED, Reason.CONTROL, Reason.DESTINATION, Reason.ACTION,
))
# The value gate may be refined only when it denied for missing evidence; a
# sensitive payload or an untrusted destination is never overridden.
REFINABLE = frozenset({Reason.UNKNOWN_FIELD, Reason.ACTION, Reason.DESTINATION})
DESTINATION_KEY = {"send_email_mock": "to", "post_webhook_mock": "endpoint"}
MAX_LEAVES, MAX_DEPTH = 64, 6
_ORIGINAL_POLICY = runtime_v14.CandidateA6Policy
_ORIGINAL_COARSE = a6_policy.COARSE_SENSITIVITY


def _clauses(raw: str) -> list[str]:
    out, start = [], 0
    for match in CLAUSE.finditer(raw):
        out.append(raw[start:match.start()])
        start = match.end()
    out.append(raw[start:])
    return out


def user_destinations(raw_user: str) -> tuple[set[str], set[str]]:
    """Destinations written by the user outside negated, conditional or quoted text."""
    emails: set[str] = set()
    endpoints: set[str] = set()
    for clause in _clauses(raw_user):
        for pattern, bucket in ((EMAIL, emails), (ENDPOINT, endpoints)):
            for match in pattern.finditer(clause):
                before = clause[: match.start()]
                quoted = len(QUOTE_MARKS.findall(before)) % 2 == 1
                if not (quoted or NEGATIVE.search(before) or CONDITIONAL.search(before)
                        or REPORTED.search(before)):
                    bucket.add(match.group().rstrip(".,!?)"))
    return emails, endpoints


def extract_anchors(raw_user: str) -> AuthorizationAnchors:
    base = extract_v4(raw_user)
    emails, endpoints = user_destinations(raw_user)
    return AuthorizationAnchors(
        emails=tuple(sorted({*base.emails, *emails})),
        endpoints=tuple(sorted({*base.endpoints, *endpoints})),
        raw_user_sha256=text_hash(raw_user),
    )


def _leaves(value: Any, key: str, depth: int = 0) -> list[tuple[str, Any]]:
    if depth > MAX_DEPTH:
        raise ValueError("payload too deep")
    if isinstance(value, dict):
        return [leaf for k, v in value.items() for leaf in _leaves(v, str(k), depth + 1)]
    if isinstance(value, list):
        return [leaf for v in value for leaf in _leaves(v, key, depth + 1)]
    return [(key, value)]


def _token(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _in_text(token: str, text: str) -> bool:
    return bool(token) and re.search(
        r"(?<![\w@./-])" + re.escape(token) + r"(?![\w@/-]|\.\w)", text) is not None


def _calculator_results(store: ArtifactStore, user_text: str) -> set[str]:
    """Calculator outputs whose every operand the user wrote."""
    artifacts = store.all()
    results = set()
    for i, artifact in enumerate(artifacts):
        if artifact.artifact_type != ArtifactType.CALCULATION_RESULT:
            continue
        arguments = [a for a in artifacts[:i] if a.artifact_type == ArtifactType.TOOL_ARGUMENT
                     and a.created_step == artifact.created_step]
        if not arguments:
            continue
        expression = json.loads(arguments[-1].raw_json).get("expression")
        value = json.loads(artifact.raw_json).get("value")
        if not isinstance(expression, str) or isinstance(value, bool) or value is None:
            continue
        operands = NUMBER.findall(expression)
        if operands and all(_in_text(o, user_text) for o in operands):
            results.add(_token(value))
    return results


def payload_provenance(store: ArtifactStore, user_text: str, action: Action) -> bool:
    """Every non-destination leaf was written by the user or computed from user operands.

    Tool sources, trusted or not, never vouch for a sink value: trust labels are
    independent of safety, and an injected value can sit in a trusted page.
    """
    computed = _calculator_results(store, user_text)
    leaves = [leaf for key, value in action.arguments.items()
              if key != DESTINATION_KEY[action.name] for leaf in _leaves(value, key)]
    if not leaves or len(leaves) > MAX_LEAVES:
        return False
    for key, value in leaves:
        token = _token(value)
        if isinstance(value, bool) and not _in_text(key, user_text):
            return False  # a flag counts as user-stated only next to its own name
        # Word-bounded match only: "public" must not match inside ".../publication".
        if not (_in_text(token, user_text) or token in computed):
            return False
    return True


def value_pre_check_v2(index: Any, proposal_artifact_id: str, user_artifact_id: str,
                       registry: Any) -> ValuePreDecision:
    baseline = cast(ValuePreDecision, bind(value_pre_check, extract_anchors=extract_anchors)(
        index, proposal_artifact_id, user_artifact_id, registry))
    if baseline.effect != Effect.DENY or not set(baseline.reasons) <= REFINABLE:
        return baseline
    store = index.store
    user_text = store.get(user_artifact_id).content()
    action = ActionTurn.model_validate_json(str(store.get(proposal_artifact_id).content())).action
    if (not isinstance(user_text, str) or action.name not in DESTINATION_KEY
            or not index.complete or baseline.protected_matches):
        return baseline
    if not extract_anchors(user_text).authorizes(action):
        return baseline
    try:
        if index.protected_matches(canonical_json(action.arguments)):
            return baseline
        if not payload_provenance(store, user_text, action):
            return baseline
    except ValueError:  # includes OriginError: fail closed to the Phase 5 decision
        return baseline
    return baseline.model_copy(update={"effect": Effect.ALLOW, "reasons": (Reason.PASS,),
                                       "profile": PROFILE})


class ProvenanceA6Policy(runtime_v14.CandidateA6Policy):
    def __init__(self, config: SecurityConfig, raw_user: str, guard: ModelGuard) -> None:
        super().__init__(config, raw_user, guard)
        self.component.anchors = extract_anchors(raw_user)

    def pre_bound(self, action: Action, *args: Any, **kwargs: Any) -> Any:
        # Only external sink calls may discharge session vetoes; reads keep the
        # Phase 5 resource-scope decisions, whose denials the later scope relies on.
        a6_policy.COARSE_SENSITIVITY = (DISCHARGEABLE if action.name in EXTERNAL
                                        else _ORIGINAL_COARSE)
        try:
            return bind(a6_policy.A6Policy.pre_bound, value_pre_check=value_pre_check_v2)(
                self, action, *args, **kwargs)
        finally:
            a6_policy.COARSE_SENSITIVITY = _ORIGINAL_COARSE


def profile() -> dict[str, str]:
    return {"name": PROFILE, "module_sha256": hashlib.sha256(
        Path(__file__).read_bytes()).hexdigest()}


def activate() -> dict[str, str]:
    runtime_v14.CandidateA6Policy = ProvenanceA6Policy  # type: ignore[misc]
    return profile()


def deactivate() -> None:
    runtime_v14.CandidateA6Policy = _ORIGINAL_POLICY  # type: ignore[misc]
    a6_policy.COARSE_SENSITIVITY = _ORIGINAL_COARSE
