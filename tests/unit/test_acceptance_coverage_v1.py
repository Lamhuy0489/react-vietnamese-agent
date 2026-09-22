"""Pinned public Dev selection only; no Test fixture loader."""

import copy
from pathlib import Path

import pytest

from react_agent.validation.acceptance_coverage_v1 import coverage, validate_coverage

RELEASE = Path(__file__).resolve().parents[2] / "data/adversarial/release_v2"


def test_pairs_and_anchors_are_not_quality_claims():
    value = coverage(RELEASE)
    assert value == coverage(RELEASE)
    assert value["public_cases"] == 16 and value["candidate_runtime_tasks"] == 32
    assert len({r["pair_id"] for r in value["cases"]}) == 8
    assert not value["dispatch_allowed"] and not value["guard_quality_validated"]
    assert len(value["missing_destination_anchors"]) == 6
    for family in {r["family_id"] for r in value["cases"]}:
        paired = [r for r in value["cases"] if r["family_id"] == family]
        assert {r["branch"] for r in paired} == {"attack", "benign"}
        assert paired[0]["task_sha256"] == paired[1]["task_sha256"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("dispatch_allowed", True),
        ("candidate_runtime_tasks", 30),
        ("phase5_accepted", True),
        ("missing_destination_anchors", []),
    ],
)
def test_tampering_rejected(key, value):
    original = coverage(RELEASE)
    changed = copy.deepcopy(original)
    changed[key] = value
    with pytest.raises(ValueError, match="coverage identity"):
        validate_coverage(changed, RELEASE)


def test_linked_seal_rejected_before_load(tmp_path):
    (tmp_path / "seal.json").symlink_to(RELEASE / "seal.json")
    with pytest.raises(ValueError):
        coverage(tmp_path)
