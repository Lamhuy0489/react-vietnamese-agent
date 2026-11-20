"""final_config_v5: pinned hashes, matrix, Test-4 gates of run_v3_api_v4 and evaluate_v3_v3."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from react_agent.evaluation import final_config_v5 as fc

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_root(tmp_path: Path) -> Path:
    for name in (*fc.FROZEN_FILES, "src/react_agent/a.py", "configs/b.yaml"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name, encoding="utf-8")
    return tmp_path


def test_verify_detects_change_and_missing(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    with pytest.raises(fc.FrozenConfigError):
        fc.verify(root)
    manifest = fc.build(root, {"test_matrix": {"m": ["V3P2"]}})
    (root / fc.MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    (root / fc.MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
    assert fc.verify(root)["files_sha256"] == manifest["files_sha256"]
    assert fc.MANIFEST.as_posix() not in manifest["files"]
    assert fc.ADAPTIVE in manifest["files"]
    (root / fc.ADAPTIVE).write_text("changed", encoding="utf-8")
    with pytest.raises(fc.FrozenConfigError, match="adaptive_test4_attack"):
        fc.verify(root)


def test_allowed_matrix() -> None:
    manifest = {"decisions": {"test_matrix": {"m": ["V3P2", "V3P2-C1"]}}}
    assert fc.allowed(manifest, "m", "V3P2-C1")
    assert not fc.allowed(manifest, "m", "SAN") and not fc.allowed(manifest, "x", "V3P2")


def test_freeze_matrix_names_match_runner() -> None:
    runner, freeze = _load("run_v3_api_v4"), _load("freeze_final_config_v5")
    names = {runner.config_name(["A0"], None), runner.config_name(["A0"], "p2"),
             runner.config_name(["A0"], "prg"), runner.config_name(["A1"], "d2p2"),
             *(runner.config_name(["A1"], d) for d in runner.V3)}
    assert names == set(freeze.MATRIX)


def _patch_manifest(monkeypatch: pytest.MonkeyPatch, module: Any, matrix: list[str]) -> None:
    monkeypatch.setattr(module.final_config_v5, "verify",
                        lambda root: {"decisions": {"test_matrix": {"qwen35_9b": matrix}}})
    monkeypatch.setattr(module.final_config_v5, "manifest_sha256", lambda root: "f" * 64)


def test_runner_refuses_test4_without_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load("run_v3_api_v4")

    def missing(root: Path) -> dict[str, Any]:
        raise fc.FrozenConfigError("missing")

    monkeypatch.setattr(runner.final_config_v5, "verify", missing)
    with pytest.raises(SystemExit, match="Test-4 refused: missing"):
        runner.main(["--release", "test4", "--model-key", "qwen35_9b", "--levels", "A1",
                     "--defense", "v3p2", "--dry-run-dummy", "--output", "/nonexistent"])


@pytest.mark.parametrize("extra, message", [
    (["--levels", "A1", "--defense", "d3dest"], "not in the matrix"),
    (["--levels", "A1", "--defense", "v3p2", "--branches", "attack"], "all branches"),
    (["--levels", "A1", "--defense", "v3p2", "--fixtures", "x.jsonl"], "--fixtures may only"),
    (["--levels", "A1", "--defense", "v3p2", "--max-new-tokens", "9"], "Dev-only"),
])
def test_runner_test4_gate(monkeypatch: pytest.MonkeyPatch, extra: list[str],
                           message: str) -> None:
    runner = _load("run_v3_api_v4")
    _patch_manifest(monkeypatch, runner, ["V3P2"])
    with pytest.raises(SystemExit, match=message):
        runner.main(["--release", "test4", "--model-key", "qwen35_9b", "--dry-run-dummy",
                     "--output", "/nonexistent", *extra])


def test_runner_test4_gate_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load("run_v3_api_v4")
    _patch_manifest(monkeypatch, runner, ["V3P2"])
    args = runner.argparse.Namespace(
        levels=["A1"], defense="v3p2", model_key="qwen35_9b",
        branches=list(runner.rel.BRANCH_CODE), fixtures=ROOT / fc.ADAPTIVE, max_new_tokens=None)
    assert runner.test4_gate(args) == "f" * 64


def test_evaluator_test4_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    ev = _load("evaluate_v3_v3")
    _patch_manifest(monkeypatch, ev, [])
    with pytest.raises(SystemExit, match="not made under"):
        ev.test4_gate({"final_config_v5_sha256": "0" * 64})
    ev.test4_gate({"final_config_v5_sha256": "f" * 64})
    assert ev.ORACLES["test4"] == "private/test_oracles.json"


def test_test4_fixtures_parse() -> None:
    """Every sealed Test-4 row and adaptive row validates as FixtureV3 (split test4, T5 ids)."""
    from react_agent.authoring.v3 import release as rel

    files = [*(ROOT / "data/adversarial/release_test4").glob("test4_*.jsonl"), ROOT / fc.ADAPTIVE]
    rows = [rel.FixtureV3.model_validate_json(line) for path in files
            for line in path.read_text(encoding="utf-8").splitlines() if line]
    assert len(rows) == 584 and {row.split for row in rows} == {"test4"}
