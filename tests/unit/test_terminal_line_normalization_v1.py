from __future__ import annotations

import pytest

from react_agent.security_v1.terminal_line_normalization_v1 import (
    PROFILE,
    canonical_email_equivalent,
    normalize_terminal_line_ending,
)

EXPECTED = "Phòng tiếp nhận hồ sơ: G204."


@pytest.mark.parametrize("suffix", ["", "\n", "\r\n", "\r"])
def test_profile_preserves_raw_hash_and_allows_one_terminal_ending(suffix: str):
    result = canonical_email_equivalent(EXPECTED + suffix, EXPECTED)
    assert result.profile == PROFILE
    assert result.status in {"exact", "normalized"}
    assert result.released_text == EXPECTED
    if suffix:
        assert result.raw_sha256 != result.released_sha256
    else:
        assert result.raw_sha256 == result.released_sha256


@pytest.mark.parametrize(
    "candidate",
    [
        EXPECTED + "\n\n",
        EXPECTED + " ",
        EXPECTED + "\nGhi chú ngoài hồ sơ",
        "Phòng tiếp nhận\nhồ sơ: G204.",
        EXPECTED + " private@example.test",
    ],
)
def test_profile_denies_non_line_ending_mismatch(candidate: str):
    result = canonical_email_equivalent(candidate, EXPECTED)
    assert result.status == "reject"
    assert result.released_text == ""
    assert len(result.raw_sha256) == 64
    assert len(result.released_sha256) == 64


def test_repeated_line_ending_is_fail_closed():
    result = normalize_terminal_line_ending(EXPECTED + "\r\n\n")
    assert result.status == "reject"
    assert result.released_text == ""


def test_line_ending_only_value_is_fail_closed():
    result = normalize_terminal_line_ending("\n")
    assert result.status == "reject"
    assert result.released_text == ""


def test_invalid_bounds_are_rejected():
    with pytest.raises((TypeError, ValueError)):
        normalize_terminal_line_ending("")
    with pytest.raises((TypeError, ValueError)):
        normalize_terminal_line_ending("x" * 131_073)
