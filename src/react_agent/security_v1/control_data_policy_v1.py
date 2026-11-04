"""Defense v2 (D2): control/data separation, deterministic and host-side.

Design: ``docs/project/defense_v2_test2_design.md`` section 3 (owner-approved 2026-10-28).
The user is the trusted principal; only tool outputs are untrusted.

1. Reads are free (the frozen tool limits still apply).
2. A side-effect sink runs only if its destination, after normalisation, occurs
   literally in the user instruction. The user text is never parsed for intent.
3. A sink argument or final answer may not carry a value observed in a
   CONFIDENTIAL tool output unless the same value occurs literally in the user text.
4. A final answer that breaks rule 3 is redacted value by value, not failed.
5. The A1 rule layer (``rules_v1``) is kept; the LLM guard is off.

Nothing here reads evaluator ground truth, task IDs or Vietnamese phrase lists.
Tunable on Dev only (design 3.4): normalisation, destination grammar and the
sensitivity threshold.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field

from react_agent.foundation.artifacts import Sensitivity
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import (
    Effect,
    PolicyObservation,
    SecurityConfig,
    Stage,
)
from react_agent.security_v1.runtime_policy import RuntimePolicy, RuntimeVerdict

PROFILE = "control_data_policy_v1"
COMPONENT = "d2_control_data_v1"
REDACTION = "[REDACTED]"

# Sink tool -> argument that names the destination.
SINK_DESTINATION = {"send_email_mock": "to", "post_webhook_mock": "endpoint"}
# Arguments of a sink that may carry data (everything except the destination).
_FORMAT_CHARS = {"Cf"}  # zero-width and other format characters

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL = re.compile(r"(?:mock|https?)://[^\s\"'<>()\[\]]+")
# Mixed alphanumeric identifiers (keys, codes, account ids): at least one digit.
IDENTIFIER = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9][A-Za-z0-9_-]{5,63}(?![A-Za-z0-9_-])")
LONG_NUMBER = re.compile(r"(?<!\d)\d[\d.,]{5,}\d(?!\d)")


def normalise(text: str) -> str:
    """NFKC, drop format characters (zero-width), casefold. Comparison only."""
    text = unicodedata.normalize("NFKC", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) not in _FORMAT_CHARS)
    return text.casefold()


def destination_allowed(destination: str, user_text: str) -> bool:
    """Rule 2: the destination occurs literally (after normalisation) in the user text."""
    target = normalise(destination).strip().rstrip("/.")
    return bool(target) and target in normalise(user_text)


def sensitive_values(content: str) -> set[str]:
    """Candidate data values in a tool output (normalised).

    Emails, URLs, mixed alphanumeric identifiers containing a digit and long
    numbers. Plain words are never values: rule 3 is about literals, not topics.
    """
    text = unicodedata.normalize("NFKC", content)
    text = "".join(ch for ch in text if unicodedata.category(ch) not in _FORMAT_CHARS)
    values = {m.group() for m in EMAIL.finditer(text)}
    values |= {m.group().rstrip(".,;") for m in URL.finditer(text)}
    values |= {m.group() for m in IDENTIFIER.finditer(text)
               if any(c.isdigit() for c in m.group()) and any(c.isalpha() for c in m.group())}
    values |= {m.group() for m in LONG_NUMBER.finditer(text)}
    return {normalise(v) for v in values}


def leaked_values(text: str, protected: Iterable[str], user_text: str) -> list[str]:
    """Rule 3: protected values present in ``text`` and absent from the user text."""
    haystack, user = normalise(text), normalise(user_text)
    return sorted(v for v in set(protected) if v in haystack and v not in user)


def redact(text: str, values: Iterable[str]) -> str:
    """Rule 4: replace each offending value (case-insensitive, NFKC-insensitive)."""
    out = unicodedata.normalize("NFKC", text)
    out = "".join(ch for ch in out if unicodedata.category(ch) not in _FORMAT_CHARS)
    for value in sorted(set(values), key=len, reverse=True):
        out = re.sub(re.escape(value), REDACTION, out, flags=re.IGNORECASE)
    return out


def _flatten(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(_flatten(v) for v in value)
    return "" if value is None else str(value)


@dataclass
class ControlDataState:
    """Per-run state: the trusted user text and values seen in sensitive outputs."""

    user_text: str
    threshold: Sensitivity = Sensitivity.CONFIDENTIAL
    protected: set[str] = field(default_factory=set)
    sources: dict[str, set[str]] = field(default_factory=dict)

    def observe(self, artifact_id: str, content: str, sensitivity: Sensitivity) -> None:
        if _rank(sensitivity) >= _rank(self.threshold):
            values = sensitive_values(content)
            self.protected |= values
            self.sources.setdefault(artifact_id, set()).update(values)

    def check_action(self, action: Action) -> tuple[str, list[str]] | None:
        """Return (reason, related_values) to deny, or None to allow."""
        key = SINK_DESTINATION.get(action.name)
        if key is None:
            return None  # rule 1: reads are free
        destination = _flatten(action.arguments.get(key))
        if not destination_allowed(destination, self.user_text):
            return "UNTRUSTED_CONTROL_INFLUENCE", []
        payload = _flatten({k: v for k, v in action.arguments.items() if k != key})
        leaked = leaked_values(payload, self.protected, self.user_text)
        if leaked:
            return "PROVENANCE_SENSITIVE_PAYLOAD", leaked
        return None

    def check_final(self, answer: str) -> list[str]:
        return leaked_values(answer, self.protected, self.user_text)

    def related_artifacts(self, values: Iterable[str]) -> tuple[str, ...]:
        wanted = set(values)
        return tuple(a for a, vs in self.sources.items() if vs & wanted)


_ORDER = {Sensitivity.PUBLIC: 0, Sensitivity.INTERNAL: 1, Sensitivity.CONFIDENTIAL: 2}


def _rank(sensitivity: Sensitivity) -> int:
    return _ORDER[sensitivity]


class ControlDataPolicy(RuntimePolicy):
    """D2 = A1 rule layer + control/data rules 1-4. Guard off, no session gates."""

    def __init__(self, config: SecurityConfig, raw_user: str,
                 threshold: Sensitivity = Sensitivity.CONFIDENTIAL) -> None:
        super().__init__(config, raw_user)
        self.state = ControlDataState(raw_user, threshold)

    def pre(self, action: Action) -> RuntimeVerdict:
        base = super().pre(action)
        if base.effect == Effect.DENY:
            return base
        denial = self.state.check_action(action)
        if denial is None:
            return base
        reason, values = denial
        return RuntimeVerdict(
            stage=Stage.PRE, effect=Effect.DENY, reasons=(reason,),
            related_artifact_ids=self.state.related_artifacts(values), component=COMPONENT)

    def post(self, observation: PolicyObservation) -> RuntimeVerdict:
        self.state.observe(observation.artifact_id, observation.content, observation.sensitivity)
        return super().post(observation)

    def final_redactions(self, answer: str) -> list[str]:
        """Values the runtime must redact from the final answer (rule 4)."""
        return self.state.check_final(answer)
