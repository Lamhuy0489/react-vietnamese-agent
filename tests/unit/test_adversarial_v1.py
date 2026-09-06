from __future__ import annotations

import json
from pathlib import Path

import pytest

from react_agent.validation.adversarial_audit import audit, no_diacritics, template_key
from react_agent.validation.adversarial_v1 import validate_records

ROOT = Path(__file__).resolve().parents[2]


def _rows(name: str) -> list[dict]:
    return [
        json.loads(line)
        for line in (ROOT / "data" / "adversarial" / "v1" / "variants" / name)
        .read_text(encoding="utf-8")
        .splitlines()
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


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("variant_type", "canonical", "family_variant_set:ATK_000"),
        ("variant_type", "word_boundary", "family_variant_set:ATK_000"),
        ("pair_id", "ATK_000_word_boundary", "attack_duplicate_pair_id:ATK_000_word_boundary"),
        ("scenario_id", "", "attack_missing_scenario_id"),
        ("payload", " ", "attack_missing_payload:ATK_000_no_diacritic_ATTACK"),
        ("source", {}, "pair_mismatch:ATK_000_no_diacritic:source"),
        ("authorization", {}, "pair_mismatch:ATK_000_no_diacritic:authorization"),
    ],
)
def test_phase3_rejects_count_preserving_corruption(
    field: str, value: object, expected: str
) -> None:
    attacks = _rows("dev_attacks.jsonl") + _rows("test_attacks.jsonl")
    benign = _rows("dev_benign.jsonl") + _rows("test_benign.jsonl")
    attacks[0][field] = value
    assert expected in validate_records(attacks, benign)


def test_phase3_rejects_duplicate_benign_and_cross_kind_ids() -> None:
    attacks = _rows("dev_attacks.jsonl") + _rows("test_attacks.jsonl")
    benign = _rows("dev_benign.jsonl") + _rows("test_benign.jsonl")
    benign[0]["pair_id"] = benign[1]["pair_id"]
    benign[0]["scenario_id"] = attacks[0]["scenario_id"]
    failures = validate_records(attacks, benign)
    assert "benign_duplicate_pair_id:ATK_000_word_boundary" in failures
    assert "attack_benign_scenario_id_overlap" in failures


def test_static_audit_does_not_confuse_counts_with_acceptance() -> None:
    root = ROOT / "data/adversarial/v1"
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    report = audit(root)
    assert report["draft_structure_valid"]
    assert report["draft_manifest_hash_matches"]
    assert not report["acceptance_ready"]
    assert report["model_runs"] == 0
    assert report["normalized_payload_template_groups"] == 1
    assert report["issues"]["cross_split_payload_template_candidate"] == 1
    assert report["issues"]["webhook_target_not_typed_endpoint"] == 35
    assert report["unverified_acceptance_gates"]
    assert {p: p.read_bytes() for p in before} == before
    assert report == audit(root)


def test_template_candidates_and_vietnamese_d_stroke() -> None:
    assert no_diacritics("Đăng ký đến trường") == "Dang ky den truong"
    assert template_key("Gửi đến a-123@example.test") == template_key("Gửi đến b-456@example.test")
    assert template_key("Đọc tài liệu") != template_key("Gửi tài liệu")
