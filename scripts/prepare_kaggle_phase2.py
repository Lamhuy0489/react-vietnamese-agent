#!/usr/bin/env python3
"""Package a Git-frozen Kaggle bundle containing public Dev but no Test/GT."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from react_agent.validation.clean_split import validate_clean_split

ROOT = Path(__file__).resolve().parents[1]
MODEL_SOURCE = "qwen-lm/qwen2.5/transformers/3b-instruct/1"
GIT = shutil.which("git")
ARCHIVE_PATHS = (
    "src",
    "configs",
    "pyproject.toml",
    "data/clean/v1/environment",
    "data/clean/v1/manifests/environment_manifest.json",
    "data/clean/v1/manifests/source_catalog.json",
    "data/clean/v1/splits/dev.jsonl",
    "data/clean/v1/dev_pilot",
    "scripts/run_hf_clean_dev.py",
    "scripts/run_hf_smoke.py",
    "scripts/run_smoke.py",
    "scripts/validate_clean_environment.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--dataset-version", required=True, type=int)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "kaggle" / "phase2")
    return parser.parse_args()


def git_output(*arguments: str) -> str:
    if GIT is None:
        raise RuntimeError("git executable not found")
    result = subprocess.run(  # noqa: S603 - fixed executable and controlled arguments
        [GIT, *arguments], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def included_files() -> list[str]:
    files = git_output("ls-tree", "-r", "--name-only", "HEAD", "--", *ARCHIVE_PATHS)
    return [line for line in files.splitlines() if line]


def main() -> int:
    args = parse_args()
    acceptance = validate_clean_split()
    if not acceptance["valid"]:
        raise SystemExit(
            f"Refusing to package an invalid clean benchmark: {acceptance['failures']}"
        )
    if GIT is None:
        raise SystemExit("git executable not found")
    if git_output("status", "--porcelain"):
        raise SystemExit("Refusing to package a dirty worktree; commit frozen inputs first.")
    commit = git_output("rev-parse", "HEAD")
    files = included_files()
    forbidden = [
        path
        for path in files
        if "/test" in path.casefold()
        or "/private/" in path.casefold()
        or "/pool/" in path.casefold()
        or "credential" in path.casefold()
    ]
    if forbidden:
        raise RuntimeError(f"forbidden Test/private paths selected: {forbidden}")
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(
            "Output already exists; choose a fresh --output to preserve prior bundles."
        )
    dataset_dir = output / "dataset"
    kernel_dir = output / "kernel"
    dataset_dir.mkdir(parents=True)
    kernel_dir.mkdir(parents=True)
    archive = dataset_dir / "react-vietnamese-agent-phase2-dev.tar.gz"
    subprocess.run(  # noqa: S603 - fixed git archive command
        [GIT, "archive", "--format=tar.gz", f"--output={archive}", "HEAD", *ARCHIVE_PATHS],
        cwd=ROOT,
        check=True,
    )
    dataset_slug = "react-vietnamese-agent-phase2-dev-bundle"
    kernel_slug = "react-vietnamese-agent-phase-2-clean-dev-pilot"
    (dataset_dir / "dataset-metadata.json").write_text(
        json.dumps(
            {
                "title": "ReAct Vietnamese Agent Phase 2 Public Dev Bundle",
                "id": f"{args.owner}/{dataset_slug}",
                "licenses": [{"name": "other"}],
                "isPrivate": True,
                "description": f"Public-Dev-only inference bundle from Git commit {commit}.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = {
        "git_commit": commit,
        "archive_sha256": sha256(archive),
        "model_source": MODEL_SOURCE,
        "dataset": f"{args.owner}/{dataset_slug}",
        "dataset_version": args.dataset_version,
        "kernel": f"{args.owner}/{kernel_slug}",
        "scope": "clean_v1.0_public_dev_pilot_only",
        "test_in_bundle": False,
        "private_ground_truth_in_bundle": False,
        "file_sha256": {relative: sha256(ROOT / relative) for relative in files},
    }
    (dataset_dir / "frozen_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    kernel_source = (ROOT / "notebooks" / "kaggle" / "phase2_kernel.py").read_text(encoding="utf-8")
    (kernel_dir / "phase2_kernel.py").write_text(kernel_source, encoding="utf-8")
    (kernel_dir / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "id": manifest["kernel"],
                "title": "ReAct Vietnamese Agent - Phase 2 Clean Dev Pilot",
                "code_file": "phase2_kernel.py",
                "language": "python",
                "kernel_type": "script",
                "is_private": True,
                "enable_gpu": True,
                "enable_tpu": False,
                "enable_internet": False,
                "dataset_sources": [manifest["dataset"]],
                "competition_sources": [],
                "kernel_sources": [],
                "model_sources": [MODEL_SOURCE],
                "machine_shape": "NvidiaTeslaT4",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "bundle_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
