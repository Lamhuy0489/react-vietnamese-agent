"""Thin Kaggle entrypoint for the frozen Phase 2 public-Dev pilot bundle."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

DEFAULT_INPUT_ROOT = Path("/kaggle/input")
DEFAULT_WORK_ROOT = Path("/kaggle/working")
MODEL_SOURCE = "qwen-lm/qwen2.5/transformers/3b-instruct/1"
EXPECTED_MODEL_SUFFIX = Path("qwen2.5/transformers/3b-instruct/1")


def find_unique(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {name!r} under {root}, found {matches}")
    return matches[0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    resolved_destination = destination.resolve()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            target = (destination / member.name).resolve()
            if resolved_destination not in target.parents and target != resolved_destination:
                raise RuntimeError(f"unsafe archive member: {member.name}")
        tar.extractall(destination)  # noqa: S202 - every target path validated above


def verify_frozen_files(project_root: Path, manifest: dict[str, Any]) -> None:
    expected = manifest.get("file_sha256")
    if not isinstance(expected, dict) or not expected:
        raise RuntimeError("frozen manifest is missing file_sha256 entries")
    failures = []
    for relative, expected_hash in expected.items():
        path = project_root / relative
        if not path.is_file():
            failures.append(f"missing:{relative}")
        elif sha256(path) != expected_hash:
            failures.append(f"hash:{relative}")
    if failures:
        raise RuntimeError(f"frozen source verification failed: {failures[:10]}")


def prepare_project(input_root: Path, project_root: Path) -> dict[str, Any]:
    manifest_path = find_unique(input_root, "frozen_manifest.json")
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("model_source") != MODEL_SOURCE:
        raise RuntimeError("manifest model source does not match the frozen condition")
    bundle_root = manifest_path.parent
    archives = list(bundle_root.glob("react-vietnamese-agent-phase2-dev.tar.gz"))
    if archives:
        archive = archives[0]
        if sha256(archive) != manifest["archive_sha256"]:
            raise RuntimeError("source archive hash does not match frozen manifest")
        safe_extract(archive, project_root)
    else:
        candidates = [
            path
            for path in bundle_root.rglob("react_agent")
            if path.is_dir() and path.parent.name == "src"
        ]
        if len(candidates) != 1:
            raise RuntimeError(f"expected one expanded source bundle, found {candidates}")
        shutil.copytree(candidates[0].parent.parent, project_root, dirs_exist_ok=True)
    verify_frozen_files(project_root, manifest)
    forbidden = (
        project_root / "data" / "clean" / "v1" / "splits" / "test.jsonl",
        project_root / "data" / "clean" / "v1" / "private",
        project_root / "data" / "clean" / "v1" / "pool",
    )
    if any(path.exists() for path in forbidden):
        raise RuntimeError("Kaggle worker bundle contains Test or private ground truth")
    return manifest


def find_model_path(input_root: Path) -> Path:
    candidates = [path for path in input_root.rglob("1") if path.is_dir()]
    candidates = [
        path
        for path in candidates
        if str(path).casefold().endswith(str(EXPECTED_MODEL_SUFFIX).casefold())
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"expected one frozen model path, found {candidates}")
    required = ("config.json", "tokenizer.json", "model.safetensors.index.json")
    missing = [name for name in required if not (candidates[0] / name).is_file()]
    if missing:
        raise RuntimeError(f"frozen model is missing required files: {missing}")
    return candidates[0]


def run(project_root: Path, frozen_commit: str, *arguments: str) -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root / "src")
    environment["FROZEN_GIT_COMMIT"] = frozen_commit
    subprocess.run(  # noqa: S603 - fixed interpreter and repository scripts
        [sys.executable, *arguments], cwd=project_root, env=environment, check=True
    )


def main(
    input_root: Path = DEFAULT_INPUT_ROOT,
    work_root: Path = DEFAULT_WORK_ROOT,
) -> None:
    project_root = work_root / "react-vietnamese-agent"
    manifest = prepare_project(input_root, project_root)
    model_path = find_model_path(input_root)
    frozen_commit = str(manifest["git_commit"])
    (work_root / "kaggle_bundle_info.json").write_text(
        json.dumps(
            {
                "git_commit": frozen_commit,
                "archive_sha256": manifest["archive_sha256"],
                "dataset": manifest["dataset"],
                "dataset_version": manifest["dataset_version"],
                "model_source": MODEL_SOURCE,
                "model_path": str(model_path),
                "test_in_bundle": False,
                "private_ground_truth_in_bundle": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    run(project_root, frozen_commit, "scripts/validate_clean_environment.py")
    run(
        project_root,
        frozen_commit,
        "scripts/run_hf_clean_dev.py",
        "--model-path",
        str(model_path),
        "--output",
        str(work_root / "phase2_clean_dev_pilot"),
    )
    print("PHASE2_CLEAN_DEV_PILOT_COMPLETE")


if __name__ == "__main__":
    main()
