"""Bounded value-gate extension for the v4 safe-email CPU candidate.

The frozen value gate requires every external argument to have an exact origin
record.  A short subject supplied in the same affirmative raw-user send clause
is user-authored control metadata, however, and is not a document payload.  A
candidate may admit that one field only when the v4 parser explicitly
authorizes the exact destination, the subject occurs in that send clause, and
the protected scan finds no sensitive value.  All other unknown fields and
all payload/provenance failures remain fail-closed.
"""

from __future__ import annotations

import re
from typing import Any, cast

from react_agent.schemas.agent_output import ActionTurn
from react_agent.security_v1.authorization_anchors_v4 import audit_anchors, extract_anchors
from react_agent.security_v1.contracts import Effect, Reason
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.value_gates import (
    FieldOrigin,
    ValuePreDecision,
    _user,
)
from react_agent.security_v1.value_gates import (
    value_pre_check as frozen_value_pre_check,
)
from react_agent.security_v1.value_origin import OriginError, OriginRecord, ValueType

PROFILE = "value_pre_gate_v2_email_subject_candidate"
MAX_SUBJECT_BYTES = 256
_SUBJECT_CUE = re.compile(r"\bsubject\b|\bchủ\s+đề\b|\bchu\s+de\b", re.I)


def _subject_clause(raw: str, subject: str, audit: Any) -> bool:
    if not subject or len(subject.encode("utf-8")) > MAX_SUBJECT_BYTES:
        return False
    if not subject.strip() or any(ord(char) < 32 for char in subject):
        return False
    for clause in audit.clauses:
        if clause.kind != "send":
            continue
        fragment = raw[clause.start : clause.end]
        if _SUBJECT_CUE.search(fragment) and subject in fragment:
            return True
    return False


def value_pre_check(
    index: Any,
    proposal_artifact_id: str,
    user_artifact_id: str,
    registry: Any,
) -> ValuePreDecision:
    """Run the frozen gate, then admit only an exact raw-user subject field."""

    baseline = cast(
        ValuePreDecision,
        bind(frozen_value_pre_check, extract_anchors=extract_anchors)(
            index,
            proposal_artifact_id,
            user_artifact_id,
            registry,
        ),
    )
    if baseline.effect != Effect.DENY or Reason.UNKNOWN_FIELD not in baseline.reasons:
        return baseline
    store = index.store
    user = _user(store, user_artifact_id)
    proposal = store.get(proposal_artifact_id)
    if not isinstance(user.content(), str) or not isinstance(proposal.content(), str):
        return baseline
    action = ActionTurn.model_validate_json(str(proposal.content())).action
    if action.name != "send_email_mock":
        return baseline
    audit = audit_anchors(str(user.content()))
    if not extract_anchors(str(user.content())).authorizes(action):
        return baseline
    try:
        protected = index.protected_matches(str(action.arguments.get("subject", "")))
    except (OriginError, ValueError):
        return baseline
    if protected:
        return baseline
    subject = action.arguments.get("subject")
    if not isinstance(subject, str) or not _subject_clause(str(user.content()), subject, audit):
        return baseline
    # Only an unknown /subject field may be discharged.  Body, destination,
    # and every other unknown field retain the frozen fail-closed behavior.
    fields = list(baseline.fields)
    # UNKNOWN_FIELD is deduplicated across fields. Discharging /subject must
    # not erase the same reason for an unknown body or a partial failed scan.
    if {field.pointer for field in fields} != {"/to", "/subject", "/body"}:
        return baseline
    if any(not field.origins for field in fields if field.pointer != "/subject"):
        return baseline
    replaced = False
    for i, field in enumerate(fields):
        if field.pointer != "/subject" or field.origins:
            continue
        fields[i] = FieldOrigin(
            pointer="/subject",
            value_sha256=field.value_sha256,
            origins=(
                OriginRecord(
                    artifact_id=user.artifact_id,
                    source_sha256=user.content_hash,
                    pointer="/authorization/subject",
                    value_type=ValueType.FREE_TEXT,
                    value=subject,
                    sensitivity=user.sensitivity,
                    trust=user.trust,
                ),
            ),
        )
        replaced = True
        break
    if not replaced:
        return baseline
    remaining = tuple(reason for reason in baseline.reasons if reason != Reason.UNKNOWN_FIELD)
    if remaining:
        return baseline.model_copy(
            update={
                "fields": tuple(fields),
                "related_artifact_ids": tuple(
                    dict.fromkeys((*baseline.related_artifact_ids, user.artifact_id))
                ),
            }
        )
    return baseline.model_copy(
        update={
            "effect": Effect.ALLOW,
            "reasons": (Reason.PASS,),
            "fields": tuple(fields),
            "related_artifact_ids": tuple(
                dict.fromkeys((*baseline.related_artifact_ids, user.artifact_id))
            ),
        }
    )
