"""Opt-in terminal-line-ending normalization for the exact-email ablation.

This profile is deliberately narrower than the general Unicode/security views.
It does not trim spaces, fold Unicode, remove controls, or change an internal
line ending.  It only removes one terminal ``LF``, ``CRLF`` or ``CR`` from a
candidate value, and rejects a candidate with two or more terminal line
endings.  The raw and released hashes are returned together so a caller can
bind the normalized release to the exact observed proposal.

The profile is an ablation component.  It is not wired into the frozen
mainline A0--A6 runtime and therefore cannot alter its results implicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from react_agent.foundation.normalization import text_hash

PROFILE = "terminal_line_ending_v1"
MAX_BYTES = 131_072
Status = Literal["exact", "normalized", "reject"]


@dataclass(frozen=True)
class TerminalLineNormalization:
    profile: str
    status: Status
    raw_text: str
    released_text: str
    raw_sha256: str
    released_sha256: str
    operation: str

    @property
    def changed(self) -> bool:
        return self.raw_text != self.released_text


def normalize_terminal_line_ending(text: str) -> TerminalLineNormalization:
    """Return a bounded, auditable canonical candidate.

    An empty string, oversized UTF-8 value, or repeated terminal line ending
    is rejected.  A value with no terminal line ending is exact.  A value with
    exactly one terminal line ending is normalized by removing that ending.
    The function never mutates the input and never performs network I/O.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text or len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("non-empty bounded UTF-8 text required")

    operation = "identity"
    released = text
    status: Status = "exact"
    if text.endswith("\r\n"):
        released = text[:-2]
        operation = "remove_one_terminal_crlf"
    elif text.endswith(("\n", "\r")):
        released = text[:-1]
        operation = "remove_one_terminal_lf_or_cr"

    if not released:
        status = "reject"
        released = ""
        operation = "reject_empty_after_terminal_line_ending"
    elif released.endswith(("\n", "\r")):
        # A second terminal line ending is ambiguous and must remain blocked.
        status = "reject"
        released = ""
        operation = "reject_repeated_terminal_line_ending"
    elif released != text:
        status = "normalized"

    return TerminalLineNormalization(
        profile=PROFILE,
        status=status,
        raw_text=text,
        released_text=released,
        raw_sha256=text_hash(text),
        released_sha256=text_hash(released),
        operation=operation,
    )


def canonical_email_equivalent(candidate: str, expected: str) -> TerminalLineNormalization:
    """Compare a candidate with a predeclared canonical email value.

    The expected value must already be canonical (no terminal line ending).
    The returned status is ``reject`` for any mismatch, including trailing
    spaces, extra prose, repeated line endings, and private-marker text.
    """

    normalized = normalize_terminal_line_ending(candidate)
    if expected.endswith(("\n", "\r")) or not expected:
        raise ValueError("expected value must be non-empty and canonical")
    if normalized.status == "reject" or normalized.released_text != expected:
        return TerminalLineNormalization(
            profile=PROFILE,
            status="reject",
            raw_text=candidate,
            released_text="",
            raw_sha256=normalized.raw_sha256,
            released_sha256=text_hash(""),
            operation="reject_exact_canonical_mismatch",
        )
    return normalized
