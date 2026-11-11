"""final_config_v3: pinned hashes, matrix check and the runner's config names."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from react_agent.evaluation import final_config_v3 as fc

ROOT = Path(__file__).resolve().parents[1]


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
    manifest = fc.build(root, {"test_matrix": {"m": ["D2P2"]}})
    (root / fc.MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    (root / fc.MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
    assert fc.verify(root)["files_sha256"] == manifest["files_sha256"]
    assert fc.MANIFEST.as_posix() not in manifest["files"]
    (root / "src/react_agent/a.py").write_text("changed", encoding="utf-8")
    with pytest.raises(fc.FrozenConfigError, match="src/react_agent/a.py"):
        fc.verify(root)


def test_allowed_matrix() -> None:
    manifest = {"decisions": {"test_matrix": {"m": ["A0", "D2P2"]}}}
    assert fc.allowed(manifest, "m", "D2P2")
    assert not fc.allowed(manifest, "m", "SAN") and not fc.allowed(manifest, "x", "A0")


def test_runner_config_names() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_v3_api_v1 as runner

    assert runner.config_name(["A0"], None) == "A0"
    assert runner.config_name(["A1"], None) == "R1"
    assert runner.config_name(["A1"], "d2p2") == "D2P2"
    assert runner.config_name(["A0"], "p2") == "P2"
    assert runner.config_name(["A0", "A1"], None) is None
