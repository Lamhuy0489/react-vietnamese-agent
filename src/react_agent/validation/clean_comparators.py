"""Deterministic typed comparisons; no model, network, or evaluator prompt access."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from datetime import date
from typing import Any

from react_agent.broker import ToolBroker
from react_agent.schemas.clean_task import AnswerFact, ArgumentValidator
from react_agent.schemas.tool import ToolResult


def normalize(value: object) -> str:
    return " ".join(unicodedata.normalize("NFC", str(value)).casefold().split())


def number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    text = str(value).strip()
    if re.fullmatch(r"[-+]?\d{1,3}(?:[.,]\d{3})+", text):
        text = text.replace(",", "").replace(".", "")
    elif "," in text and "." not in text:
        text = text.replace(",", ".")
    try:
        parsed = float(text)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def compare(actual: object, expected: object, comparator: str, tolerance: float = 0) -> bool:
    if comparator in {"numeric_equal", "numeric_tolerance"}:
        left, right = number(actual), number(expected)
        return left is not None and right is not None and abs(left - right) <= tolerance
    if comparator == "boolean_equal":
        return isinstance(actual, bool) and isinstance(expected, bool) and actual == expected
    if comparator in {"set_equal", "set_contains"}:
        if not isinstance(actual, list) or not isinstance(expected, list):
            return False
        left_set, right_set = {normalize(x) for x in actual}, {normalize(x) for x in expected}
        return left_set == right_set if comparator == "set_equal" else left_set >= right_set
    if comparator == "substring_normalized":
        return phrase_present(str(actual), str(expected))
    if comparator in {"exact_normalized", "case_insensitive", "entity_id_equal", "date_equal"}:
        return normalize(actual) == normalize(expected)
    raise ValueError(f"unsupported scalar comparator: {comparator}")


def phrase_present(text: str, phrase: str) -> bool:
    return (
        re.search(r"(?<!\w)" + re.escape(normalize(phrase)) + r"(?!\w)", normalize(text))
        is not None
    )


def fact_in_text(answer: str, fact: AnswerFact) -> bool:
    if fact.comparator in {"numeric_equal", "numeric_tolerance"}:
        tokens = re.findall(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)*(?![\w.])", answer)
        return any(
            compare(token, fact.value, fact.comparator, fact.tolerance or 0) for token in tokens
        )
    if fact.comparator == "date_equal":
        for year, month, day in re.findall(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", answer):
            try:
                if date(int(year), int(month), int(day)).isoformat() == fact.value:
                    return True
            except ValueError:
                continue
        for day, month, year in re.findall(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", answer):
            try:
                if date(int(year), int(month), int(day)).isoformat() == fact.value:
                    return True
            except ValueError:
                continue
        return False
    if fact.comparator in {"set_equal", "set_contains"}:
        for candidate in re.findall(r"\[[^\[\]]*\]", answer):
            try:
                if compare(json.loads(candidate), fact.value, fact.comparator):
                    return True
            except (ValueError, TypeError):
                continue
        return False
    if fact.comparator == "boolean_equal":
        return phrase_present(answer, "true" if fact.value is True else "false")
    return phrase_present(answer, str(fact.value))


def fact_in_content(content: object, fact: AnswerFact) -> bool:
    if isinstance(content, dict):
        return any(fact_in_content(value, fact) for value in content.values())
    if isinstance(content, list):
        if fact.comparator in {"set_equal", "set_contains"}:
            if compare(content, fact.value, fact.comparator):
                return True
        return any(fact_in_content(value, fact) for value in content)
    if isinstance(content, str):
        if fact.comparator in {"set_equal", "set_contains"} and isinstance(fact.value, list):
            # Source prose can contain other facts; availability of the required
            # set members is distinct from exact-set scoring of the final answer.
            return all(phrase_present(content, member) for member in fact.value)
        return fact_in_text(content, fact)
    return compare(content, fact.value, fact.comparator, fact.tolerance or 0)


def nested_argument(arguments: dict[str, Any], path: str) -> object:
    value: object = arguments
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def argument_matches(
    validator: ArgumentValidator,
    arguments: dict[str, Any],
    result: ToolResult,
    broker: ToolBroker,
) -> bool:
    if not result.ok:
        return False
    value = nested_argument(arguments, validator.argument)
    if value is None:
        return False
    if validator.comparator == "retrieval_target":
        if not isinstance(result.content, dict):
            return False
        rows = result.content.get("results")
        if not isinstance(rows, list):
            return False
        ids = {
            row.get("doc_id", row.get("page_id")) for row in rows if isinstance(row, dict)
        }
        return set(validator.retrieval_targets) <= ids
    if validator.comparator == "db_result_equivalent":
        reference = broker.execute(
            "db_query",
            {"query": validator.reference_sql},
            run_id="qa_reference",
            task_id="qa_reference",
            step=0,
        )
        if (
            not reference.ok
            or not isinstance(reference.content, dict)
            or not isinstance(result.content, dict)
        ):
            return False
        # Column aliases and row ordering are not SQL-result semantics; preserve
        # multiplicity and column position. All reference queries are read-only.
        expected = sorted(json.dumps(row, ensure_ascii=False) for row in reference.content["rows"])
        actual = sorted(json.dumps(row, ensure_ascii=False) for row in result.content["rows"])
        return actual == expected
    if validator.tool == "calculator" and validator.argument == "expression":
        reference = broker.execute(
            "calculator",
            {"expression": validator.expected},
            run_id="qa_reference",
            task_id="qa_reference",
            step=0,
        )
        return reference.ok and reference.content == result.content
    return compare(value, validator.expected, validator.comparator)
