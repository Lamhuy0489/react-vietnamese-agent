"""Synthetic inputs only: telemetry is deterministic, private and non-repairing."""

import json

import pytest
from pydantic import ValidationError

from react_agent.security_v1.guard import parse_guard
from react_agent.security_v1.guard_diagnostics_v1 import MAX_DIAGNOSTIC_CHARS
from react_agent.security_v1.guard_diagnostics_v1 import diagnose as v1
from react_agent.security_v1.guard_diagnostics_v2 import GuardDiagnosticV2, diagnose

VALID = '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'


@pytest.mark.parametrize(
    "text,framing,kind",
    [
        (VALID, "object", "none"),
        ("", "empty", "expected_value"),
        (" \n ", "empty", "expected_value"),
        ("```json\n" + VALID + "\n```", "fenced", "expected_value"),
        ('{"risk":"SAFE",}', "object", "expected_key"),
        ('{"risk" "SAFE"}', "object", "expected_colon"),
        ('{"risk":"SAFE" "confidence":"HIGH"}', "object", "expected_comma"),
        ('{"risk":"SAFE', "object", "unterminated_string"),
        ('{"risk":', "object", "expected_value"),
        (VALID + " trailing synthetic text", "object", "extra_data"),
        ('"\\q"', "other", "invalid_escape"),
        ('"\\uZZZZ"', "other", "invalid_escape"),
        ('"hello\nworld"', "other", "invalid_control"),
        ("[]", "array", "none"),
        ('{"risk":"SAFE","risk":"SAFE"}', "object", "none"),
        ('{"risk":NaN}', "object", "none"),
    ],
)
def test_structural_hints_preserve_authoritative_v1(text, framing, kind):
    result = diagnose(text)
    assert result.baseline == v1(text)
    assert result.framing == framing and result.syntax_kind == kind
    assert result == diagnose(text)
    assert GuardDiagnosticV2.model_validate_json(result.model_dump_json()) == result


def test_fences_are_not_repaired():
    text = "```json\n" + VALID + "\n```"
    result = diagnose(text)
    assert result.terminal_fence and result.baseline.category == "json_syntax"
    with pytest.raises(json.JSONDecodeError):
        parse_guard(text)
    assert diagnose(VALID).baseline.category == "valid"


def test_offsets_no_truncation_claim():
    unfinished = '{"risk":'
    r = diagnose(unfinished)
    assert r.error_offset == len(unfinished) and r.error_at_end
    r = diagnose('{"risk":"SAFE",}')
    assert r.trailing_comma_at_error and not r.error_at_end


@pytest.mark.parametrize(
    "text",
    [
        '{"SYNTHETIC_SECRET_NEVER_LOG_THIS":"SYNTHETIC_PRIVATE_VALUE"}',
        '{"risk":"SYNTHETIC_SECRET_NEVER_LOG_THIS",}',
        "```SYNTHETIC_SECRET_NEVER_LOG_THIS\n{}\n```",
        '"SYNTHETIC_SECRET_NEVER_LOG_THIS\\q"',
    ],
)
def test_no_response_or_exception_text_retained(text):
    encoded = diagnose(text).model_dump_json()
    assert "SYNTHETIC_SECRET_NEVER_LOG_THIS" not in encoded
    assert "SYNTHETIC_PRIVATE_VALUE" not in encoded
    assert "Expecting" not in encoded


def test_size_and_depth_boundaries():
    text = "x" * (MAX_DIAGNOSTIC_CHARS + 1)
    r = diagnose(text)
    assert r.baseline.category == "size" and r.framing == "not_inspected"
    assert r.error_offset is None and r.error_at_end is None
    r = diagnose("[" * 2000 + "0" + "]" * 2000)
    assert r.baseline.category == "depth" and r.syntax_kind == "none"


def test_unicode_hash_and_extra_fields_rejected():
    text = '{"risk":"tổng hợp \\ud800",}'
    assert diagnose(text).baseline == v1(text)
    payload = diagnose(VALID).model_dump()
    payload["raw_text"] = "synthetic"
    with pytest.raises(ValidationError):
        GuardDiagnosticV2.model_validate(payload)
