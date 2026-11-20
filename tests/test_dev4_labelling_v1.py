"""Dev v4 labelling sheets (rules frozen 2026-11-15): inventory coverage and kappa."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dev4_labelling_v1",
                                              ROOT / "scripts/dev4_labelling_v1.py")
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_inventory_covers_all_families() -> None:
    rows = mod.inventory()
    assert len({r["family_id"] for r in rows}) == 168
    assert all(set(r) == {"family_id", "source_id", "kind", "current_sensitivity", "trust",
                          "branches"} for r in rows)


def test_cohen_kappa() -> None:
    assert mod.cohen_kappa([True, False, True, False], [True, False, True, False]) == 1.0
    assert mod.cohen_kappa([True, True, False, False], [True, False, True, False]) == 0.0
