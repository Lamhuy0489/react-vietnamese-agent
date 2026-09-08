#!/usr/bin/env python3
"""Package and preflight a cancellation-only source overlay on the frozen Dataset."""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType

from react_agent.foundation.dev_validation import prerequisites

ROOT = Path(__file__).resolve().parents[1]


def load_kernel(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("guard_pax_kernel", path)
    if spec is None or spec.loader is None:
        raise ValueError("bootstrap unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    git = shutil.which("git")
    if git is None:
        raise ValueError("Git required")

    def git_text(*arguments: str) -> str:
        return subprocess.check_output([git, *arguments], cwd=ROOT, text=True).strip()  # noqa: S603

    if git_text("status", "--porcelain"):
        raise ValueError("commit bootstrap source before exact preflight")
    bootstrap_commit = git_text("rev-parse", "HEAD")
    before = prerequisites(ROOT)
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle output required")
    dataset = args.bundle.resolve() / "dataset"
    manifest_path = dataset / "guard_bundle.json"
    kernel = load_kernel(ROOT / "notebooks/kaggle/guard_cancellation_kernel_v1.py")
    base_receipt_path = ROOT / "experiments/manifests/phase5_guard_bundle_v1_preflight03.json"
    diagnostic_path = ROOT / "experiments/manifests/phase5_guard_remote_mount_v1_diagnostic01.json"
    base_receipt = json.loads(base_receipt_path.read_text())
    diagnostic = json.loads(diagnostic_path.read_text())
    manifest_hash = kernel.digest(manifest_path)
    if not base_receipt["valid"] or manifest_hash != base_receipt["bundle_manifest_sha256"]:
        raise ValueError("base bundle receipt mismatch")
    value = json.loads(manifest_path.read_text())
    commit = value["source_commit"]
    if commit != base_receipt["source_commit"] or before != base_receipt["prerequisites"]:
        raise ValueError("source or sealed prerequisites changed")
    source = dataset / "source.tar.gz"
    model_archive = dataset / "guard-model.tar"
    if (
        kernel.digest(source) != value["source_archive_sha256"]
        or kernel.digest(model_archive) != value["model_archive_sha256"]
    ):
        raise ValueError("base archive changed")
    header = ROOT / "build/kaggle/guard_pax_diagnostic01/pax_global_header"
    if kernel.digest(header) != diagnostic["remote_header_sha256"] or header.read_bytes() != (
        "52 comment=" + commit + "\n"
    ).encode("ascii"):
        raise ValueError("remote PAX evidence mismatch")
    kernel_dir = output / "kernel"
    kernel_dir.mkdir(parents=True)
    template = ROOT / "notebooks/kaggle/guard_cancellation_kernel_v1.py"
    wrapper = template.read_text().replace("__BUNDLE_MANIFEST_SHA256__", manifest_hash)
    wrapper = wrapper.replace("__BOOTSTRAP_COMMIT__", bootstrap_commit)
    overlay = {
        name: {
            "base64": base64.b64encode((ROOT / name).read_bytes()).decode("ascii"),
            "sha256": kernel.digest(ROOT / name),
        }
        for name in sorted(kernel.OVERLAY_PATHS)
    }
    wrapper = wrapper.replace("{}  # __CANCELLATION_OVERLAY__", repr(overlay))
    wrapper_path = kernel_dir / "guard_cancellation_kernel_v1.py"
    wrapper_path.write_text(wrapper)
    metadata = json.loads((args.bundle / "kernel/kernel-metadata.json").read_text())
    metadata["code_file"] = wrapper_path.name
    metadata["id"] = "huylmhuhu/react-vn-guard-cancel-run-v1"
    metadata["title"] = "ReAct VN Guard Cancel Run v1"
    if (
        metadata["is_private"] is not True
        or metadata["enable_internet"] is not False
        or metadata["dataset_sources"] != [value["dataset"]]
    ):
        raise ValueError("unexpected kernel metadata")
    (kernel_dir / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
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
                    {f["name"]: f["sha256"] for f in value["snapshot"]["files"]},
                )
                shutil.copy2(header, mount / "generated-source/pax_global_header")
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
                source_commit=commit,
            )
            kernel.materialize(
                mounted,
                model_archive.name,
                value["model_archive_sha256"],
                "model.safetensors",
                model,
                {f["name"]: f["sha256"] for f in value["snapshot"]["files"]},
            )
            expanded = kernel.install_overlay(project, value["source_sha256"])
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
                "scripts/probe_phase5_guard_cancellation.py",
                "--backend",
                "stub",
                "--output",
                str(probe),
            )
            summary = json.loads((probe / "summary.json").read_text())
            if summary["valid"] is not True or len(summary["rows"]) != 3:
                raise ValueError("packaged probe failed")
            kernel.verify_tree(project, expanded)
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
        raise ValueError("source/seal changed during preflight")
    receipt = {
        "protocol": "guard_cancellation_overlay_v1_preflight",
        "valid": True,
        "phase5_accepted": False,
        "source_commit": commit,
        "bootstrap_commit": bootstrap_commit,
        "bundle_manifest_sha256": manifest_hash,
        "base_preflight_sha256": kernel.digest(base_receipt_path),
        "remote_diagnostic_sha256": kernel.digest(diagnostic_path),
        "remote_pax_sha256": kernel.digest(header),
        "wrapper_sha256": kernel.digest(wrapper_path),
        "bootstrap_template_sha256": kernel.digest(template),
        "kernel_metadata_sha256": kernel.digest(kernel_dir / "kernel-metadata.json"),
        "checks": checks,
        "overlay_sha256": {name: item["sha256"] for name, item in overlay.items()},
        "prerequisites": before,
        "dataset": value["dataset"],
        "dataset_version": 1,
        "real_model_runs": 0,
        "scope": "Technical cancellation overlay; Dataset/runtime/model unchanged; "
        "no LLM text generation.",
    }
    (output / "preflight_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("PASS: cancellation overlay; isolated archive/expanded mounts; no GPU")


if __name__ == "__main__":
    main()
