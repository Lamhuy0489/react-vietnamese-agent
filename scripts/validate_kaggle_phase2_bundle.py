#!/usr/bin/env python3
"""Simulate Phase 2 Kaggle expanded mount and enforce Test/GT exclusion."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import tarfile
import tempfile
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "bundle", type=Path, nargs="?", default=ROOT / "build" / "kaggle" / "phase2"
    )
    return parser.parse_args()


def load_kernel() -> ModuleType:
    path = ROOT / "notebooks" / "kaggle" / "phase2_kernel.py"
    spec = importlib.util.spec_from_file_location("phase2_kernel_validation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load Kaggle wrapper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    bundle = parse_args().bundle.resolve()
    dataset = bundle / "dataset"
    archive = dataset / "react-vietnamese-agent-phase2-dev.tar.gz"
    manifest_path = dataset / "frozen_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    kernel = load_kernel()
    if kernel.sha256(archive) != manifest["archive_sha256"]:
        raise RuntimeError("local archive hash does not match manifest")
    with tarfile.open(archive, "r:gz") as stream:
        members = [member.name for member in stream.getmembers() if member.isfile()]
    forbidden = [
        name
        for name in members
        if "/test" in name.casefold()
        or "/private/" in name.casefold()
        or "/pool/" in name.casefold()
        or "credential" in name.casefold()
    ]
    if forbidden:
        raise RuntimeError(f"forbidden files in archive: {forbidden}")
    if "data/clean/v1/splits/dev.jsonl" not in members:
        raise RuntimeError("public Dev split missing from archive")

    with tempfile.TemporaryDirectory(prefix="phase2-kaggle-simulation-") as temporary:
        temporary_root = Path(temporary)
        input_root = temporary_root / "kaggle" / "input"
        work_root = temporary_root / "kaggle" / "working"
        mount_root = input_root / "datasets" / "owner" / "bundle"
        expanded_root = mount_root / "react-vietnamese-agent-phase2-dev"
        kernel.safe_extract(archive, expanded_root)
        mount_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_path, mount_root / "frozen_manifest.json")
        project_root = work_root / "react-vietnamese-agent"
        loaded = kernel.prepare_project(input_root, project_root)
        if loaded != manifest:
            raise RuntimeError("loaded manifest differs from source manifest")
        kernel.run(
            project_root, str(manifest["git_commit"]), "scripts/validate_clean_environment.py"
        )

    print(
        "PASS: Phase 2 Kaggle mount, file hashes, public Dev presence, and Test/private "
        "ground-truth exclusion are valid"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
