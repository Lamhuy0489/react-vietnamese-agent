"""Test-3 split: spec rows, release folder, oracle path, final_config_v4 gating."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from react_agent.authoring.v3 import release as rel
from react_agent.evaluation import final_config_v4 as fc

ROOT = Path(__file__).resolve().parents[2]


def test_spec_rows_include_test3() -> None:
    rows = rel.load_spec_rows(ROOT)
    t4 = [r for r in rows.values() if r.split == "test3"]
    assert len(t4) == 48 and all(r.family_id.startswith("T4_") for r in t4)
    assert sum(r.split == "test" for r in rows.values()) == 72


def test_release_folder_and_oracles() -> None:
    assert rel.release_folder("test3") == rel.RELEASE_TEST3
    assert rel.release_folder("dev") == rel.RELEASE == rel.release_folder("test")
    assert rel.oracle_path(Path("x"), "test3") == Path("x/private/test_oracles.json")
    assert Path("data/adversarial/release_v3") in rel.NOVELTY_REFERENCES_TEST3


def test_final_config_v4_verify(tmp_path: Path) -> None:
    for name in (*fc.FROZEN_FILES, "src/react_agent/a.py", "configs/final/final_config_v3.json"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name, encoding="utf-8")
    with pytest.raises(fc.FrozenConfigError):
        fc.verify(tmp_path)
    manifest = fc.build(tmp_path, {"test_matrix": {"m": ["D3"]}})
    assert "configs/final/final_config_v3.json" not in manifest["files"]
    (tmp_path / fc.MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
    assert fc.allowed(fc.verify(tmp_path), "m", "D3")
    assert not fc.allowed(manifest, "m", "A0")
    (tmp_path / "src/react_agent/a.py").write_text("changed", encoding="utf-8")
    with pytest.raises(fc.FrozenConfigError, match="src/react_agent/a.py"):
        fc.verify(tmp_path)


def test_runner_refuses_test3_without_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util
    import sys

    monkeypatch.setenv("VLLM_BASE_URL", "x")
    spec = importlib.util.spec_from_file_location("run_v3_api_v1",
                                                  ROOT / "scripts/run_v3_api_v1.py")
    assert spec and spec.loader
    run = importlib.util.module_from_spec(spec)
    sys.modules["run_v3_api_v1"] = run
    spec.loader.exec_module(run)
    if (ROOT / fc.MANIFEST).exists():
        pytest.skip("manifest present")
    with pytest.raises(SystemExit, match="Test-3 refused"):
        run.main(["--split", "test3", "--levels", "A1", "--defense", "d3", "--dry-run-dummy",
                  "--output", "/nonexistent"])
