"""Freeze observer source and rehearse archive/expanded mounts in offline fresh venvs."""

from __future__ import annotations

import argparse
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
from react_agent.llm.document_runtime_probe_v1 import inventory

ROOT = Path(__file__).resolve().parents[1]
BUILDER = "scripts/prepare_phase5_observer_package_v2.py"
CONTRACT = "docs/architecture/phase5_observer_native_v2_contract.md"
ENTRYPOINTS = {
    "scripts/check_phase5_observer_package_v2.py",
    "scripts/run_phase5_guard_observer_v2.py",
    "scripts/audit_phase5_guard_observer_probe_v2.py",
    "scripts/preflight_clean_worker.py",
    "scripts/run_clean_v11_dev.py",
}
PUBLIC = {
    "configs/agent/A0.yaml",
    "configs/runtime/default.yaml",
    "docs/evaluation/qwen7b_upstream_inventory_v1.json",
    "docs/evaluation/publisher_policy_v1/agent_generation_config.json",
    "docs/evaluation/publisher_policy_v1/guard_generation_config.json",
}


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
    base = load(ROOT / BASE)
    archive = output / "source.tar.gz"
    with tempfile.TemporaryDirectory(prefix="observer-v2-exact-") as temporary:
        scratch = Path(temporary).resolve()
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
            "from react_agent.llm.native_guard_diagnostics_v2 import native_pair; "
            "assert sys.prefix!=sys.base_prefix; "
            "assert pathlib.Path(react_agent.__file__).resolve().is_relative_to"
            "(pathlib.Path('src').resolve()); "
            "assert not {'torch','transformers','tokenizers'} & sys.modules.keys(); "
            "print('OBSERVER_ISOLATED_IMPORT_OK')",
        )
        run("scripts/preflight_clean_worker.py")
        dummy, partial = evidence / "dummy", evidence / "dummy_partial"
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy))
        before = inventory(dummy)
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy), "--resume")
        if inventory(dummy) != before or len(list((dummy / "tasks").iterdir())) != 21:
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
        probe = evidence / "observer"
        run(
            "scripts/check_phase5_observer_package_v2.py",
            "--source-commit",
            commit,
            "--output",
            str(probe),
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
            observer=json.loads((probe / "check.json").read_text()),
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
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True  # noqa: S607
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
    write_receipt(
        output / "source_manifest.json",
        dict(
            source_commit=commit,
            source_sha256=files,
            archive_sha256=digest(output / "source.tar.gz"),
        ),
    )
    os.environ["PAIR_SOURCE_COMMIT"] = commit
    checks = [
        rehearse(output, layout, files, commit, dataset, value, wheel)
        for layout in ("archive", "expanded")
    ]
    if committed_sources(set(source), commit) != source:
        raise ValueError("source changed during package check")
    write_receipt(
        output / "preflight_receipt.json",
        dict(
            protocol="guard_observer_package_v2_cpu",
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
            native_submission_ready=False,
            phase5_accepted=False,
            remaining=[
                "notebook launcher",
                "native metrics/source audit",
                "remote admission and inference",
            ],
        ),
    )
    print("OBSERVER_PACKAGE_CPU_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
