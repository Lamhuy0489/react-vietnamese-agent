"""Exact offline two-layout worker rehearsal for the doc_read final-proof candidate.

Development mode never authenticates committed source or enables native inference.
"""

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

from prepare_phase5_document_probe import BASE, WHEEL_SHA, digest, load
from prepare_phase5_grouped_package_v3 import BUNDLE_SHA, dependency_closure, make_archive
from prepare_phase5_room_ticket_package_v1 import DATASET, PUBLIC, ROOT, WHEEL, committed_sources

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.validation.clause_dev_release_v1 import safe_name
from react_agent.validation.context_stress_audit_v1 import inventory
from react_agent.validation.doc_read_native_admission_v1 import REQUIRED, SOURCE_PROTOCOL

SEEDS = REQUIRED | {
    "pyproject.toml", "scripts/preflight_clean_worker.py", "scripts/run_clean_v11_dev.py",
}


def worker_files(base_sources: dict[str, str]) -> dict[str, str]:
    names = dependency_closure(ROOT, set(base_sources) | SEEDS) | PUBLIC
    allowed_data = {name for name in base_sources if name.startswith("data/")}
    files = {}
    for name in sorted(names):
        safe_name(name)
        if name.startswith("src/react_agent/authoring/") or "doc_read_final_controls" in name or (
            name.startswith("data/") and name not in allowed_data
        ):
            raise ValueError("host QA or non-public data in doc_read worker")
        files[name] = digest(ROOT / name)
    if not SEEDS <= files.keys():
        raise ValueError("doc_read worker entrypoint missing")
    return files


