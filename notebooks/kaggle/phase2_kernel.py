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
            if not member.isfile() and not member.isdir():
                raise RuntimeError(f"unsafe archive member type: {member.name}")
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
        if project_root.resolve() not in path.resolve().parents or path.is_symlink():
            raise RuntimeError(f"unsafe manifest file: {relative}")
        if not path.is_file():
            failures.append(f"missing:{relative}")
        elif sha256(path) != expected_hash:
            failures.append(f"hash:{relative}")
    if failures:
        raise RuntimeError(f"frozen source verification failed: {failures[:10]}")


def prepare_project(input_root: Path, project_root: Path) -> dict[str, Any]:
    manifest_path = find_unique(input_root, "frozen_manifest.json")
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    permitted_sources = {
        MODEL_SOURCE,
        "google/gemma-2/transformers/gemma-2-2b-it/2",
        "metaresearch/llama-3.2/transformers/3b-instruct/1",
        "qwen-lm/qwen2.5/transformers/7b-instruct/1",
        "google/gemma-4/transformers/gemma-4-e4b-it/1",
    }
    if manifest.get("model_source") not in permitted_sources:
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
    forbidden = [
        path
        for path in (project_root / "data").rglob("*")
        if path.name in {"private", "pool", "reviews", "test.jsonl"}
    ]
    if forbidden:
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
    if os.environ.get("PILOT_DEPENDENCY_DIR"):
        environment["PYTHONPATH"] += os.pathsep + os.environ["PILOT_DEPENDENCY_DIR"]
    environment["FROZEN_GIT_COMMIT"] = frozen_commit
    subprocess.run(  # noqa: S603 - fixed interpreter and repository scripts
        [sys.executable, *arguments], cwd=project_root, env=environment, check=True
    )


def bootstrap_dependencies(input_root: Path, work_root: Path, manifest: dict[str, Any]) -> None:
    hashes = manifest.get("wheel_sha256", {})
    if not hashes:
        return
    bundle = find_unique(input_root, "frozen_manifest.json").parent
    for name, digest in hashes.items():
        if Path(name).name != name or not name.endswith(".whl"):
            raise RuntimeError("invalid dependency filename")
        if sha256(bundle / name) != digest:
            raise RuntimeError("dependency wheel hash mismatch")
    target = work_root / "pilot_dependencies"
    if target.exists():
        raise RuntimeError("dependency target must be fresh")
    subprocess.run(  # noqa: S603 - offline pinned dependencies, no shell
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--find-links",
            str(bundle),
            "--target",
            str(target),
            *manifest["dependency_versions"],
        ],
        check=True,
    )
    os.environ["PILOT_DEPENDENCY_DIR"] = str(target)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    sys.path.insert(0, str(target))


def main(
    input_root: Path = DEFAULT_INPUT_ROOT,
    work_root: Path = DEFAULT_WORK_ROOT,
) -> None:
    project_root = work_root / "react-vietnamese-agent"
    manifest = prepare_project(input_root, project_root)
    bootstrap_dependencies(input_root, work_root, manifest)
    profile_key = manifest.get("model_profile", "qwen")
    sys.path.insert(0, str(project_root / "src"))
    from react_agent.llm.pilot_profiles import PROFILES, find_pilot_model

    profile = PROFILES[profile_key]
    if profile.source != manifest["model_source"]:
        raise RuntimeError("profile and frozen model source differ")
    model_path = find_pilot_model(input_root, profile)
    frozen_commit = str(manifest["git_commit"])
    if manifest.get("cpu_model_preflight"):
        run(project_root, frozen_commit, "scripts/preflight_clean_worker.py")
        run(
            project_root,
            frozen_commit,
            "scripts/preflight_pilot_models.py",
            "--input-root",
            str(input_root),
            "--output",
            str(work_root / "model_preflight.json"),
        )
        print("MODEL_CPU_PREFLIGHT_COMPLETE")
        return
    (work_root / "kaggle_bundle_info.json").write_text(
        json.dumps(
            {
                "git_commit": frozen_commit,
                "archive_sha256": manifest["archive_sha256"],
                "dataset": manifest["dataset"],
                "dataset_version": manifest["dataset_version"],
                "model_source": profile.source,
                "model_profile": profile_key,
                "chat_adapter": profile.chat_adapter,
                "measurement_protocol": manifest.get("measurement_protocol"),
                "wheel_sha256": manifest.get("wheel_sha256", {}),
                "model_path": str(model_path),
                "test_in_bundle": False,
                "private_ground_truth_in_bundle": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    replacement = manifest.get("benchmark") == "clean_v1.1"
    if replacement:
        run(project_root, frozen_commit, "scripts/preflight_clean_worker.py")
        run(
            project_root,
            frozen_commit,
            "scripts/run_clean_v11_dev.py",
            "--backend",
            "dummy",
            "--output",
            str(work_root / "phase2_v11_dummy_preflight"),
        )
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError("GPU unavailable for the frozen real-model condition")
        if (torch.ones(2, device="cuda") + 1).sum().item() != 4:
            raise RuntimeError("actual CUDA operation failed")
    else:
        run(project_root, frozen_commit, "scripts/validate_clean_environment.py")
    run(
        project_root,
        frozen_commit,
        "scripts/run_clean_v11_dev.py" if replacement else "scripts/run_hf_clean_dev.py",
        *(["--backend", "hf"] if replacement else []),
        *(["--model-profile", profile_key] if replacement else []),
        *(["--measure-performance"] if manifest.get("measurement_protocol") else []),
        "--model-path",
        str(model_path),
        "--output",
        str(work_root / "phase2_clean_dev_pilot"),
    )
    print("PHASE2_CLEAN_DEV_PILOT_COMPLETE")


if __name__ == "__main__":
    main()
