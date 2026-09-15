"""Opt-in structural telemetry only; never repair output or retain model text."""

from __future__ import annotations

import json
from typing import Literal, cast

from pydantic import Field

from react_agent.foundation.artifacts import Immutable
from react_agent.security_v1.guard_diagnostics_v1 import (
    MAX_DIAGNOSTIC_CHARS,
    GuardDiagnostic,
)
from react_agent.security_v1.guard_diagnostics_v1 import (
    diagnose as diagnose_v1,
)

Framing = Literal["empty", "object", "array", "fenced", "other", "not_inspected"]
SyntaxKind = Literal[
    "none",
    "expected_value",
    "expected_key",
    "expected_colon",
    "expected_comma",
    "unterminated_string",
    "invalid_escape",
    "invalid_control",
    "extra_data",
    "other",
]


class GuardDiagnosticV2(Immutable):
    """All output fields are fixed enums, booleans, bounded offsets or v1 hashes."""

    protocol: Literal["guard_structural_diagnostic_v2"] = "guard_structural_diagnostic_v2"
    baseline: GuardDiagnostic
    framing: Framing
    terminal_fence: bool
    syntax_kind: SyntaxKind
    error_offset: int | None = Field(default=None, ge=0, le=MAX_DIAGNOSTIC_CHARS)
    error_at_end: bool | None = None
    trailing_comma_at_error: bool | None = None


def diagnose(text: str) -> GuardDiagnosticV2:
    """A framing hint never implies parse success or a recoverable truncated response.

    No exception message, response slice, field value, decoded payload or reasoning
    is retained. The v1 parser classification stays authoritative. Not wired into
    the frozen native worker; rollout requires a separate versioned adapter.
    """
    baseline = diagnose_v1(text)
    if len(text) > MAX_DIAGNOSTIC_CHARS:
        return GuardDiagnosticV2(
            baseline=baseline,
            framing="not_inspected",
            terminal_fence=False,
            syntax_kind="none",
        )
    stripped = text.strip()
    framing: Framing = (
        "empty"
        if not stripped
        else "fenced"
        if stripped.startswith("```")
        else "object"
        if stripped.startswith("{")
        else "array"
        if stripped.startswith("[")
        else "other"
    )
    if baseline.category != "json_syntax":
        return GuardDiagnosticV2(
            baseline=baseline,
            framing=framing,
            terminal_fence=stripped.endswith("```"),
            syntax_kind="none",
        )
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        messages: dict[str, SyntaxKind] = {
            "Expecting value": "expected_value",
            "Expecting property name enclosed in double quotes": "expected_key",
            "Expecting ':' delimiter": "expected_colon",
            "Expecting ',' delimiter": "expected_comma",
            "Extra data": "extra_data",
        }
        kind = messages.get(exc.msg, "other")
        for prefix, label in (
            ("Unterminated string", "unterminated_string"),
            ("Invalid \\escape", "invalid_escape"),
            ("Invalid \\uXXXX escape", "invalid_escape"),
            ("Invalid control character", "invalid_control"),
        ):
            if exc.msg.startswith(prefix):
                kind = cast(SyntaxKind, label)
        offset = exc.pos
        return GuardDiagnosticV2(
            baseline=baseline,
            framing=framing,
            terminal_fence=stripped.endswith("```"),
            syntax_kind=kind,
            error_offset=offset,
            error_at_end=offset == len(text),
            trailing_comma_at_error=(
                offset < len(text) and text[offset] in "}]" and text[:offset].rstrip().endswith(",")
            ),
        )
    # v1 already checked the same bounded JSON input; fail loudly if parsing
    # disagrees instead of silently publishing inconsistent diagnostic evidence.
    raise ValueError("structural diagnostic parser disagreement")
