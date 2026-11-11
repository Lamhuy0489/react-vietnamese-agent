"""Test-3 spec: 48 balanced families, file matches the deterministic build."""

from __future__ import annotations

import json
from pathlib import Path

from react_agent.authoring.v3 import spec as v3
from react_agent.authoring.v3 import spec_test3 as t3

ROOT = Path(__file__).resolve().parents[2]


def test_spec_valid_and_on_disk() -> None:
    spec = t3.build_spec()
    assert t3.validate_spec(spec) == []
    assert len(spec["families"]) == 48 and t3.fixture_count(spec) == 560
    assert json.loads((ROOT / t3.SPEC_PATH).read_text(encoding="utf-8")) == spec
    assert "data/adversarial/release_v3" in spec["generation_rules"]["novelty"]["reference"]


def test_no_axis_combination_copied_from_v3() -> None:
    def key(f: dict) -> tuple:  # type: ignore[type-arg]
        return tuple(f[k] for k in ("mechanism", "detail", "vector", "persuasion", "placement",
                                    "tone", "structure", "constraint", "sector", "user_sink"))
    old = {key(f) for f in v3.build_spec()["families"]}
    assert not any(key(f) in old for f in t3.build_spec()["families"])


def test_v3_spec_unchanged() -> None:
    assert v3.validate_spec(json.loads((ROOT / v3.SPEC_PATH).read_text(encoding="utf-8"))) == []
