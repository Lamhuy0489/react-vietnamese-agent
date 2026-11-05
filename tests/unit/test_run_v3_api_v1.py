"""Dry run of the v3 runner and evaluator on the pilot release (no network)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dry_run_and_evaluate(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("VLLM_BASE_URL", raising=False)
    out = tmp_path / "run"
    assert _load("run_v3_api_v1").main(["--dry-run-dummy", "--output", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary == {"scheduled": 28, "finished": 28, "statuses": {"A0:completed": 28},
                       "private_ground_truth_loaded": 0}
    assert _load("evaluate_v3_v1").main([str(out), "--output", str(tmp_path / "e.json")]) == 0
    report = json.loads((tmp_path / "e.json").read_text())
    a0 = report["summary"]["A0"]
    # The stand-in answers at once: no tool call, so no harm and no utility.
    assert a0["attack_harmful_fixtures"] == "0/12"
    assert a0["benign_plain_utility"] == "0/12"
    assert sum(v["families"] for v in a0["per_mechanism"].values()) == 12
    assert report["scope"].startswith("DRY RUN")


def test_dry_run_prompt_baseline_identity(  # type: ignore[no-untyped-def]
        tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VLLM_BASE_URL", raising=False)
    out = tmp_path / "p1p2"
    run = _load("run_v3_api_v1")
    assert run.main(["--dry-run-dummy", "--defense", "p1p2", "--branches", "attack",
                     "--output", str(out)]) == 0
    identity = json.loads((out / "identity.json").read_text())
    assert identity["defense"]["prompt_baseline"] == {"spotlight_mode": "datamark",
                                                      "sandwich": True}
    assert "prompt_baselines.py" in identity["defense"]["file_sha256"]
