"""Structural diagnostics never echo arbitrary model content or repair schema."""

import hashlib
import json

import pytest

from react_agent.security_v1.guard import parse_guard
from react_agent.security_v1.guard_diagnostics_v1 import diagnose

SAFE = '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'


@pytest.mark.parametrize(
    "text,category",
    [
        (SAFE, "valid"),
        (" " + SAFE + "\n", "valid"),
        ("```json\n" + SAFE + "\n```", "json_syntax"),
        (SAFE + SAFE, "json_syntax"),
        ("", "json_syntax"),
        ('{"risk":"SAFE","risk":"MALICIOUS","labels":[],"confidence":"HIGH"}', "duplicate_key"),
        ('{"risk":"SAFE","labels":[],"confidence":NaN}', "nonfinite_number"),
        ('{"risk":"SAFE","labels":[],"confidence":Infinity}', "nonfinite_number"),
        ('{"risk":"SAFE","labels":[],"confidence":1e999}', "other"),
        ('{"risk":"UNKNOWN","labels":[],"confidence":"HIGH"}', "schema"),
        ('{"risk":"SAFE","labels":[],"confidence":0.95}', "schema"),
        ('{"risk":"SAFE","labels":["invented"],"confidence":"HIGH"}', "schema"),
        ('{"risk":"SAFE","confidence":"HIGH"}', "schema"),
        ('{"risk":"SAFE","labels":[],"confidence":"HIGH","extra":"x"}', "schema"),
        ("[]", "schema"),
        ("null", "schema"),
        ("[" * 2000 + "]" * 2000, "depth"),
        ("x" * 65537, "size"),
    ],
)
def test_category_and_parser_authority(text, category):
    result = diagnose(text)
    assert result.category == category
    assert result.response_sha256 == hashlib.sha256(text.encode()).hexdigest()
    assert result.response_chars == len(text)
    if category == "valid":
        assert parse_guard(text).risk == "SAFE"
    elif category != "size":
        with pytest.raises((ValueError, RecursionError)):
            parse_guard(text)


@pytest.mark.parametrize("location", ["risk", "labels", "confidence", "extra"])
def test_secret_values_and_unknown_keys_never_retained(location):
    secret = "SYNTHETIC_PRIVATE_CANARY_8f61"  # noqa: S105 - synthetic exclusion fixture
    value = json.loads(SAFE)
    if location == "extra":
        value[secret] = secret
    else:
        value[location] = [secret] if location == "labels" else secret
    result = diagnose(json.dumps(value))
    assert result.category == "schema"
    assert secret not in result.model_dump_json()
    assert result.issues
    assert {i.field for i in result.issues} == ({"other"} if location == "extra" else {location})


def test_missing_fields_and_issue_deduplication():
    missing = diagnose("{}")
    assert {(i.field, i.kind) for i in missing.issues} == {
        (f, "missing") for f in ("risk", "labels", "confidence")
    }
    bad = json.loads(SAFE)
    bad["labels"] = ["SYNTHETIC_INVALID"] * 4
    assert len(diagnose(json.dumps(bad)).issues) == 1
