"""Frozen replacement integrity, isolated from model behavior or Test scores."""

from pathlib import Path

from react_agent.validation.clean_v11_seal import validate_seal

ROOT = Path(__file__).resolve().parents[2]


def test_v11_seal_and_cross_category_group_isolation() -> None:
    assert validate_seal(ROOT / "data/clean/v1_1") == []
