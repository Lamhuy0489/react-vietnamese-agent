#!/usr/bin/env python3
"""Create reproducible Kaggle Dataset and kernel upload folders from Git HEAD."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_SOURCE = "qwen-lm/qwen2.5/transformers/3b-instruct/1"
GIT = shutil.which("git")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "kaggle" / "phase1")
    return parser.parse_args()


def git_output(*arguments: str) -> str:
    if GIT is None:
        raise RuntimeError("git executable not found")
    result = subprocess.run(  # noqa: S603 - fixed executable and controlled arguments
        [GIT, *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    if GIT is None:
        raise SystemExit("git executable not found")
    if git_output("status", "--porcelain"):
        raise SystemExit("Refusing to package a dirty worktree; commit the frozen inputs first.")
    commit = git_output("rev-parse", "HEAD")
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    dataset_dir = output / "dataset"
    kernel_dir = output / "kernel"
    dataset_dir.mkdir(parents=True)
    kernel_dir.mkdir(parents=True)

    archive = dataset_dir / "react-vietnamese-agent-phase1.tar.gz"
    subprocess.run(  # noqa: S603 - fixed git archive command
        [GIT, "archive", "--format=tar.gz", f"--output={archive}", "HEAD"],
        cwd=ROOT,
        check=True,
    )
    archive_hash = sha256(archive)
    dataset_slug = "react-vietnamese-agent-phase1-bundle"
    dataset_metadata = {
        "title": "ReAct Vietnamese Agent Phase 1 Bundle",
        "id": f"{args.owner}/{dataset_slug}",
        "licenses": [{"name": "other"}],
        "isPrivate": True,
        "description": f"Frozen private source bundle for Git commit {commit}.",
    }
    (dataset_dir / "dataset-metadata.json").write_text(
        json.dumps(dataset_metadata, indent=2) + "\n", encoding="utf-8"
    )

    kernel_source = (ROOT / "notebooks" / "kaggle" / "phase1_kernel.py").read_text(
        encoding="utf-8"
    )
    (kernel_dir / "phase1_kernel.py").write_text(kernel_source, encoding="utf-8")
    kernel_metadata = {
        "id": f"{args.owner}/react-vietnamese-agent-phase1-smoke",
        "title": "ReAct Vietnamese Agent - Phase 1 Real Model Smoke",
        "code_file": "phase1_kernel.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "dataset_sources": [f"{args.owner}/{dataset_slug}"],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [MODEL_SOURCE],
        "machine_shape": "NvidiaTeslaT4",
    }
    (kernel_dir / "kernel-metadata.json").write_text(
        json.dumps(kernel_metadata, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "git_commit": commit,
        "archive_sha256": archive_hash,
        "model_source": MODEL_SOURCE,
        "dataset": f"{args.owner}/{dataset_slug}",
        "kernel": kernel_metadata["id"],
    }
    (output / "bundle_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
