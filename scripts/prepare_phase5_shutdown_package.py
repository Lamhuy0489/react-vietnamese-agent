"""Build and exercise the exact ordinary package offline; no local model loading."""

from __future__ import annotations

import argparse
import base64
import functools
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import no_links

ROOT = Path(__file__).resolve().parents[1]
PRIOR = "experiments/manifests/phase5_efficient_stress_gpu_v1_preflight01.json"
PRIOR_SHA = "33cf51c67de3ff4d8bca8ce2f7fcc7030034da10fae25997708e43eb0ddba793"
TOKENIZER_QA = "experiments/manifests/phase5_tokenizer_metadata_cpu_v1_release_qa01.json"
TOKENIZER_QA_SHA = "d805580f2ca594ba83336b594ffa06435e6f8b735f0de976748e2dad8c69d948"
TEMPLATE = "notebooks/kaggle/security_runtime_kernel_v2.py"
BASE = "notebooks/kaggle/guard_cancellation_kernel_v1.py"
WIRING_QA = "experiments/manifests/phase5_native_shutdown_wiring_v2_cpu01.json"
WIRING_SHA = "fd4c7a3fcc773811545a286d5b23e3b1bfa214526ba115bd54eb3052c1a8e911"
WHEEL_SHA = "ee1e4c0e59148062281c49d80b25b67771a127c85fc9676d3be5f243206826bf"


