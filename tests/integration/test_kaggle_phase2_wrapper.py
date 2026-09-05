"""Kaggle Phase 2 wrapper privacy and mount tests."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_kernel() -> ModuleType:
    path = ROOT / "notebooks" / "kaggle" / "phase2_kernel.py"
    spec = importlib.util.spec_from_file_location("phase2_kernel", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase2_bundle_rejects_private_ground_truth(tmp_path: Path) -> None:
    kernel = load_kernel()
    input_root = tmp_path / "input"
    bundle_root = input_root / "dataset"
    project = bundle_root / "expanded"
    package = project / "src" / "react_agent"
    package.mkdir(parents=True)
    package_file = package / "__init__.py"
    package_file.write_text("", encoding="utf-8")
    private = project / "data" / "clean" / "v1" / "private"
    private.mkdir(parents=True)
    (private / "test_ground_truth.jsonl").write_text("{}\n", encoding="utf-8")
    manifest = {
        "git_commit": "a" * 40,
        "archive_sha256": "b" * 64,
        "model_source": kernel.MODEL_SOURCE,
        "file_sha256": {"src/react_agent/__init__.py": kernel.sha256(package_file)},
    }
    (bundle_root / "frozen_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Test or private"):
        kernel.prepare_project(input_root, tmp_path / "working")
