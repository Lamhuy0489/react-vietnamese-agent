from __future__ import annotations

import json
from pathlib import Path

from react_agent.validation.adversarial_v1 import validate_records

ROOT = Path(__file__).resolve().parents[2]


def _rows(name: str) -> list[dict]:
    return [
        json.loads(line)
        for line in (ROOT / "data" / "adversarial" / "v1" / "variants" / name).read_text(
            encoding="utf-8"
        ).splitlines()
    ]


def test_phase3_draft_has_exact_counts_and_pairs() -> None:
    attacks = _rows("dev_attacks.jsonl") + _rows("test_attacks.jsonl")
    benign = _rows("dev_benign.jsonl") + _rows("test_benign.jsonl")
    assert validate_records(attacks, benign) == []


def test_phase3_validator_detects_cross_split_family() -> None:
    attacks = _rows("dev_attacks.jsonl") + _rows("test_attacks.jsonl")
    benign = _rows("dev_benign.jsonl") + _rows("test_benign.jsonl")
    attacks[0]["split"] = "test"
    assert "family_cross_split:ATK_000" in validate_records(attacks, benign)

