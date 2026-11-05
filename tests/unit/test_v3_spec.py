"""VN-AgentInject v3 spec: deterministic, balanced, and equal to the committed file."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from react_agent.authoring.v3 import spec as v3

ROOT = Path(__file__).resolve().parents[2]


def test_build_is_deterministic_and_valid() -> None:
    first, second = v3.build_spec(), v3.build_spec()
    assert first == second
    assert v3.validate_spec(first) == []


def test_committed_spec_matches_build() -> None:
    committed = (ROOT / v3.SPEC_PATH).read_text(encoding="utf-8")
    assert committed == v3.dumps(v3.build_spec())


def test_counts() -> None:
    spec = v3.build_spec()
    splits = Counter(f["split"] for f in spec["families"])
    assert splits == {"pilot": 12, "dev": 48, "test": 72}
    assert Counter(f["split"] for f in spec["families"] if f["b_auth"]) == {
        "pilot": 4, "dev": 16, "test": 24}
    assert v3.fixture_counts(spec) == {"pilot": 28, "dev": 560, "test": 840}


def test_mechanism_constraints() -> None:
    for f in v3.build_spec()["families"]:
        if f["mechanism"] == "M6":
            assert f["user_sink"] == "none"
        assert f["detail"] in v3.DETAILS[f["mechanism"]]


def test_validator_catches_imbalance() -> None:
    spec = v3.build_spec()
    broken = json.loads(json.dumps(spec))
    test_m1 = [f for f in broken["families"] if f["split"] == "test" and f["mechanism"] == "M1"]
    for f in test_m1:
        f["vector"], f["trigger_tool"] = "document", "doc_read"
    problems = v3.validate_spec(broken)
    assert any("axis vector unbalanced" in p for p in problems)


def test_validator_catches_bad_detail_and_duplicates() -> None:
    broken = json.loads(json.dumps(v3.build_spec()))
    broken["families"][0]["detail"] = "nonsense"
    broken["families"][1]["family_id"] = broken["families"][2]["family_id"]
    problems = v3.validate_spec(broken)
    assert any("not allowed" in p for p in problems)
    assert "duplicate family_id" in problems
