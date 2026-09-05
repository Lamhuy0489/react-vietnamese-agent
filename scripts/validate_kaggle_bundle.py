#!/usr/bin/env python3
"""Simulate Kaggle's expanded Dataset mount before any kernel upload."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "bundle",
        type=Path,
        nargs="?",
        default=ROOT / "build" / "kaggle" / "phase1",
    )
    return parser.parse_args()


def load_kernel() -> ModuleType:
    path = ROOT / "notebooks" / "kaggle" / "phase1_kernel.py"
    spec = importlib.util.spec_from_file_location("phase1_kernel_validation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load Kaggle wrapper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reject_sensitive_paths(paths: list[str]) -> None:
    failures = []
    for path in paths:
        folded = path.casefold()
        if "credential kaggle/" in folded or folded.endswith("kaggle.json"):
            failures.append(path)
        if folded.endswith(".env") and not folded.endswith(".env.example"):
            failures.append(path)
    if failures:
        raise RuntimeError(f"sensitive paths found in frozen manifest: {failures}")


def main() -> int:
    args = parse_args()
    bundle = args.bundle.resolve()
    dataset = bundle / "dataset"
    archive = dataset / "react-vietnamese-agent-phase1.tar.gz"
    manifest_path = dataset / "frozen_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    reject_sensitive_paths(list(manifest["file_sha256"]))
    kernel = load_kernel()
    if kernel.sha256(archive) != manifest["archive_sha256"]:
        raise RuntimeError("local archive hash does not match manifest")

    with tempfile.TemporaryDirectory(prefix="phase1-kaggle-simulation-") as temporary:
        temporary_root = Path(temporary)
        input_root = temporary_root / "kaggle" / "input"
        work_root = temporary_root / "kaggle" / "working"
        mount_root = input_root / "datasets" / "owner" / "bundle"
        expanded_root = mount_root / "react-vietnamese-agent-phase1"
        kernel.safe_extract(archive, expanded_root)
        mount_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_path, mount_root / "frozen_manifest.json")

        model_root = (
            input_root
            / "models"
            / "qwen-lm"
            / "qwen2.5"
            / "Transformers"
            / "3b-instruct"
            / "1"
        )
        model_root.mkdir(parents=True)
        for name in ("config.json", "tokenizer.json", "model.safetensors.index.json"):
            (model_root / name).write_text("{}\n", encoding="utf-8")

        project_root = work_root / "react-vietnamese-agent"
        loaded = kernel.prepare_project(input_root, project_root)
        if loaded != manifest:
            raise RuntimeError("loaded manifest differs from source manifest")
        if kernel.find_model_path(input_root) != model_root:
            raise RuntimeError("model mount discovery mismatch")
        commit = str(manifest["git_commit"])
        kernel.run(project_root, commit, "scripts/build_smoke_environment.py")
        kernel.run(project_root, commit, "scripts/validate_smoke_data.py")
        kernel.run(project_root, commit, "scripts/verify_phase1.py")

    print(
        "PASS: Kaggle expanded-mount simulation, per-file hashes, credential guard, "
        "model discovery, PYTHONPATH, and Phase 1 validators"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
