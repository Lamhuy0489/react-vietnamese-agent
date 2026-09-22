"""Rehearse constrained packages offline; development packages cannot run inference."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from prepare_phase5_document_probe import BASE, WHEEL_SHA, committed_sources, digest, load
from prepare_phase5_grouped_package_v3 import BUNDLE_SHA, dependency_closure, make_archive

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.clause_dev_identity_v1 import execution_sources
from react_agent.llm.document_runtime_probe_v1 import inventory

ROOT = Path(__file__).resolve().parents[1]
BUILDER = "scripts/prepare_phase5_clause_dev_package_v1.py"
CONTRACT = "docs/architecture/phase5_clause_dev_package_v1_contract.md"
TEMPLATE = "notebooks/kaggle/clause_dev32_kernel_v1.py"
ENTRYPOINTS = {
    "scripts/check_phase5_clause_dev_package_v1.py",
    "scripts/run_phase5_clause_dev_native_v1.py",
    "scripts/audit_phase5_clause_dev_native_v1.py",
    "scripts/preflight_clean_worker.py",
    "scripts/run_clean_v11_dev.py",
    "scripts/collect_phase5_tokenizer_metadata.py",
}
PUBLIC = {
    "configs/agent/A0.yaml",
    "configs/runtime/default.yaml",
    "data/adversarial/release_v2/dev_attack.jsonl",
    "data/adversarial/release_v2/dev_benign.jsonl",
    "data/adversarial/release_v2/seal.json",
    "docs/evaluation/qwen7b_upstream_inventory_v1.json",
    "docs/evaluation/publisher_policy_v1/agent_generation_config.json",
    "docs/evaluation/publisher_policy_v1/guard_generation_config.json",
}


def selected_sources(names: set[str], commit: str, *, development: bool) -> dict[str, str]:
    """Bind working bytes explicitly during QA; releases must match committed bytes."""
    if development:
        return {name: digest(ROOT / name) for name in sorted(names)}
    return committed_sources(names, commit)


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
    archive = output / "source.tar.gz"
    with tempfile.TemporaryDirectory(prefix="exit-pair-v1-exact-") as temporary:
        scratch = Path(temporary).resolve()
        wrapper = load(output / "kernel/clause_dev32_kernel_v1.py")
        wrapper.write_source_manifest(scratch / "source_manifest.json")
        if digest(scratch / "source_manifest.json") != digest(output / "source_manifest.json"):
            raise ValueError("launcher source admission differs from builder")
        base = wrapper.bootstrap(scratch)
        embedded = scratch / "embedded.tar.gz"
        wrapper.source_archive(embedded)
        if digest(embedded) != digest(archive) or wrapper.SOURCE_FILES != files:
            raise ValueError("launcher archive differs from preflight source")
        mount = scratch / "input/dataset"
        mount.mkdir(parents=True)
        if layout == "archive":
            shutil.copy2(archive, mount / "source.tar.gz")
        else:
            base.extract(archive, mount / "generated/source", files)
        project = scratch / "project"
        base.materialize(
            mount,
            "source.tar.gz",
            digest(archive),
            "pyproject.toml",
            project,
            files,
            source_commit=commit,
        )
        venv = scratch / "venv"
        subprocess.run(  # noqa: S603 - known interpreter and fresh local venv
            [str(Path(sys.base_prefix) / "bin/python3"), "-I", "-m", "venv", str(venv)], check=True
        )
        python = venv / "bin/python"
        base.install(python, dataset, value, None)
        subprocess.run(  # noqa: S603 - offline hash-verified wheel
            [str(python), "-I", "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)],
            check=True,
        )

        def run(*arguments: str) -> None:
            base.run(python, project, None, commit, *arguments)

        run(
            "-c",
            "import sys,pathlib,react_agent; "
            "from react_agent.llm.clause_dev_dispatch_v1 import run; "
            "assert sys.prefix!=sys.base_prefix; "
            "assert pathlib.Path(react_agent.__file__).resolve().is_relative_to"
            "(pathlib.Path('src').resolve()); "
            "assert not {'torch','transformers','tokenizers'} & sys.modules.keys(); "
            "print('EXIT_PAIR_ISOLATED_IMPORT_OK')",
        )
        run("scripts/audit_phase5_clause_dev_native_v1.py", "--help")
        run("scripts/preflight_clean_worker.py")
        dummy, partial = evidence / "dummy", evidence / "dummy_partial"
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy))
        before = inventory(dummy / "tasks")
        dummy_identity = digest(dummy / "identity.json")
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy), "--resume")
        if (
            inventory(dummy / "tasks") != before
            or digest(dummy / "identity.json") != dummy_identity
            or len(list((dummy / "tasks").iterdir())) != 21
        ):
            raise ValueError("clean completed resume mismatch")
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
            raise ValueError("clean missing-only resume mismatch")
        probe = evidence / "dev32"
        run(
            "scripts/check_phase5_clause_dev_package_v1.py",
            "--source-commit",
            commit,
            "--source-manifest",
            str(output / "source_manifest.json"),
            "--source-sha256",
            digest(output / "source_manifest.json"),
            "--output",
            str(probe),
        )
        for shard in range(8):
            run(
                "scripts/audit_phase5_clause_dev_native_v1.py",
                "--probe",
                str(probe / f"shard{shard}"),
                "--output",
                str(evidence / "audits" / f"shard{shard}.json"),
                "--source-commit",
                commit,
                "--shard",
                str(shard),
                "--source-manifest",
                str(output / "source_manifest.json"),
                "--source-sha256",
                digest(output / "source_manifest.json"),
            )
        base.verify_tree(project, files)
        return dict(
            layout=layout,
            valid=True,
            isolated_python=True,
            offline_wheels=True,
            tools=8,
            clean_dummy_tasks=21,
            clean_missing_only_resume=True,
            dev32=json.loads((probe / "check.json").read_text()),
            raw_sha256=inventory(evidence),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--development", action="store_true", help="CPU-only working-tree QA; no native submission"
    )
    args = parser.parse_args()
    development = args.development
    source_mode = "working_tree" if development else "committed"
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
    # Frozen identities also pin explicit filenames outside the static import graph.
    identity_sources = {"src/react_agent/" + name for name in execution_sources()}
    names = (
        dependency_closure(ROOT, set(value["source_sha256"]) | ENTRYPOINTS | identity_sources)
        | PUBLIC
    )
    allowed_data = {n for n in value["source_sha256"] if n.startswith("data/")} | PUBLIC
    base = load(ROOT / BASE)
    for name in names:
        base.relative_name(name)
        if name.startswith("tests/") or (name.startswith("data/") and name not in allowed_data):
            raise ValueError("unapproved worker data or test file")
    files = selected_sources(names, commit, development=development)
    source = selected_sources(
        names
        | {
            BUILDER,
            CONTRACT,
            BASE,
            TEMPLATE,
            "scripts/prepare_phase5_document_probe.py",
            "scripts/prepare_phase5_grouped_package_v3.py",
            "scripts/audit_phase5_clause_dev_gpu_v1.py",
        },
        commit,
        development=development,
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
        "__SOURCE_MODE__": source_mode,
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
    (kernel / "clause_dev32_kernel_v1.py").write_text(code)
    metadata = dict(
        id="huylmhuhu/react-vn-clause-dev32-v1",
        title="ReAct VN Clause Dev32 v1",
        code_file="clause_dev32_kernel_v1.py",
        language="python",
        kernel_type="script",
        is_private=True,
        enable_gpu=not development,
        enable_tpu=False,
        enable_internet=False,
        dataset_sources=[value["dataset"]],
        model_sources=["qwen-lm/qwen2.5/transformers/7b-instruct/1"],
        kernel_sources=[],
        competition_sources=[],
        machine_shape="NvidiaTeslaT4",
        docker_image_pinning_type="original",
        docker_image="gcr.io/kaggle-private-byod/python@sha256:"
        "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
    )
    write_receipt(kernel / "kernel-metadata.json", metadata)
    write_receipt(
        output / "source_manifest.json",
        dict(
            protocol="clause_dev32_source_v1",
            source_commit=None if development else commit,
            git_base_commit=commit,
            source_mode=source_mode,
            source_sha256=files,
            archive_sha256=digest(output / "source.tar.gz"),
        ),
    )
    os.environ["PAIR_SOURCE_COMMIT"] = commit
    checks = [
        rehearse(output, layout, files, commit, dataset, value, wheel)
        for layout in ("archive", "expanded")
    ]
    if selected_sources(set(source), commit, development=development) != source:
        raise ValueError("source changed during package check")
    write_receipt(
        output / "preflight_receipt.json",
        dict(
            protocol="clause_dev32_package_v1_cpu",
            valid=True,
            source_commit=None if development else commit,
            git_base_commit=commit,
            source_mode=source_mode,
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
            native_submission_ready=not development,
            kernel_sha256=inventory(kernel),
            requested_notebook=metadata["id"],
            phase5_accepted=False,
            remaining=(["committed source freeze and release preflight"] if development else [])
            + [
                "remote admission and inference",
                "download/version/source authentication",
            ],
        ),
    )
    print("CLAUSE_DEV32_PACKAGE_CPU_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