def rehearse(output: Path, layout: str, files: dict[str, str], bundle: dict[str, Any],
             *, committed: bool, source_commit: str) -> dict[str, Any]:
    evidence = output / "cpu" / layout
    evidence.mkdir(parents=True, exist_ok=False)
    base = load(ROOT / BASE)
    archive = output / "source.tar.gz"
    with tempfile.TemporaryDirectory(prefix="doc-read-exact-") as temporary:
        scratch = Path(temporary).resolve()
        mount = scratch / "input/dataset"
        mount.mkdir(parents=True)
        if layout == "archive":
            shutil.copy2(archive, mount / "source.tar.gz")
        elif layout == "expanded":
            base.extract(archive, mount / "generated/source", files)
        else:
            raise ValueError("known mount layout required")
        project = scratch / "project"
        base.materialize(mount, "source.tar.gz", digest(archive), "pyproject.toml", project, files)
        venv = scratch / "venv"
        subprocess.run(  # noqa: S603 - isolated local interpreter
            [str(Path(sys.base_prefix) / "bin/python3"), "-I", "-m", "venv", str(venv)],
            check=True,
        )
        python = venv / "bin/python"
        base.install(python, DATASET, bundle, None)
        subprocess.run(  # noqa: S603 - hash-pinned local wheel
            [str(python), "-I", "-m", "pip", "install", "--no-index", "--no-deps", str(WHEEL)],
            check=True,
        )

        def run(*arguments: str) -> None:
            env = os.environ.copy()
            for key in ("VIRTUAL_ENV", "PYTHONHOME", "PILOT_DEPENDENCY_DIR", "FROZEN_GIT_COMMIT"):
                env.pop(key, None)
            env.update(PYTHONPATH=str(project / "src"), PYTHONNOUSERSITE="1",
                       PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
            result = subprocess.run(  # noqa: S603 - fixed isolated interpreter
                [str(python), *arguments], cwd=project, env=env, check=False,
                text=True, capture_output=True,
            )
            with (evidence / "commands.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(dict(arguments=arguments, stdout=result.stdout,
                                             stderr=result.stderr, returncode=result.returncode)))
                stream.write("\n")
            result.check_returncode()

        run("-c", "import importlib,pathlib,sys; "
            "names=['react_agent.llm.doc_read_native_dispatch_v1',"
            "'react_agent.validation.doc_read_native_admission_v1',"
            "'react_agent.validation.doc_read_native_release_v1',"
            "'react_agent.validation.doc_read_pair_audit_v1',"
            "'react_agent.security_v1.doc_read_pair_runtime_v1']; "
            "modules=[importlib.import_module(n) for n in names]; "
            "modules[0].execution_source(pathlib.Path('.')); "
            "assert all(pathlib.Path(m.__file__).resolve().is_relative_to"
            "(pathlib.Path('src').resolve()) for m in modules); "
            "assert not {'torch','transformers','tokenizers'} & sys.modules.keys(); "
            "assert not any(n.startswith('react_agent.authoring') or "
            "'doc_read_final_controls' in n for n in sys.modules); "
            "print('DOC_READ_ISOLATED_IMPORT_OK')")
        run("scripts/run_phase5_doc_read_native_v1.py", "--help")
        if committed:
            run("-c", "from pathlib import Path; import sys; "
                "from react_agent.validation.doc_read_native_admission_v1 import admit_source; "
                "admit_source(Path('.'),Path(sys.argv[1]),sys.argv[2],sys.argv[3]); "
                "print('DOC_READ_COMMITTED_SOURCE_ADMITTED')",
                str(output / "source_manifest.json"), digest(output / "source_manifest.json"),
                source_commit)
        run("scripts/preflight_clean_worker.py")
        dummy = evidence / "dummy"
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy))
        before = inventory(dummy)
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy), "--resume")
        # Root summaries may be refreshed by the frozen clean runner; task/identity must not be.
        stable = {n: s for n, s in before.items() if n.startswith("tasks/") or n == "identity.json"}
        after = inventory(dummy)
        if any(after.get(n) != s for n, s in stable.items()):
            raise ValueError("complete clean resume mutated retained tasks")
        partial = evidence / "dummy_partial"
        partial.mkdir()
        shutil.copy2(dummy / "identity.json", partial / "identity.json")
        for task in sorted((dummy / "tasks").iterdir())[:-1]:
            shutil.copytree(task, partial / "tasks" / task.name)
        retained = inventory(partial)
        run("scripts/run_clean_v11_dev.py", "--output", str(partial), "--resume")
        after_partial = inventory(partial)
        if any(after_partial.get(n) != s for n, s in retained.items()) or any(
            len(list((root / "tasks").iterdir())) != 21 for root in (dummy, partial)
        ):
            raise ValueError("missing-only clean resume changed retained tasks or count")
        base.verify_tree(project, files)
    return dict(layout=layout, valid=True, isolated_python=True, offline_wheels=True, tools=8,
                doc_read_native_imports=True, doc_read_native_cli_help=True,
                clean_dummy_tasks=21, clean_missing_only_resume=True,
                native_inference_runs=0, committed_source_admitted=committed,
                raw_sha256=inventory(evidence))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--committed", action="store_true")
    args = parser.parse_args()
    no_links(args.output)
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle package root required")
    git_base = subprocess.check_output(  # noqa: S603 - read-only Git identity
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,  # noqa: S607
    ).strip()
    manifest_path = DATASET / "guard_bundle.json"
    if digest(manifest_path) != BUNDLE_SHA or digest(WHEEL) != WHEEL_SHA:
        raise ValueError("frozen offline dependency bundle changed")
    bundle = json.loads(manifest_path.read_text())
    for name, expected in bundle["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("frozen base source changed")
    files = worker_files(bundle["source_sha256"])
    if args.committed:
        committed_sources(files, git_base)
    output.mkdir(parents=True)
    make_archive(ROOT, files, output / "source.tar.gz")
    source_mode = "committed" if args.committed else "working_tree_cpu_only"
    write_receipt(output / "source_manifest.json", dict(
        protocol=SOURCE_PROTOCOL if args.committed else "phase5_doc_read_package_dev_v1",
        source_mode=source_mode, git_base_commit=git_base,
        source_commit=git_base if args.committed else None,
        source_sha256=files, archive_sha256=digest(output / "source.tar.gz"),
    ))
    layouts = [rehearse(output, layout, files, bundle, committed=args.committed,
                       source_commit=git_base) for layout in ("archive", "expanded")]
    write_receipt(output / "preflight.json", dict(
        protocol="phase5_doc_read_package_v1", source_mode=source_mode, git_base_commit=git_base,
        source_commit=git_base if args.committed else None,
        worker_files=len(files), layouts=layouts,
        source_manifest_sha256=digest(output / "source_manifest.json"),
        archive_sha256=digest(output / "source.tar.gz"), native_inference_runs=0,
        selected_prospective_tasks=0, release_admitted=False, phase5_accepted=False,
    ))
    print("DOC_READ_PACKAGE_PREFLIGHT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
