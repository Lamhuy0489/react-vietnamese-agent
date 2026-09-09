#!/usr/bin/env python3
"""Exact pair wrapper rehearsal against frozen private Dataset archive/PAX layouts."""

from __future__ import annotations

import argparse
import base64
import functools
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType

from react_agent.foundation.dev_validation import prerequisites

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("pair_wrapper", path)
    if spec is None or spec.loader is None:
        raise ValueError("wrapper import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT):  # noqa: S603,S607
        raise ValueError("commit source before exact preflight")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603,S607
    before = prerequisites(ROOT)
    if args.output.exists() or not args.output.resolve().is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle output required")
    template = ROOT / "notebooks/kaggle/model_pair_kernel_v1.py"
    wrapper = load(template)
    base_path = ROOT / "notebooks/kaggle/guard_cancellation_kernel_v1.py"
    base = load(base_path)
    prior = json.loads(
        (ROOT / "experiments/manifests/phase5_guard_cancellation_v1_preflight01.json").read_text()
    )
    if base.digest(base_path) != prior["bootstrap_template_sha256"]:
        raise ValueError("frozen base bootstrap changed")
    dataset = args.bundle / "dataset"
    manifest_path = dataset / "guard_bundle.json"
    manifest_sha = base.digest(manifest_path)
    if manifest_sha != prior["bundle_manifest_sha256"]:
        raise ValueError("frozen Dataset identity mismatch")
    value = json.loads(manifest_path.read_text())
    for name, key in (
        ("source.tar.gz", "source_archive_sha256"),
        ("guard-model.tar", "model_archive_sha256"),
    ):
        if base.digest(dataset / name) != value[key]:
            raise ValueError("frozen archive changed")
    overlay = {
        name: {
            "base64": base64.b64encode((ROOT / name).read_bytes()).decode(),
            "sha256": base.digest(ROOT / name),
        }
        for name in sorted(wrapper.OVERLAY_PATHS)
    }
    code = template.read_text().replace(
        "__BASE64_SOURCE__", base64.b64encode(base_path.read_bytes()).decode()
    )
    code = code.replace("__BASE_SHA256__", base.digest(base_path)).replace(
        "__SOURCE_COMMIT__", commit
    )
    code = code.replace("__EXPECTED_MANIFEST__", manifest_sha).replace(
        "{}  # __PAIR_OVERLAY__", repr(overlay)
    )
    kernel = args.output / "kernel"
    kernel.mkdir(parents=True)
    path = kernel / "model_pair_kernel_v1.py"
    path.write_text(code)
    metadata = json.loads((args.bundle / "kernel/kernel-metadata.json").read_text())
    metadata.update(
        id="huylmhuhu/react-vn-pair-gpu-v1",
        title="ReAct VN Pair GPU v1",
        code_file=path.name,
        model_sources=["qwen-lm/qwen2.5/transformers/7b-instruct/1"],
        docker_image_pinning_type="original",
    )
    (kernel / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    wrapper = load(path)
    os.environ["PAIR_SOURCE_COMMIT"] = commit
    checks = []
    for layout in ("archive", "expanded"):
        with tempfile.TemporaryDirectory(prefix="pair-preflight-") as temporary:
            scratch = Path(temporary)
            base = wrapper.load_base(scratch)
            mount = scratch / "input/dataset"
            mount.mkdir(parents=True)
            shutil.copy2(manifest_path, mount / manifest_path.name)
            model_hashes = {f["name"]: f["sha256"] for f in value["snapshot"]["files"]}
            if layout == "archive":
                for name in ("source.tar.gz", "guard-model.tar"):
                    shutil.copy2(dataset / name, mount / name)
            else:
                base.extract(
                    dataset / "source.tar.gz", mount / "nested-source", value["source_sha256"]
                )
                base.extract(dataset / "guard-model.tar", mount / "nested-model", model_hashes)
                (mount / "nested-source/pax_global_header").write_text(
                    "52 comment=" + value["source_commit"] + "\n"
                )
            mounted, remote_value = base.manifest(scratch / "input", manifest_sha)
            if remote_value != value:
                raise ValueError("simulated metadata changed")
            project, model = scratch / "project", scratch / "guard"
            base.materialize(
                mounted,
                "source.tar.gz",
                value["source_archive_sha256"],
                "pyproject.toml",
                project,
                value["source_sha256"],
                source_commit=value["source_commit"],
            )
            base.materialize(
                mounted,
                "guard-model.tar",
                value["model_archive_sha256"],
                "model.safetensors",
                model,
                model_hashes,
            )
            expanded = wrapper.install_overlay(base, project, value["source_sha256"])
            isolated = scratch / "venv"
            subprocess.run(  # noqa: S603 - fixed local interpreter and generated venv
                [str(Path(sys.base_prefix) / "bin/python3"), "-I", "-m", "venv", str(isolated)],
                check=True,
            )  # noqa: S603
            python = isolated / "bin/python"
            base.install(python, dataset, value, None)

            run = functools.partial(base.run, python, project, None, value["source_commit"])

            run(
                "-c",
                "import react_agent,pathlib,sys; "
                "from react_agent.llm.model_pair_hf_v1 import hf_pair; "
                "module=pathlib.Path(react_agent.__file__).resolve(); "
                "assert module.is_relative_to(pathlib.Path('src').resolve()); "
                "assert sys.prefix != sys.base_prefix; assert 'torch' not in sys.modules; "
                "print('PAIR_ISOLATED_IMPORT_OK')",
            )
            run("scripts/preflight_clean_worker.py")
            dummy = scratch / "dummy"
            run("scripts/run_clean_v11_dev.py", "--output", str(dummy))
            run("scripts/run_clean_v11_dev.py", "--output", str(dummy), "--resume")
            partial = scratch / "partial"
            partial.mkdir()
            shutil.copy2(dummy / "identity.json", partial / "identity.json")
            tasks = sorted((dummy / "tasks").iterdir())
            if len(tasks) != 21:
                raise ValueError("21 Dummy tasks required")
            for task in tasks[:-1]:
                shutil.copytree(task, partial / "tasks" / task.name)
            retained = {
                p.relative_to(partial).as_posix(): base.digest(p)
                for p in partial.rglob("*")
                if p.is_file()
            }
            run("scripts/run_clean_v11_dev.py", "--output", str(partial), "--resume")
            if len(list((partial / "tasks").iterdir())) != 21 or any(
                base.digest(partial / n) != h for n, h in retained.items()
            ):
                raise ValueError("missing-only resume changed checkpoints")
            probe = scratch / "pair"
            run("scripts/run_phase5_pair_worker.py", "--backend", "stub", "--output", str(probe))
            summary = json.loads((probe / "summary.json").read_text())
            if summary["valid"] is not True:
                raise ValueError("exact worker rehearsal failed")
            base.verify_tree(project, expanded)
            checks.append(
                {
                    "layout": layout,
                    "isolated_python": True,
                    "tools": 8,
                    "dummy_tasks": 21,
                    "retained_checkpoints": 20,
                    "missing_only_resume": True,
                    "probe": summary,
                }
            )
    if prerequisites(ROOT) != before or subprocess.check_output(
        ["git", "status", "--porcelain"],  # noqa: S607
        cwd=ROOT,
    ):  # noqa: S603,S607
        raise ValueError("source or seals changed during preflight")
    receipt = {
        "protocol": "pair_gpu_exact_preflight_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_commit": commit,
        "runtime_commit": value["source_commit"],
        "wrapper_sha256": base.digest(path),
        "metadata_sha256": base.digest(kernel / "kernel-metadata.json"),
        "base_source_sha256": base.digest(base_path),
        "bundle_manifest_sha256": manifest_sha,
        "overlay_sha256": {n: v["sha256"] for n, v in overlay.items()},
        "checks": checks,
        "prerequisites": before,
        "actual_model_loads": 0,
        "gpu_runs": 0,
    }
    (args.output / "preflight_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("PASS: exact pair wrapper/archive/expanded/PAX/eight tools/21Dummy/resume; no GPU")


if __name__ == "__main__":
    main()
