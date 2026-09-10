#!/usr/bin/env python3
"""Exact context/policy GPU package rehearsal, with no local model materialization."""

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
    parser.add_argument("--tqdm-wheel", type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):  # noqa: S603,S607
        raise ValueError("commit source before exact preflight")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603,S607
    before = prerequisites(ROOT)
    native_evidence = ROOT / "experiments/manifests/phase5_policy_native_cpu_v1_audit01.json"
    import hashlib

    if hashlib.sha256(native_evidence.read_bytes()).hexdigest() != (
        "b68645e8fbeacc03c3e1e686e8f4f8ad0e9149923ceb245f8e18bb58653304cf"
    ):
        raise ValueError("accepted native-library rehearsal evidence required")
    if args.output.exists() or not args.output.resolve().is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle output required")
    template = ROOT / "notebooks/kaggle/context_policy_kernel_v1.py"
    wrapper = load(template)
    # Untracked reports may coexist, but every packaged byte must be committed.
    required = sorted(
        wrapper.OVERLAY_PATHS
        | {
            "notebooks/kaggle/context_policy_kernel_v1.py",
            "scripts/prepare_phase5_context_policy.py",
        }
    )
    subprocess.run(  # noqa: S603 - fixed read-only Git query
        ["git", "ls-files", "--error-unmatch", *required],  # noqa: S607
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    wheel_sha = "ee1e4c0e59148062281c49d80b25b67771a127c85fc9676d3be5f243206826bf"
    import zipfile

    if args.tqdm_wheel.name != "tqdm-4.67.3-py3-none-any.whl" or (
        hashlib.sha256(args.tqdm_wheel.read_bytes()).hexdigest() != wheel_sha
    ):
        raise ValueError("exact native preflight wheel required")
    with zipfile.ZipFile(args.tqdm_wheel) as archive:
        if hashlib.sha256(archive.read("tqdm/std.py")).hexdigest() != (
            "4a4db84b039de7d86935b6f450bf18dfff2e79198bdffe4eef6572d9729ab231"
        ):
            raise ValueError("native preflight implementation differs from GPU pin")
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
    pair_pin = json.loads(
        (ROOT / "experiments/manifests/phase5_pair_gpu_v1_preflight02.json").read_text()
    )
    cpu_pin = json.loads(
        (ROOT / "experiments/manifests/phase5_pair_cancellation_v1_validation01.json").read_text()
    )
    pinned = pair_pin["overlay_sha256"] | {
        "src/react_agent/llm/pair_cancellation_v1.py": cpu_pin["source_sha256"][
            "src/react_agent/llm/pair_cancellation_v1.py"
        ]
    }
    if any(base.digest(ROOT / name) != expected for name, expected in pinned.items()):
        raise ValueError("frozen pair/cancellation source changed")
    ipc_parent = json.loads(
        (ROOT / "experiments/manifests/phase5_pair_cancel_gpu_v1_preflight01.json").read_text()
    )
    if any(base.digest(ROOT / n) != h for n, h in ipc_parent["overlay_sha256"].items()):
        raise ValueError("frozen cancellation overlay changed")
    ipc_pin = json.loads(
        (ROOT / "experiments/manifests/phase5_pair_ipc_gpu_v1_preflight01.json").read_text()
    )
    if any(base.digest(ROOT / n) != h for n, h in ipc_pin["overlay_sha256"].items()):
        raise ValueError("frozen IPC overlay changed")
    progress_pin = json.loads(
        (ROOT / "experiments/manifests/phase5_worker_progress_v1_validation01.json").read_text()
    )
    if any(base.digest(ROOT / n) != h for n, h in progress_pin["source_sha256"].items()):
        raise ValueError("frozen progress source changed")
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
    path = kernel / "context_policy_kernel_v1.py"
    path.write_text(code)
    metadata = json.loads((args.bundle / "kernel/kernel-metadata.json").read_text())
    metadata.update(
        id="huylmhuhu/react-vn-context-policy-v1",
        title="ReAct VN Context Policy v1",
        code_file=path.name,
        model_sources=["qwen-lm/qwen2.5/transformers/7b-instruct/1"],
        enable_gpu=True,
        enable_tpu=False,
        enable_internet=False,
        is_private=True,
        machine_shape="NvidiaTeslaT4",
        docker_image_pinning_type="original",
        docker_image="gcr.io/kaggle-private-byod/python@sha256:"
        "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
    )
    (kernel / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    sys.dont_write_bytecode = True
    wrapper = load(path)
    os.environ["PAIR_SOURCE_COMMIT"] = commit
    checks = []
    for layout in ("archive", "expanded"):
        with tempfile.TemporaryDirectory(prefix="pair-preflight-") as temporary:
            # macOS tempfile may spell /private/var as the /var symlink. Resolve
            # our own new scratch root; never relax link checks on model inputs.
            scratch = Path(temporary).resolve()
            base = wrapper.load_base(scratch)
            mount = scratch / "input/dataset"
            mount.mkdir(parents=True)
            shutil.copy2(manifest_path, mount / manifest_path.name)
            if layout == "archive":
                for name in ("source.tar.gz",):
                    shutil.copy2(dataset / name, mount / name)
            else:
                base.extract(
                    dataset / "source.tar.gz", mount / "nested-source", value["source_sha256"]
                )
                (mount / "nested-source/pax_global_header").write_text(
                    "52 comment=" + value["source_commit"] + "\n"
                )
            mounted, remote_value = base.manifest(scratch / "input", manifest_sha)
            if remote_value != value:
                raise ValueError("simulated metadata changed")
            project = scratch / "project"
            base.materialize(
                mounted,
                "source.tar.gz",
                value["source_archive_sha256"],
                "pyproject.toml",
                project,
                value["source_sha256"],
                source_commit=value["source_commit"],
            )
            expanded = wrapper.install_overlay(base, project, value["source_sha256"])
            isolated = scratch / "venv"
            subprocess.run(  # noqa: S603 - fixed local interpreter and generated venv
                [str(Path(sys.base_prefix) / "bin/python3"), "-I", "-m", "venv", str(isolated)],
                check=True,
            )  # noqa: S603
            python = isolated / "bin/python"
            base.install(python, dataset, value, None)
            subprocess.run(  # noqa: S603 - verified local wheel and isolated interpreter
                [
                    str(python),
                    "-I",
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--no-deps",
                    str(args.tqdm_wheel.resolve()),
                ],
                check=True,
            )  # noqa: S603 - exact hash-verified local pure-Python wheel; CPU preflight only

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
            run(
                "scripts/run_phase5_pair_progress_worker.py",
                "--backend",
                "stub",
                "--output",
                str(probe),
            )
            summary = json.loads((probe / "pair_cancellation/summary.json").read_text())
            if summary["valid"] is not True:
                raise ValueError("exact worker rehearsal failed")
            run(
                "-c",
                "from pathlib import Path; "
                "from react_agent.llm.ipc_trace_v1 import read_trace; "
                f"r=read_trace(Path({str(probe / 'tracker/owner.jsonl')!r})); "
                "assert r['register_calls']==r['unregister_calls']==90; "
                "assert not r['unmatched_registrations']; "
                "print('IPC_PARENT_LEDGER_BALANCED_90')",
            )
            run(
                "-c",
                "import json; from pathlib import Path; "
                "from react_agent.llm.ipc_trace_v1 import read_trace; "
                f"root=Path({str(probe)!r}); "
                "policies=list((root/'progress_policy').glob('*.json')); "
                "assert len(policies)==6; "
                "assert all(json.loads(p.read_text())['policy']['protocol']=="
                "'worker_thread_progress_v1' for p in policies); "
                "assert all(read_trace(root/'tracker'/(p.stem+'.jsonl'))['register_calls']==0 "
                "for p in policies); print('NATIVE_PROGRESS_SIX_WORKERS_ZERO_REGISTRATIONS')",
            )
            run(
                "scripts/run_phase5_policy_stress_v2.py",
                "--backend",
                "stub",
                "--output",
                str(scratch / "context_stub"),
                "--policy-output",
                str(scratch / "policy_stub"),
            )
            compatibility = json.loads((scratch / "policy_stub/summary.json").read_text())
            if not compatibility["valid"] or compatibility["native_library_verified"]:
                raise ValueError("CPU stub compatibility rehearsal failed")
            context = json.loads((scratch / "context_stub/summary.json").read_text())
            if not context["valid"] or context["actual_model_generation_calls"] != 0:
                raise ValueError("synthetic context transport failed")
            run(
                "-c",
                "from pathlib import Path; "
                "from react_agent.validation.context_policy_audit_v1 import publisher_policy; "
                "root=Path('docs/evaluation/publisher_policy_v1'); "
                "assert publisher_policy(root/'agent_generation_config.json','agent')"
                "['observed_publisher_expected']['repetition_penalty']==1.05; "
                "assert publisher_policy(root/'guard_generation_config.json','guard')"
                "['observed_publisher_expected']['repetition_penalty']==1.1; "
                "print('PINNED_PUBLISHER_METADATA_OK')",
            )
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
                    "policy_stub": compatibility,
                    "context_stub": context,
                    "publisher_metadata_authenticated": True,
                }
            )
    if prerequisites(ROOT) != before or subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],  # noqa: S607
        cwd=ROOT,
    ):  # noqa: S603,S607
        raise ValueError("source or seals changed during preflight")
    receipt = {
        "protocol": "context_policy_gpu_exact_preflight_v1",
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
        "native_preflight_tqdm_wheel_sha256": wheel_sha,
        "native_preflight_tqdm_version": "4.67.3",
        "native_progress_workers_each_layout": 6,
        "actual_model_loads": 0,
        "gpu_runs": 0,
        "native_library_verified_locally": False,
        "expected_native_generations": 2,
        "expected_separate_final_forwards": 2,
        "kernel_timeout_seconds": 3600,
        "guard_weights_materialized": False,
        "native_library_evidence_sha256": base.digest(native_evidence),
    }
    (args.output / "preflight_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        "PASS: exact context/policy package/archive/expanded/PAX/tools/Dummy/resume; "
        "GPU stress still pending"
    )


if __name__ == "__main__":
    main()
