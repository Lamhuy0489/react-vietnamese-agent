"""Freeze observer source and rehearse archive/expanded mounts in offline fresh venvs."""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from prepare_phase5_document_probe import BASE, WHEEL_SHA, committed_sources, digest, load
from prepare_phase5_grouped_package_v3 import BUNDLE_SHA, dependency_closure, make_archive

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory

ROOT = Path(__file__).resolve().parents[1]
BUILDER = "scripts/prepare_phase5_guard_language_cpu_v1.py"
CONTRACT = "docs/architecture/phase5_guard_language_native_v1_contract.md"
TEMPLATE = "notebooks/kaggle/guard_language_cpu_kernel_v1.py"
ENTRYPOINTS = {
    "scripts/run_phase5_guard_language_native_v1.py",
    "scripts/probe_phase5_guard_language_v1.py",
    "scripts/preflight_clean_worker.py",
    "scripts/run_clean_v11_dev.py",
}
PUBLIC: set[str] = set()


def rehearse(
    output: Path,
    layout: str,
    files: dict[str, str],
    commit: str,
    dataset: Path,
    value: dict[str, Any],
    wheel: Path,
) -> dict[str, Any]:
    evidence = output / "cpu" / layout
    evidence.mkdir(parents=True)
    wrapper = load(output / "kernel/guard_language_cpu_kernel_v1.py")
    with tempfile.TemporaryDirectory(prefix="guard-language-exact-") as temporary:
        scratch = Path(temporary).resolve()
        base = wrapper.bootstrap(scratch)
        wrapper.source_archive(scratch / "source.tar.gz")
        if digest(scratch / "source.tar.gz") != digest(output / "source.tar.gz"):
            raise ValueError("embedded archive mismatch")
        mount = scratch / "mount"
        mount.mkdir()
        if layout == "archive":
            shutil.copy2(scratch / "source.tar.gz", mount / "source.tar.gz")
        else:
            base.extract(scratch / "source.tar.gz", mount / "generated/source", files)
        project = scratch / "project"
        base.materialize(
            mount,
            "source.tar.gz",
            wrapper.ARCHIVE_SHA,
            "pyproject.toml",
            project,
            files,
            source_commit=commit,
        )
        venv = scratch / "venv"
        subprocess.run(  # noqa: S603 - fresh isolated interpreter
            [str(Path(sys.base_prefix) / "bin/python3"), "-I", "-m", "venv", str(venv)], check=True
        )
        python = venv / "bin/python"
        base.install(python, dataset, value, None)

        def run(*arguments: str) -> None:
            base.run(python, project, None, commit, *arguments)

        run(
            "-c",
            "import pathlib,sys,react_agent; "
            "assert pathlib.Path(react_agent.__file__).resolve().is_relative_to"
            "(pathlib.Path('src').resolve()); "
            "assert sys.prefix != sys.base_prefix; assert 'torch' not in sys.modules",
        )
        run("scripts/preflight_clean_worker.py")
        dummy = evidence / "dummy"
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy))
        before = inventory(dummy / "tasks")
        identity = digest(dummy / "identity.json")
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy), "--resume")
        if (
            inventory(dummy / "tasks") != before
            or digest(dummy / "identity.json") != identity
            or len(list((dummy / "tasks").iterdir())) != 21
        ):
            raise ValueError("Dummy completed resume mismatch")
        partial = evidence / "partial"
        partial.mkdir()
        shutil.copy2(dummy / "identity.json", partial / "identity.json")
        for task in sorted((dummy / "tasks").iterdir())[:-1]:
            shutil.copytree(task, partial / "tasks" / task.name)
        retained = inventory(partial)
        run("scripts/run_clean_v11_dev.py", "--output", str(partial), "--resume")
        after = inventory(partial)
        if len(list((partial / "tasks").iterdir())) != 21 or any(
            after.get(n) != h for n, h in retained.items()
        ):
            raise ValueError("missing-only resume mismatch")
        (project / "results").mkdir()
        run(
            "scripts/probe_phase5_guard_language_v1.py",
            "--output",
            str(project / "results/synthetic.json"),
        )
        # Actual launcher invocation, with only native imports explicitly disabled.
        wrapper.payload(base, python, project, None, dataset, evidence, metadata_only=True)
        # Check expanded tokenizer layout too; copy only authenticated small files.
        expanded = scratch / "expanded_dataset"
        expanded.mkdir()
        shutil.copy2(dataset / "guard_bundle.json", expanded / "guard_bundle.json")
        shutil.copytree(evidence / "language/tokenizer", expanded / "generated/tokenizer")
        second = evidence / "expanded_metadata"
        wrapper.payload(base, python, project, None, expanded, second, metadata_only=True)
        if inventory(evidence / "language/tokenizer") != inventory(second / "language/tokenizer"):
            raise ValueError("archive/expanded tokenizer mismatch")
        # Generated synthetic receipt is outside the frozen source inventory.
        synthetic = json.loads((project / "results/synthetic.json").read_text())
        shutil.move(str(project / "results"), str(evidence / "synthetic"))
        base.verify_tree(project, files)
        return dict(
            layout=layout,
            valid=True,
            tools=8,
            clean_dummy_tasks=21,
            missing_only_resume=True,
            native_library_executed=False,
            actual_launcher_cli_executed=True,
            synthetic=synthetic,
            raw_sha256=inventory(evidence),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    no_links(args.output)
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle output required")
    commit = subprocess.check_output(  # noqa: S603,S607 - fixed read-only git command
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=ROOT,
        text=True,
    ).strip()
    dataset = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset"
    manifest = dataset / "guard_bundle.json"
    if digest(manifest) != BUNDLE_SHA:
        raise ValueError("frozen Dataset manifest changed")
    value = json.loads(manifest.read_text())
    for name, expected in value["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("frozen base source changed")
    names = dependency_closure(ROOT, set(value["source_sha256"]) | ENTRYPOINTS) | PUBLIC
    allowed_data = {n for n in value["source_sha256"] if n.startswith("data/")}
    base = load(ROOT / BASE)
    for name in names:
        base.relative_name(name)
        if name.startswith("tests/") or (name.startswith("data/") and name not in allowed_data):
            raise ValueError("unapproved worker data or test file")
    files = committed_sources(names, commit)
    source = committed_sources(
        names
        | {
            BUILDER,
            CONTRACT,
            BASE,
            TEMPLATE,
            "scripts/prepare_phase5_document_probe.py",
            "scripts/prepare_phase5_grouped_package_v3.py",
        },
        commit,
    )
    wheel = ROOT / "build/kaggle/worker_progress_v1_wheels/tqdm-4.67.3-py3-none-any.whl"
    if digest(wheel) != WHEEL_SHA:
        raise ValueError("offline progress wheel changed")
    old = ROOT / "experiments/manifests/phase5_grouped_package_v3_preflight01.json"
    frozen = json.loads(old.read_text())["source_sha256"]
    for name, sha in frozen.items():
        if digest(ROOT / name) != sha:
            raise ValueError("baseline worker changed")
    output.mkdir(parents=True)
    make_archive(ROOT, files, output / "source.tar.gz")
    code = (ROOT / TEMPLATE).read_text()
    for key, replacement in {
        "__SOURCE_COMMIT__": commit,
        "__BASE_SOURCE__": base64.b64encode((ROOT / BASE).read_bytes()).decode(),
        "__BASE_SHA__": source[BASE],
        "__ARCHIVE__": base64.b64encode((output / "source.tar.gz").read_bytes()).decode(),
        "__ARCHIVE_SHA__": digest(output / "source.tar.gz"),
        "__BUNDLE_SHA__": BUNDLE_SHA,
        "{}  # __SOURCE_FILES__": repr(files),
    }.items():
        if code.count(key) != 1:
            raise ValueError("unique launcher placeholder required")
        code = code.replace(key, replacement)
    kernel = output / "kernel"
    kernel.mkdir()
    (kernel / "guard_language_cpu_kernel_v1.py").write_text(code)
    metadata = dict(
        id="huylmhuhu/react-vn-guard-language-cpu-v1",
        title="ReAct VN Guard Language CPU v1",
        code_file="guard_language_cpu_kernel_v1.py",
        language="python",
        kernel_type="script",
        is_private=True,
        enable_gpu=False,
        enable_tpu=False,
        enable_internet=False,
        dataset_sources=[value["dataset"]],
        model_sources=[],
        kernel_sources=[],
        competition_sources=[],
        machine_shape=None,
        docker_image_pinning_type="original",
        docker_image="gcr.io/kaggle-private-byod/python@sha256:"
        "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
    )
    write_receipt(kernel / "kernel-metadata.json", metadata)
    write_receipt(
        output / "source_manifest.json",
        dict(
            source_commit=commit,
            source_sha256=files,
            archive_sha256=digest(output / "source.tar.gz"),
        ),
    )
    checks = [
        rehearse(output, layout, files, commit, dataset, value, wheel)
        for layout in ("archive", "expanded")
    ]
    if committed_sources(set(source), commit) != source:
        raise ValueError("source changed during package check")
    write_receipt(
        output / "preflight_receipt.json",
        dict(
            protocol="guard_language_native_cpu_package_v1",
            valid=True,
            source_commit=commit,
            source_sha256=source,
            package_sha256=files,
            checks=checks,
            archive_sha256=digest(output / "source.tar.gz"),
            dataset_manifest_sha256=digest(manifest),
            offline_tqdm_sha256=WHEEL_SHA,
            frozen_worker_pins_verified=len(frozen),
            actual_model_loads=0,
            gpu_runs=0,
            test_payload_accessed=False,
            native_submission_ready=True,
            kernel_sha256=inventory(kernel),
            requested_notebook=metadata["id"],
            phase5_accepted=False,
            remaining=[
                "remote CPU tokenizer/processor compatibility",
                "download/version/source authentication",
            ],
        ),
    )
    print("LANGUAGE_CPU_PACKAGE_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
