"""Numeric-token fix for the clean v1.1 evaluator, activated explicitly for rebuild runs.

``clean_comparators.fact_in_text`` extracts numbers with ``(?![\\w.])``, so a value
that ends a sentence ("GPA là 8.0.", "bằng 876.") is never matched. The module is
pinned by the adversarial seal, so the fix lives here (decision log 2026-10-26).
Only the trailing guard changes: a number may be followed by sentence
punctuation, but not by a letter or by ``.``/``,`` plus a digit, so "8.05" still
does not match 8.0. Every other comparator is unchanged.
"""

from __future__ import annotations

import re

import react_agent.validation.clean_comparators as comparators
import react_agent.validation.clean_v11 as scorer
from react_agent.schemas.clean_task import AnswerFact
from react_agent.validation.clean_comparators import compare

EVALUATOR_VERSION = "clean_v1_1_typed_v1+numfix1"
NUMBER_TOKEN = re.compile(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)*(?!\w|[.,]\d)")
_ORIGINAL = comparators.fact_in_text


def fact_in_text(answer: str, fact: AnswerFact) -> bool:
    if fact.comparator in {"numeric_equal", "numeric_tolerance"}:
        return any(compare(token, fact.value, fact.comparator, fact.tolerance or 0)
                   for token in NUMBER_TOKEN.findall(answer))
    return _ORIGINAL(answer, fact)


def activate() -> str:
    """Route the scorer and evidence checks through the fixed matcher."""
    comparators.fact_in_text = fact_in_text
    scorer.fact_in_text = fact_in_text  # type: ignore[attr-defined]
    return EVALUATOR_VERSION


def deactivate() -> None:
    comparators.fact_in_text = _ORIGINAL
    scorer.fact_in_text = _ORIGINAL  # type: ignore[attr-defined]
