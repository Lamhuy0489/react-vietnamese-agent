"""Allowlisted structural diagnostics; never retain model text or validation input.

The frozen parser is authoritative. Diagnostics neither repair a response nor
relax the guard schema. They cannot recover an unretained historical response.
"""

from __future__ import annotations

import hashlib
import json
from typing import Literal, TypedDict, cast

from pydantic import Field, ValidationError

from react_agent.foundation.artifacts import Immutable
from react_agent.security_v1.guard import parse_guard

Category = Literal[
    "valid", "json_syntax", "duplicate_key", "nonfinite_number", "schema", "depth", "size", "other"
]
FieldName = Literal["risk", "labels", "confidence", "root", "other"]
ErrorKind = Literal[
    "missing", "extra_forbidden", "literal_error", "tuple_type", "too_long", "model_type", "other"
]
MAX_DIAGNOSTIC_CHARS = 65_536


class ResponseIdentity(TypedDict):
    response_sha256: str
    response_chars: int


class SchemaIssue(Immutable):
    field: FieldName
    kind: ErrorKind


class GuardDiagnostic(Immutable):
    protocol: Literal["guard_structural_diagnostic_v1"] = "guard_structural_diagnostic_v1"
    category: Category
    parser_checked: bool
    response_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_chars: int = Field(ge=0)
    issues: tuple[SchemaIssue, ...] = ()


def diagnose(text: str) -> GuardDiagnostic:
    """Inspect observable output without emitting text, unknown keys or error messages."""
    common: ResponseIdentity = dict(
        response_sha256=hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest(),
        response_chars=len(text),
    )
    if len(text) > MAX_DIAGNOSTIC_CHARS:
        return GuardDiagnostic(category="size", parser_checked=False, **common)
    try:
        parse_guard(text)
    except ValidationError as exc:
        issues = set()
        # No str(exc), input, context, URL or attacker-controlled field path is retained.
        for error in exc.errors(include_input=False, include_context=False, include_url=False):
            location = error["loc"]
            field: FieldName = "root" if not location else "other"
            if location and location[0] in {"risk", "labels", "confidence"}:
                field = cast(FieldName, location[0])
            kind: ErrorKind = "other"
            if error["type"] in {
                "missing",
                "extra_forbidden",
                "literal_error",
                "tuple_type",
                "too_long",
                "model_type",
            }:
                kind = cast(ErrorKind, error["type"])
            issues.add(SchemaIssue(field=field, kind=kind))
        return GuardDiagnostic(
            category="schema",
            parser_checked=True,
            issues=tuple(sorted(issues, key=lambda i: (i.field, i.kind))),
            **common,
        )
    except json.JSONDecodeError:
        return GuardDiagnostic(category="json_syntax", parser_checked=True, **common)
    except RecursionError:
        return GuardDiagnostic(category="depth", parser_checked=True, **common)
    except ValueError:
        # Reparse only to distinguish structural JSON categories, never to accept.
        duplicate, nonfinite = False, False

        def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
            nonlocal duplicate
            result: dict[str, object] = {}
            for key, value in items:
                duplicate = duplicate or key in result
                result[key] = value
            return result

        def constant(value: str) -> None:
            nonlocal nonfinite
            nonfinite = True

        try:
            json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
        except (ValueError, RecursionError):
            pass  # Authoritative rejection above; no response/exception text escapes.
        category: Category = (
            "duplicate_key" if duplicate else "nonfinite_number" if nonfinite else "other"
        )
        return GuardDiagnostic(category=category, parser_checked=True, **common)
    return GuardDiagnostic(category="valid", parser_checked=True, **common)
