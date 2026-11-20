"""Test-4 authoring spec (decision log 2026-11-15 16:30): balanced, new ids, file matches build."""

from __future__ import annotations

import json
from pathlib import Path

from react_agent.authoring.v3 import spec_test4 as t4

ROOT = Path(__file__).resolve().parents[1]


def test_spec_valid_and_matches_file() -> None:
    spec = t4.build_spec()
    assert t4.validate_spec(spec) == []
    assert json.loads((ROOT / t4.SPEC_PATH).read_text(encoding="utf-8")) == spec
    assert len(spec["families"]) == 48 and t4.fixture_count(spec) == 560
    assert all(f["family_id"].startswith("T5_") for f in spec["families"])
    assert "data/adversarial/release_dev4" in spec["generation_rules"]["novelty"]["reference"]
