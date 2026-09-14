"""Scheduling reads Dev only and never exports task text, overlays or labels."""

import hashlib
import json
from pathlib import Path

import pytest

from react_agent.validation import grouped_dev_plan_v1 as planner
from react_agent.validation.grouped_dev_plan_v1 import plan

ROOT = Path(__file__).resolve().parents[2]


def test_real_dev_selection_is_stable_and_metadata_only(monkeypatch):
    read = Path.read_bytes
    seen = []

    def guarded(path):
        assert path.name in {"dev_attack.jsonl", "dev_benign.jsonl"}
        seen.append(path.name)
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    first = plan(ROOT / "data/adversarial/release_v2")
    assert plan(ROOT / "data/adversarial/release_v2") == first
    assert len(first["selected_pairs"]) == 8
    assert len(set(first["selected_families"])) == 8
    assert len(first["remaining_dev_families"]) == 32
    assert not first["dispatch_allowed"] and not first["test_payload_accessed"]
    assert all(
        set(meta) == {"variant_id", "pair_id", "family_id", "group_id", "variant_type"}
        for pair in first["selected_pairs"]
        for meta in pair.values()
    )
    assert seen == ["dev_attack.jsonl", "dev_benign.jsonl"] * 2


@pytest.mark.parametrize("fault", ["split", "branch", "duplicate", "group", "missing", "variant"])
def test_bad_geometry_rejected(monkeypatch, fault):
    original = Path.read_bytes
    pins = dict(planner.DEV_SHA256)
    monkeypatch.setattr(planner, "DEV_SHA256", pins)

    def read(path):
        rows = [json.loads(line) for line in original(path).splitlines()]
        if path.name == "dev_benign.jsonl":
            if fault == "split":
                rows[0]["split"] = "test"
            elif fault == "branch":
                rows[0]["branch"] = "attack"
            elif fault == "duplicate":
                rows[0]["variant_id"] = rows[1]["variant_id"]
            elif fault == "group":
                rows[0]["group_id"] = "OTHER"
            elif fault == "missing":
                rows.pop()
            elif fault == "variant":
                rows[0]["variant_type"] = "other"
        raw = "\n".join(json.dumps(row) for row in rows).encode()
        pins[path.name] = hashlib.sha256(raw).hexdigest()
        return raw

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError):
        plan(ROOT / "data/adversarial/release_v2")


def test_unsealed_bytes_rejected(monkeypatch):
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: original(p) + b"\n")
    with pytest.raises(ValueError, match="source hash"):
        plan(ROOT / "data/adversarial/release_v2")
