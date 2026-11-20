"""Dev v4 merge (decision log 2026-11-15 16:30): stratified Dev-val and the merge QA."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_dev_pool_v4",
                                              ROOT / "scripts/build_dev_pool_v4.py")
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_val_families_stratified_and_deterministic() -> None:
    mech = {f"F{i:03d}": f"M{i % 6 + 1}" for i in range(168)}
    val = mod.val_families(mech)
    assert val == mod.val_families(dict(reversed(list(mech.items()))))
    assert len(val) == 6 * mod.VAL_PER_MECHANISM
    assert all(sum(mech[f] == m for f in val) == mod.VAL_PER_MECHANISM
               for m in {f"M{k}" for k in range(1, 7)})


def test_merge_qa_on_sealed_releases() -> None:
    built = mod.build(ROOT)
    privates = built["privates"]
    val = mod.val_families({f: p.mechanism for f, p in privates.items()})
    report = mod.qa(built["fixtures"], privates, built["origin"], val)
    assert report["all"]["families"] == 168
    assert report["all"]["fixtures"] == {"attack": 840, "benign_auth": 280, "benign_plain": 840}
    assert {f.split for f in built["fixtures"]} == {"dev"}
    assert report["dev_val"]["families"] + report["dev_train"]["families"] == 168
