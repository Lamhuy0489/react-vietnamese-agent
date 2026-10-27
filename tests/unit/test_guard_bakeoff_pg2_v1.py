from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/run_guard_bakeoff_pg2_v1.py"
spec = importlib.util.spec_from_file_location("bakeoff", SCRIPT)
assert spec and spec.loader
bakeoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bakeoff)


def labels(n: int) -> dict[str, dict[str, str]]:
    return {f"a{i}": {"branch": "attack"} for i in range(n)} | {
        f"b{i}": {"branch": "benign"} for i in range(n)}


def test_challenger_wins_only_with_more_recall_inside_flag_bound() -> None:
    scores = {f"a{i}": 0.9 if i < 30 else 0.1 for i in range(40)} | {
        f"b{i}": 0.9 if i < 6 else 0.1 for i in range(40)}
    report = bakeoff.score(scores, labels(40))
    assert report["prompt_guard2_86m"] == {"TP": 30, "FN": 10, "FP": 6, "TN": 34}
    assert report["selected"] == "prompt_guard2_86m"


def test_over_bound_or_tie_keeps_incumbent() -> None:
    noisy = {f"a{i}": 0.9 for i in range(40)} | {f"b{i}": 0.9 if i < 7 else 0.0 for i in range(40)}
    assert bakeoff.score(noisy, labels(40))["selected"] == "llama32_3b_prompted"
    tie = {f"a{i}": 0.9 if i < 21 else 0.0 for i in range(40)} | {f"b{i}": 0.0 for i in range(40)}
    assert bakeoff.score(tie, labels(40))["selected"] == "llama32_3b_prompted"
