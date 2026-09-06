"""Deterministic surface drafts with protected literals; not semantic review approval."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

SurfaceKind = Literal["no_diacritic", "word_boundary", "zero_width"]
TOOL_NAMES = (
    "doc_search",
    "doc_read",
    "cached_search",
    "cached_fetch",
    "db_query",
    "calculator",
    "send_email_mock",
    "post_webhook_mock",
)
INVISIBLE = "\u200b\u200c\u200d\ufeff\u2060"


@dataclass(frozen=True)
class SurfaceDraft:
    variant_type: SurfaceKind
    raw: str
    visible_debug: str
    review_status: Literal["pending"] = "pending"


def strip_vietnamese_diacritics(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def draft_surface(
    text: str, kind: SurfaceKind, *, protected_literals: tuple[str, ...] = ()
) -> SurfaceDraft:
    """Produce a candidate only; fail on no-op rather than falsely labelling a variant.

    Tool names, addresses, URLs, mock endpoints and caller-supplied exact data
    literals remain byte-identical. Code-mix/paraphrase require separate authored
    and reviewed candidates; this helper deliberately does not fabricate them.
    """
    if kind not in {"no_diacritic", "word_boundary", "zero_width"}:
        raise ValueError("unsupported mechanical variant; code-mix/paraphrase need authored review")
    if not text.strip() or any(char in text for char in INVISIBLE):
        raise ValueError("canonical must be nonempty and free of pre-existing invisible characters")
    if any(not literal or literal not in text for literal in protected_literals):
        raise ValueError("protected literals must be nonempty and present in canonical")
    literals = sorted(set(TOOL_NAMES + protected_literals), key=lambda item: (-len(item), item))
    pattern = re.compile(
        "(?:"
        + "|".join(re.escape(literal) for literal in literals)
        + r"|(?:https?://|mock://)[^\s<>]+|[\w.+-]+@[\w.-]+)"
    )
    parts: list[str] = []
    offset = 0
    changed_once = False

    def transform(chunk: str) -> str:
        nonlocal changed_once
        if kind == "no_diacritic":
            return strip_vietnamese_diacritics(chunk)
        if changed_once:
            return chunk
        if kind == "word_boundary":
            result, replacements = re.subn(r"(?<=[^\W\d_]) (?=[^\W\d_])", "_", chunk, count=1)
        else:
            # Insert inside a word; do not delete an existing space or alter a target literal.
            result, replacements = re.subn(r"(?<=[^\W\d_])(?=[^\W\d_])", "\u200b", chunk, count=1)
        changed_once = bool(replacements)
        return result

    for match in pattern.finditer(text):
        parts.extend((transform(text[offset : match.start()]), match.group()))
        offset = match.end()
    parts.append(transform(text[offset:]))
    raw = "".join(parts)
    if raw == text:
        raise ValueError("no-op variant; author a suitable canonical or candidate first")
    if kind == "zero_width" and raw.replace("\u200b", "") != text:
        raise ValueError("zero-width transformation must be insertion-only")
    debug = "".join(f"<U+{ord(char):04X}>" if char in INVISIBLE else char for char in raw)
    return SurfaceDraft(kind, raw, debug)
