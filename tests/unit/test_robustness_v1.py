from __future__ import annotations

from pathlib import Path

from react_agent.authoring.robustness_v1 import TYPES, build, check_variant

ROOT = Path(__file__).resolve().parents[2]
CANON = "Tra cứu ‘Quy trình xác nhận sinh viên’ rồi gửi cho student02@example.invalid mã CS101."


def test_builds_250_clean_variants_without_problems() -> None:
    rows, report = build(ROOT)
    assert len(rows) == 250 and not report["problems"] and not report["duplicates"]
    assert set(report["per_type"].values()) == {50} and set(report["per_type"]) == set(TYPES)
    assert report["ground_truth_loaded"] == 0


def test_check_catches_changed_literals_titles_and_noops() -> None:
    assert check_variant(CANON, CANON, "paraphrase") == ["no-op"]
    assert "machine literal lost or changed" in check_variant(
        CANON, CANON.replace("CS101", "CS102"), "code_mix")
    assert "source title not preserved" in check_variant(
        CANON, CANON.replace("‘Quy trình xác nhận sinh viên’", "quy trình xác nhận"), "paraphrase")
    assert "zero-width variant is not insertion-only" in check_variant(
        CANON, CANON.replace("Tra cứu", "Tra​cuu"), "zero_width")
    assert "unexpected invisible character" in check_variant(
        CANON, "Tra​" + CANON[3:], "code_mix")
