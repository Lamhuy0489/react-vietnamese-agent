import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_kernel_module() -> ModuleType:
    path = ROOT / "notebooks" / "kaggle" / "phase1_kernel.py"
    spec = importlib.util.spec_from_file_location("phase1_kernel", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_expanded_bundle_discovery_hash_and_import_path(
    tmp_path: Path,
) -> None:
    kernel = load_kernel_module()
    input_root = tmp_path / "input"
    bundle_root = input_root / "datasets" / "owner" / "bundle"
    expanded_root = bundle_root / "react-vietnamese-agent-phase1"
    package = expanded_root / "src" / "react_agent"
    package.mkdir(parents=True)
    package_file = package / "__init__.py"
    package_file.write_text('__version__ = "test"\n', encoding="utf-8")
    manifest = {
        "git_commit": "a" * 40,
        "archive_sha256": "b" * 64,
        "dataset": "owner/bundle",
        "dataset_version": 5,
        "model_source": kernel.MODEL_SOURCE,
        "file_sha256": {
            "src/react_agent/__init__.py": kernel.sha256(package_file),
        },
    }
    bundle_root.mkdir(parents=True, exist_ok=True)
    (bundle_root / "frozen_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    destination = tmp_path / "working" / "react-vietnamese-agent"
    loaded = kernel.prepare_project(input_root, destination)
    assert loaded == manifest
    assert (destination / "src" / "react_agent" / "__init__.py").is_file()


def test_model_discovery_accepts_kaggle_framework_case(tmp_path: Path) -> None:
    kernel = load_kernel_module()
    model = (
        tmp_path
        / "models"
        / "qwen-lm"
        / "qwen2.5"
        / "Transformers"
        / "3b-instruct"
        / "1"
    )
    model.mkdir(parents=True)
    for name in ("config.json", "tokenizer.json", "model.safetensors.index.json"):
        (model / name).write_text("{}", encoding="utf-8")
    assert kernel.find_model_path(tmp_path) == model


def test_frozen_file_hash_rejects_tampering(tmp_path: Path) -> None:
    kernel = load_kernel_module()
    project = tmp_path / "project"
    tracked = project / "tracked.txt"
    tracked.parent.mkdir(parents=True)
    tracked.write_text("expected", encoding="utf-8")
    manifest = {"file_sha256": {"tracked.txt": kernel.sha256(tracked)}}
    tracked.write_text("tampered", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hash:tracked.txt"):
        kernel.verify_frozen_files(project, manifest)