def digest(path: Path) -> str:
    no_links(path)
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("ordinary_wrapper", path)
    if spec is None or spec.loader is None:
        raise ValueError("wrapper import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def committed_sources(names: set[str], commit: str) -> dict[str, str]:
    """Permit unrelated dirty work, but every selected byte must match this Git tree."""
    result = {}
    for name in sorted(names):
        path = ROOT / name
        observed = digest(path)
        raw = subprocess.check_output(  # noqa: S603 - fixed read-only Git object query
            ["git", "show", f"{commit}:{name}"],  # noqa: S607
            cwd=ROOT,
        )
        if hashlib.sha256(raw).hexdigest() != observed:
            raise ValueError("uncommitted selected source: " + name)
        result[name] = observed
    return result


def check_pins() -> dict[str, Any]:
    for name, expected in ((PRIOR, PRIOR_SHA), (TOKENIZER_QA, TOKENIZER_QA_SHA)):
        if digest(ROOT / name) != expected:
            raise ValueError("accepted evidence pin changed")
    if digest(ROOT / WIRING_QA) != WIRING_SHA:
        raise ValueError("native wiring evidence pin changed")
    wiring = json.loads((ROOT / WIRING_QA).read_text())
    if wiring["valid"] is not True:
        raise ValueError("native wiring QA not accepted")
    for name, expected in wiring["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("native wiring source changed: " + name)
    prior = json.loads((ROOT / PRIOR).read_text())
    qa = json.loads((ROOT / TOKENIZER_QA).read_text())
    for name, expected in (prior["overlay_sha256"] | qa["source_sha256"]).items():
        if digest(ROOT / name) != expected:
            raise ValueError("frozen implementation changed: " + name)
    if digest(ROOT / BASE) != prior["base_source_sha256"]:
        raise ValueError("frozen bootstrap changed")
    return dict(prior)


def synthetic_fixture() -> tuple[Path, str]:
    """Authenticate old CPU-only fixtures; these are never included in the worker payload."""
    qa = json.loads((ROOT / TOKENIZER_QA).read_text())
    prior_path = ROOT / qa["prior_release_path"]
    if digest(prior_path) != qa["prior_release_sha256"]:
        raise ValueError("saved synthetic fixture authority changed")
    prior = json.loads(prior_path.read_text())
    fixture = ROOT / prior["synthetic_join"]["path"]
    for name, expected in prior["synthetic_join"]["raw_sha256"].items():
        if digest(fixture / name) != expected:
            raise ValueError("saved synthetic fixture changed")
    return fixture / "synthetic", prior["supervisor_reaudits"][0]["source_commit"]


def rehearse(
    wrapper: ModuleType,
    dataset: Path,
    value: dict[str, Any],
    wheel: Path,
    layout: str,
    evidence: Path,
) -> dict[str, Any]:
    """Use a fresh offline venv and actual packaged scripts, retaining CPU raw evidence."""
    with tempfile.TemporaryDirectory(prefix="ordinary-exact-") as temporary:
        scratch = Path(temporary).resolve()
        base = wrapper.load_base(scratch)
        mount = scratch / "input/dataset"
        mount.mkdir(parents=True)
        shutil.copy2(dataset / "guard_bundle.json", mount / "guard_bundle.json")
        if layout == "archive":
            shutil.copy2(dataset / "source.tar.gz", mount / "source.tar.gz")
        elif layout == "expanded":
            base.extract(
                dataset / "source.tar.gz", mount / "generated/source", value["source_sha256"]
            )
            (mount / "generated/source/pax_global_header").write_text(
                "52 comment=" + value["source_commit"] + "\n"
            )
        else:
            raise ValueError("known layout required")
        mounted, observed = base.manifest(scratch / "input", wrapper.EXPECTED_MANIFEST)
        if observed != value:
            raise ValueError("mounted manifest mismatch")
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
        subprocess.run(  # noqa: S603 - local interpreter and self-created venv
            [str(Path(sys.base_prefix) / "bin/python3"), "-I", "-m", "venv", str(isolated)],
            check=True,
        )
        python = isolated / "bin/python"
        base.install(python, dataset, value, None)
        subprocess.run(  # noqa: S603 - exact hash-verified local wheel, offline
            [str(python), "-I", "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)],
            check=True,
        )
        run = functools.partial(base.run, python, project, None, value["source_commit"])
        run(
            "-c",
            "import sys,pathlib,react_agent; "
            "from react_agent.llm.native_shutdown_v2 import native_pair; "
            "from react_agent.validation.security_runtime_probe_audit_v2 import audit; "
            "assert pathlib.Path(react_agent.__file__).resolve().is_relative_to"
            "(pathlib.Path('src').resolve()); assert sys.prefix!=sys.base_prefix; "
            "assert not {'torch','transformers','tokenizers'} & sys.modules.keys(); "
            "print('ORDINARY_ISOLATED_IMPORT_OK')",
        )
        run("scripts/preflight_clean_worker.py")
        dummy, partial = evidence / "dummy", evidence / "partial"
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy))
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy), "--resume")
        partial.mkdir()
        shutil.copy2(dummy / "identity.json", partial / "identity.json")
        tasks = sorted((dummy / "tasks").iterdir())
        if len(tasks) != 21:
            raise ValueError("exact selected public Dev count required")
        for task in tasks[:-1]:
            shutil.copytree(task, partial / "tasks" / task.name)
        retained = {
            p.relative_to(partial).as_posix(): digest(p) for p in partial.rglob("*") if p.is_file()
        }
        run("scripts/run_clean_v11_dev.py", "--output", str(partial), "--resume")
        if len(list((partial / "tasks").iterdir())) != 21 or any(
            digest(partial / n) != h for n, h in retained.items()
        ):
            raise ValueError("missing-only resume changed retained work")
        probe = evidence / "probe"
        run("scripts/run_phase5_ordinary_pair.py", "--output", str(probe))
        for index in (1, 2):
            run(
                "scripts/audit_phase5_ordinary_pair.py",
                "--probe",
                str(probe),
                "--source-commit",
                wrapper.SOURCE_COMMIT,
                "--backend",
                "stub",
                "--output",
                str(evidence / f"audit{index}.json"),
            )
        if (evidence / "audit1.json").read_bytes() != (evidence / "audit2.json").read_bytes():
            raise ValueError("independent audit not byte-identical")
        audit = json.loads((evidence / "audit1.json").read_text())
        # Public metadata fixture is kept OUTSIDE the worker payload; never materialize weights.
        metadata = json.loads(
            (ROOT / "docs/evaluation/tokenizer_config_v1_source.json").read_text()
        )
        fake_mount = scratch / "metadata_only"
        fake_mount.mkdir()
        (fake_mount / "tokenizer_config.json").write_bytes(metadata["source_utf8"].encode())
        run(
            "scripts/collect_phase5_tokenizer_metadata.py",
            "--agent-path",
            str(fake_mount),
            "--guard-path",
            str(fake_mount),
            "--output",
            str(evidence / "tokenizers"),
        )
        fixture, fixture_commit = synthetic_fixture()
        # Exercise the entire joined CLI from the isolated package, using separately
        # authenticated fake records. This never promotes a synthetic run to native.
        pin = scratch / "snapshot.json"
        pin.write_text(json.dumps(value["snapshot"]))
        arguments = ["scripts/audit_phase5_ordinary_tokenizer.py"]
        for name in ("probe", "policy", "attention", "publishers"):
            arguments.extend(["--" + name, str(fixture / name)])
        arguments.extend(
            [
                "--tokenizers",
                str(evidence / "tokenizers"),
                "--snapshot",
                str(pin),
                "--source-commit",
                fixture_commit,
            ]
        )
        for index in (1, 2):
            run(*arguments, "--output", str(evidence / f"synthetic_join{index}.json"))
        if (evidence / "synthetic_join1.json").read_bytes() != (
            evidence / "synthetic_join2.json"
        ).read_bytes():
            raise ValueError("synthetic joined audit not byte-identical")
        synthetic_fixture()
        security = evidence / "security_runtime"
        run("scripts/run_phase5_shutdown_runtime_probe.py", "--output", str(security))
        retained_security = {
            p.relative_to(security).as_posix(): digest(p)
            for p in security.rglob("*")
            if p.is_file()
        }
        run("scripts/run_phase5_shutdown_runtime_probe.py", "--output", str(security), "--resume")
        if any(digest(security / n) != h for n, h in retained_security.items()):
            raise ValueError("security resume changed retained evidence")
        run("scripts/audit_phase5_shutdown_runtime_probe.py", "--help")
        for index in (1, 2):
            run(
                "scripts/check_phase5_shutdown_package.py",
                "--probe",
                str(security),
                "--output",
                str(evidence / f"shutdown_audit{index}.json"),
            )
        if (evidence / "shutdown_audit1.json").read_bytes() != (
            evidence / "shutdown_audit2.json"
        ).read_bytes():
            raise ValueError("shutdown package audit not repeatable")
        base.verify_tree(project, expanded)
        return dict(
            shutdown_checkpoint_audit=True,
            new_native_audit_cli_imported=True,
            security_runtime_levels=7,
            security_runtime_resume_immutable=True,
            layout=layout,
            isolated_python=True,
            tools=8,
            dummy_tasks=21,
            retained_checkpoints=20,
            missing_only_resume=True,
            ordinary_supervisor_audit=audit,
            metadata_only_collector=True,
            synthetic_joined_cli=True,
            native_tokenizer_executed=False,
            raw_sha256={
                p.relative_to(evidence).as_posix(): digest(p)
                for p in sorted(evidence.rglob("*"))
                if p.is_file()
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "output", "tqdm-wheel"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    for path in (args.bundle, args.output, args.tqdm_wheel):
        no_links(path)
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle output required")
    prior = check_pins()
    before = prerequisites(ROOT)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603,S607
    sys.dont_write_bytecode = True
    wrapper = load(ROOT / TEMPLATE)
    names = wrapper.OVERLAY_PATHS | {
        TEMPLATE,
        BASE,
        WIRING_QA,
        "scripts/prepare_phase5_shutdown_package.py",
        PRIOR,
        TOKENIZER_QA,
        "docs/evaluation/tokenizer_config_v1_source.json",
    }
    source = committed_sources(names, commit)
    dataset = args.bundle.resolve() / "dataset"
    manifest = dataset / "guard_bundle.json"
    if digest(manifest) != prior["bundle_manifest_sha256"]:
        raise ValueError("fixed private Dataset manifest required")
    value = json.loads(manifest.read_text())
    for name, expected in {
        "source.tar.gz": value["source_archive_sha256"],
        "guard-model.tar": value["model_archive_sha256"],
        **value["wheel_sha256"],
    }.items():
        if digest(dataset / name) != expected:
            raise ValueError("frozen archive/wheel mismatch")
    if (
        args.tqdm_wheel.name != "tqdm-4.67.3-py3-none-any.whl"
        or digest(args.tqdm_wheel) != WHEEL_SHA
    ):
        raise ValueError("exact offline tqdm wheel required")
    with zipfile.ZipFile(args.tqdm_wheel) as archive:
        if hashlib.sha256(archive.read("tqdm/std.py")).hexdigest() != (
            "4a4db84b039de7d86935b6f450bf18dfff2e79198bdffe4eef6572d9729ab231"
        ):
            raise ValueError("native progress implementation changed")
    overlay = {
        n: dict(base64=base64.b64encode((ROOT / n).read_bytes()).decode(), sha256=source[n])
        for n in sorted(wrapper.OVERLAY_PATHS)
    }
    code = (ROOT / TEMPLATE).read_text()
    for key, replacement in {
        "__BASE64_SOURCE__": base64.b64encode((ROOT / BASE).read_bytes()).decode(),
        "__BASE_SHA256__": source[BASE],
        "__SOURCE_COMMIT__": commit,
        "__EXPECTED_MANIFEST__": digest(manifest),
        "{}  # __PAIR_OVERLAY__": repr(overlay),
    }.items():
        if code.count(key) != 1:
            raise ValueError("unique template placeholder required")
        code = code.replace(key, replacement)
    kernel = output / "kernel"
    kernel.mkdir(parents=True)
    worker = kernel / "security_runtime_kernel_v2.py"
    worker.write_text(code)
    metadata = json.loads((args.bundle / "kernel/kernel-metadata.json").read_text())
    metadata.update(
        id="huylmhuhu/react-vn-security-runtime-v2",
        title="ReAct VN Security Runtime v2",
        code_file=worker.name,
        model_sources=["qwen-lm/qwen2.5/transformers/7b-instruct/1"],
        dataset_sources=[value["dataset"]],
        kernel_sources=[],
        competition_sources=[],
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
    wrapper = load(worker)
    os.environ["PAIR_SOURCE_COMMIT"] = commit
    checks = []
    for layout in ("archive", "expanded"):
        evidence = output / "cpu" / layout
        evidence.mkdir(parents=True)
        checks.append(
            rehearse(wrapper, dataset, value, args.tqdm_wheel.resolve(), layout, evidence)
        )
    if committed_sources(names, commit) != source or prerequisites(ROOT) != before:
        raise ValueError("selected source or seals changed during preflight")
    receipt = dict(
        protocol="security_runtime_gpu_exact_preflight_v2",
        valid=True,
        phase5_accepted=False,
        source_commit=commit,
        runtime_commit=value["source_commit"],
        source_sha256=source,
        wrapper_sha256=digest(worker),
        metadata_sha256=digest(kernel / "kernel-metadata.json"),
        base_source_sha256=source[BASE],
        bundle_manifest_sha256=digest(manifest),
        overlay_sha256={n: v["sha256"] for n, v in overlay.items()},
        checks=checks,
        prerequisites=before,
        native_preflight_tqdm_wheel_sha256=WHEEL_SHA,
        actual_model_loads=0,
        gpu_runs=0,
        native_submission_ready=False,
        wiring_qa_sha256=WIRING_SHA,
        expected_native_levels=7,
        native_library_verified_locally=False,
        remote_source_authenticated=False,
        scope="Exact package CPU import/tool/Dummy/resume/stub/metadata evidence only. "
        "Model tensors are never materialized locally; runtime uses a public synthetic task. "
        "Native factory execution and remote "
        "source/identity audit remain release gates. No semantic retry or quality claim.",
    )
    (output / "preflight_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("SECURITY_RUNTIME_EXACT_PREFLIGHT_COMPLETE native_validated=False gpu_runs=0")


if __name__ == "__main__":
    main()
