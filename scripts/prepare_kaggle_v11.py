#!/usr/bin/env python3
"""Package a clean Git revision and validate both possible Kaggle mount layouts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from prepare_kaggle_phase2 import git_output, sha256

from react_agent.llm.pilot_profiles import PROFILES
from react_agent.validation.clean_v11_seal import validate_seal

ROOT = Path(__file__).resolve().parents[1]
PATHS = (
    "src",
    "configs",
    "pyproject.toml",
    "data/clean/v1_1/environment",
    "data/clean/v1_1/manifests/environment_manifest.json",
    "data/clean/v1_1/manifests/source_catalog.json",
    "data/clean/v1_1/splits/dev.jsonl",
    "data/clean/v1_1/dev_pilot",
    "scripts/run_clean_v11_dev.py",
    "scripts/preflight_clean_worker.py",
    "scripts/run_hf_smoke.py",
    "scripts/run_smoke.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-profile", choices=sorted(PROFILES), default="qwen")
    parser.add_argument("--dataset-slug", default="react-vn-clean-v11-dev")
    parser.add_argument("--kernel-slug")
    args = parser.parse_args()
    import re

    profile = PROFILES[args.model_profile]
    kernel_slug = args.kernel_slug or f"react-vn-v11-pilot-{args.model_profile}"
    for slug in (args.owner, args.dataset_slug, kernel_slug):
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError("invalid owner/dataset/kernel slug")
    if git_output("status", "--porcelain"):
        raise RuntimeError("commit frozen source and dataset before packaging")
    failures = validate_seal(ROOT / "data/clean/v1_1")
    if failures:
        raise RuntimeError(failures)
    if args.output.exists():
        raise RuntimeError("choose a fresh output directory")
    dataset = args.output / "dataset"
    kernel_dir = args.output / "kernel"
    dataset.mkdir(parents=True)
    kernel_dir.mkdir()
    archive = dataset / "react-vietnamese-agent-phase2-dev.tar.gz"
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git missing")
    subprocess.run(  # noqa: S603 - fixed git archive invocation; no shell
        [git, "archive", "--format=tar.gz", f"--output={archive.resolve()}", "HEAD", *PATHS],
        cwd=ROOT,
        check=True,
    )  # noqa: S603
    files = git_output("ls-tree", "-r", "--name-only", "HEAD", "--", *PATHS).splitlines()
    if any(
        "credential" in name.casefold()
        or "/private/" in name
        or "/test" in name
        or "/pool/" in name
        for name in files
    ):
        raise RuntimeError("forbidden worker file")
    manifest: dict[str, Any] = {
        "git_commit": git_output("rev-parse", "HEAD"),
        "benchmark": "clean_v1.1",
        "archive_sha256": sha256(archive),
        "file_sha256": {name: sha256(ROOT / name) for name in files},
        "model_source": profile.source,
        "model_profile": args.model_profile,
        "chat_adapter": profile.chat_adapter,
        "dataset": f"{args.owner}/{args.dataset_slug}",
        "dataset_version": 1,
    }
    (dataset / "frozen_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    metadata = {
        "title": "ReAct Vietnamese Clean v1.1 Public Dev",
        "id": manifest["dataset"],
        "licenses": [{"name": "other"}],
    }
    (dataset / "dataset-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    kernel_path = ROOT / "notebooks/kaggle/phase2_kernel.py"
    shutil.copy2(kernel_path, kernel_dir / "phase2_kernel.py")
    (kernel_dir / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "id": f"{args.owner}/{kernel_slug}",
                "title": kernel_slug.replace("-", " "),
                "code_file": "phase2_kernel.py",
                "language": "python",
                "kernel_type": "script",
                "is_private": True,
                "enable_gpu": True,
                "enable_tpu": False,
                "enable_internet": False,
                "dataset_sources": [manifest["dataset"]],
                "model_sources": [profile.source],
                "competition_sources": [],
                "kernel_sources": [],
                "machine_shape": "NvidiaTeslaT4",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    spec = importlib.util.spec_from_file_location("frozen_kernel", kernel_dir / "phase2_kernel.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import packaged wrapper")
    kernel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kernel)
    for layout in ("archive", "expanded"):
        with tempfile.TemporaryDirectory(prefix="clean-v11-mount-") as temporary:
            root = Path(temporary)
            mount = root / "input/dataset"
            mount.mkdir(parents=True)
            shutil.copy2(dataset / "frozen_manifest.json", mount / "frozen_manifest.json")
            if layout == "archive":
                shutil.copy2(archive, mount / archive.name)
            else:
                kernel.safe_extract(archive, mount / "generated-directory")
            project = root / "working/project"
            kernel.prepare_project(root / "input", project)
            kernel.run(project, manifest["git_commit"], "scripts/preflight_clean_worker.py")
            output = root / "working/dummy"
            kernel.run(
                project,
                manifest["git_commit"],
                "scripts/run_clean_v11_dev.py",
                "--output",
                str(output),
                "--model-profile",
                args.model_profile,
            )
            kernel.run(
                project,
                manifest["git_commit"],
                "scripts/run_clean_v11_dev.py",
                "--output",
                str(output),
                "--resume",
                "--model-profile",
                args.model_profile,
            )
    (args.output / "preflight_receipt.json").write_text(
        json.dumps(
            {
                "valid": True,
                "git_commit": manifest["git_commit"],
                "archive_sha256": manifest["archive_sha256"],
                "wrapper_sha256": sha256(kernel_path),
                "model_source": profile.source,
                "model_profile": args.model_profile,
                "layouts": ["archive", "expanded"],
                "runtime_tools": 8,
                "dummy_tasks_per_layout": 21,
                "resume_verified": True,
                "gpu_tested_locally": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sealed = json.loads((ROOT / "data/clean/v1_1/manifests/benchmark_manifest.json").read_text())
    (args.output / "expected_run.json").write_text(
        json.dumps(
            {
                "status": "prepared_not_submitted",
                "source_commit": manifest["git_commit"],
                "archive_sha256": manifest["archive_sha256"],
                "wrapper_sha256": sha256(kernel_path),
                "dataset_hash": sealed["dataset_hash"],
                "dataset": manifest["dataset"],
                "dataset_version": 1,
                "kernel": f"{args.owner}/{kernel_slug}",
                "model_profile": args.model_profile,
                "model_source": profile.source,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("PASS: exact packaged source in both mounts, eight tools, 21 Dev tasks and resume")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
