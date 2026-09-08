#!/usr/bin/env python3
"""Build and simulate both exact Kaggle layouts in a fresh offline Python venv."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.guard_acquisition_v1 import UpstreamSnapshot, verify_acquisition

ROOT = Path(__file__).resolve().parents[1]
BASE = [
    "pydantic==2.13.5",
    "pydantic-core==2.46.5",
    "PyYAML==6.0.3",
    "typing-extensions==4.16.0",
    "annotated-types==0.8.0",
    "typing-inspection==0.4.4",
]
GPU = [
    *BASE,
    "transformers==5.5.0",
    "tokenizers==0.22.2",
    "huggingface-hub==1.7.2",
    "regex==2025.11.3",
    "safetensors==0.6.2",
    "hf-xet==1.4.2",
    "accelerate==1.10.1",
]
PATHS = (
    "src/react_agent/__init__.py",
    "src/react_agent/config.py",
    "src/react_agent/agent",
    "src/react_agent/broker",
    "src/react_agent/environment",
    "src/react_agent/logging",
    "src/react_agent/parser",
    "src/react_agent/prompts",
    "src/react_agent/tools",
    "src/react_agent/schemas/__init__.py",
    "src/react_agent/schemas/agent_output.py",
    "src/react_agent/schemas/clean_task.py",
    "src/react_agent/schemas/task.py",
    "src/react_agent/schemas/tool.py",
    "src/react_agent/schemas/trace.py",
    "src/react_agent/llm/__init__.py",
    "src/react_agent/llm/base.py",
    "src/react_agent/llm/dummy.py",
    "src/react_agent/llm/replay.py",
    "src/react_agent/llm/hf_backend.py",
    "src/react_agent/llm/pilot_profiles.py",
    "src/react_agent/llm/guard_hf_v1.py",
    "src/react_agent/llm/guard_snapshot_v1.py",
    "src/react_agent/llm/guard_probe_v1.py",
    "src/react_agent/security_v1/__init__.py",
    "src/react_agent/security_v1/contracts.py",
    "src/react_agent/security_v1/guard.py",
    "src/react_agent/security_v1/process_guard.py",
    "src/react_agent/security_v1/warm_guard.py",
    "src/react_agent/foundation/__init__.py",
    "src/react_agent/foundation/artifacts.py",
    "src/react_agent/foundation/normalization.py",
    # Namespace-only worker validation directory: the historical __init__ eagerly
    # imports pool validators. Never package it merely to import environment QA.
    "src/react_agent/validation/clean_environment.py",
    "configs/agent/A0.yaml",
    "configs/runtime/default.yaml",
    "pyproject.toml",
    "data/clean/v1_1/environment",
    "data/clean/v1_1/manifests/environment_manifest.json",
    "data/clean/v1_1/manifests/source_catalog.json",
    "data/clean/v1_1/splits/dev.jsonl",
    "data/clean/v1_1/dev_pilot",
    "scripts/run_clean_v11_dev.py",
    "scripts/preflight_clean_worker.py",
    "scripts/probe_phase5_guard.py",
)


def load_kernel(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("guard_probe_kernel", path)
    if spec is None or spec.loader is None:
        raise ValueError("kernel wrapper unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquisition", type=Path, required=True)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--owner", default="huylmhuhu")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9]+", args.owner):
        raise ValueError("invalid owner")
    git = shutil.which("git")
    if git is None:
        raise ValueError("Git required")

    def git_text(*arguments: str) -> str:
        return subprocess.check_output([git, *arguments], cwd=ROOT, text=True).strip()  # noqa: S603

    if git_text("status", "--porcelain"):
        raise ValueError("commit source before packaging")
    before = prerequisites(ROOT)
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle output required")
    upstream = UpstreamSnapshot.model_validate_json(
        (ROOT / "configs/guard_hf_v1/qwen_1_5b_upstream.json").read_text()
    )
    snapshot = verify_acquisition(args.acquisition / "snapshot", upstream)
    acquired = json.loads((args.acquisition / "acquisition.json").read_text())
    if acquired["valid"] is not True or acquired["snapshot_sha256"] != snapshot.sha256:
        raise ValueError("acquisition receipt mismatch")
    kernel = load_kernel(ROOT / "notebooks/kaggle/guard_probe_kernel.py")
    dataset, kernel_dir = output / "dataset", output / "kernel"
    dataset.mkdir(parents=True)
    kernel_dir.mkdir()
    commit = git_text("rev-parse", "HEAD")
    files = git_text("ls-tree", "-r", "--name-only", "HEAD", "--", *PATHS).splitlines()
    for name in files:
        kernel.relative_name(name)
    source = dataset / "source.tar.gz"
    subprocess.run(  # noqa: S603 - explicit committed source allowlist
        [git, "archive", "--format=tar.gz", f"--output={source}", commit, *PATHS],
        cwd=ROOT,
        check=True,
    )
    model_archive = dataset / "guard-model.tar"
    with tarfile.open(model_archive, "w") as stream:
        for entry in snapshot.files:
            stream.add(
                args.acquisition / "snapshot" / entry.name, arcname=entry.name, recursive=False
            )
    old = json.loads((ROOT / "experiments/manifests/measured_pilot_submission.json").read_text())
    gpu_hashes = old["conditions"]["qwen7b"]["expected"]["wheel_sha256"]
    old_wheels = ROOT / "build/kaggle/measured_qwen7b_v1/dataset"
    for name, sha256 in gpu_hashes.items():
        if kernel.digest(old_wheels / name) != sha256:
            raise ValueError("previously pinned inference wheel changed")
        shutil.copy2(old_wheels / name, dataset / name)
    base_wheels = sorted(args.wheelhouse.glob("*.whl"))
    if len(base_wheels) != 10:
        raise ValueError("ten base wheels required: Mac cp311 and Linux cp311/cp312")
    for wheel in base_wheels:
        if (dataset / wheel.name).exists():
            raise ValueError("duplicate wheel name")
        shutil.copy2(wheel, dataset / wheel.name)
    value: dict[str, Any] = {
        "protocol": "guard_statelessness_preflight_v1",
        "source_commit": commit,
        "source_archive_sha256": kernel.digest(source),
        "source_sha256": {name: kernel.digest(ROOT / name) for name in files},
        "model_archive_sha256": kernel.digest(model_archive),
        "snapshot": snapshot.model_dump(mode="json"),
        "acquisition_sha256": kernel.digest(args.acquisition / "acquisition.json"),
        "base_dependencies": BASE,
        "gpu_dependencies": GPU,
        "wheel_sha256": {p.name: kernel.digest(p) for p in sorted(dataset.glob("*.whl"))},
        "dataset": f"{args.owner}/react-vn-guard15-probe-data-v1",
        "dataset_version": 1,
        "kernel": f"{args.owner}/react-vn-guard15-probe-run-v1",
        "model_quality_selection": False,
        "held_out_test_in_payload": False,
    }
    manifest_path = dataset / "guard_bundle.json"
    manifest_path.write_text(json.dumps(value, indent=2) + "\n")
    manifest_hash = kernel.digest(manifest_path)
    wrapper = (
        (ROOT / "notebooks/kaggle/guard_probe_kernel.py")
        .read_text()
        .replace(
            "__BUNDLE_MANIFEST_SHA256__",
            manifest_hash,
        )
    )
    wrapper_path = kernel_dir / "guard_probe_kernel.py"
    wrapper_path.write_text(wrapper)
    (dataset / "dataset-metadata.json").write_text(
        json.dumps(
            {
                "title": "ReAct VN Guard15 Probe Data v1",
                "id": value["dataset"],
                "licenses": [{"name": "other"}],
            },
            indent=2,
        )
        + "\n"
    )
    (kernel_dir / "kernel-metadata.json").write_text(
        json.dumps(
            {
                "id": value["kernel"],
                "title": "ReAct VN Guard15 Probe Run v1",
                "code_file": "guard_probe_kernel.py",
                "language": "python",
                "kernel_type": "script",
                "is_private": True,
                "enable_gpu": True,
                "enable_tpu": False,
                "enable_internet": False,
                "dataset_sources": [value["dataset"]],
                "model_sources": [],
                "competition_sources": [],
                "kernel_sources": [],
                "machine_shape": "NvidiaTeslaT4",
            },
            indent=2,
        )
        + "\n"
    )
    kernel = load_kernel(wrapper_path)
    checks = []
    for layout in ("archive", "expanded"):
        with tempfile.TemporaryDirectory(prefix="guard-bundle-simulation-") as temporary:
            scratch = Path(temporary)
            mount = scratch / "input/dataset"
            mount.mkdir(parents=True)
            shutil.copy2(manifest_path, mount / manifest_path.name)
            if layout == "archive":
                shutil.copy2(source, mount / source.name)
                shutil.copy2(model_archive, mount / model_archive.name)
            else:
                kernel.extract(source, mount / "generated-source", value["source_sha256"])
                kernel.extract(
                    model_archive,
                    mount / "generated-model",
                    {f.name: f.sha256 for f in snapshot.files},
                )
            mounted, loaded = kernel.manifest(scratch / "input", manifest_hash)
            if loaded != value:
                raise ValueError("mounted manifest differs")
            project, model = scratch / "project", scratch / "model"
            kernel.materialize(
                mounted,
                source.name,
                value["source_archive_sha256"],
                "pyproject.toml",
                project,
                value["source_sha256"],
            )
            kernel.materialize(
                mounted,
                model_archive.name,
                value["model_archive_sha256"],
                "model.safetensors",
                model,
                {f.name: f.sha256 for f in snapshot.files},
            )
            venv_path = scratch / "isolated-venv"
            base_python = str(Path(sys.base_prefix) / "bin/python3")
            subprocess.run([base_python, "-I", "-m", "venv", str(venv_path)], check=True)  # noqa: S603
            python = venv_path / "bin/python"
            kernel.install(python, dataset, value, None)
            kernel.run(
                python,
                project,
                None,
                commit,
                "-c",
                "import react_agent,pathlib,sys; "
                "module=pathlib.Path(react_agent.__file__).resolve(); "
                "assert module.is_relative_to(pathlib.Path('src').resolve()); "
                "assert sys.prefix != sys.base_prefix; print('ISOLATED_BUNDLE_IMPORT_OK')",
            )
            kernel.run(python, project, None, commit, "scripts/preflight_clean_worker.py")
            dummy = scratch / "dummy"
            kernel.run(
                python,
                project,
                None,
                commit,
                "scripts/run_clean_v11_dev.py",
                "--output",
                str(dummy),
            )
            kernel.run(
                python,
                project,
                None,
                commit,
                "scripts/run_clean_v11_dev.py",
                "--output",
                str(dummy),
                "--resume",
            )
            # Copy a prefix of completed checkpoints into a NEW simulation.
            # Do not delete/retry any terminal task from the first run.
            partial = scratch / "partial-dummy"
            partial.mkdir()
            shutil.copy2(dummy / "identity.json", partial / "identity.json")
            task_roots = sorted((dummy / "tasks").iterdir())
            if len(task_roots) != 21:
                raise ValueError("unexpected baseline checkpoint coverage")
            for task_root in task_roots[:-1]:
                shutil.copytree(task_root, partial / "tasks" / task_root.name)
            retained = {
                p.relative_to(partial).as_posix(): kernel.digest(p)
                for p in partial.rglob("*")
                if p.is_file()
            }
            kernel.run(
                python,
                project,
                None,
                commit,
                "scripts/run_clean_v11_dev.py",
                "--output",
                str(partial),
                "--resume",
            )
            if len(list((partial / "tasks").iterdir())) != 21 or any(
                kernel.digest(partial / p) != h for p, h in retained.items()
            ):
                raise ValueError("missing-only resume changed retained checkpoints")
            probe = scratch / "probe"
            kernel.run(
                python,
                project,
                None,
                commit,
                "scripts/probe_phase5_guard.py",
                "--backend",
                "stub",
                "--output",
                str(probe),
            )
            summary = json.loads((probe / "summary.json").read_text())
            if summary["valid"] is not True or summary["structured_valid_calls"] != 4:
                raise ValueError("packaged probe failed")
            kernel.verify_tree(project, value["source_sha256"])
            checks.append(
                {
                    "layout": layout,
                    "isolated_python": True,
                    "tools": 8,
                    "dummy_tasks": 21,
                    "completed_task_resume": True,
                    "missing_only_resume": True,
                    "retained_checkpoints": 20,
                    "missing_task_runs": 1,
                    "probe": summary,
                }
            )
    if prerequisites(ROOT) != before or git_text("status", "--porcelain"):
        raise ValueError("source/seal changed during packaging")
    receipt = {
        "valid": True,
        "source_commit": commit,
        "bundle_manifest_sha256": manifest_hash,
        "wrapper_sha256": kernel.digest(wrapper_path),
        "checks": checks,
        "prerequisites": before,
        "snapshot_sha256": snapshot.sha256,
        "source_file_count": len(files),
        "real_model_runs": 0,
        "gpu_tested_locally": False,
        "phase5_accepted": False,
    }
    (output / "preflight_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("PASS: two exact mounts, isolated offline environments, tools/Dev/stub probe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
