"""CPU-only two-layout package rehearsal for the prospective room-ticket route.

This uses working-tree bytes and labels Git HEAD only as a base. It cannot
enable HF/Kaggle inference or certify a source commit.
"""

from __future__ import annotations

import argparse
import hashlib
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

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.validation.clause_dev_release_v1 import safe_name

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset"
WHEEL = ROOT / "build/kaggle/worker_progress_v1_wheels/tqdm-4.67.3-py3-none-any.whl"
SEEDS = {
    "pyproject.toml",
    "scripts/preflight_clean_worker.py",
    "scripts/run_clean_v11_dev.py",
    "scripts/run_phase5_room_ticket_native_v1.py",
    "scripts/run_phase5_room_prospective_native_v2.py",
    "src/react_agent/llm/room_control_native_dispatch_v1.py",
    "src/react_agent/llm/room_ticket_native_dispatch_v1.py",
    "src/react_agent/security_v1/room_control_pair_runtime_v1.py",
    "src/react_agent/security_v1/room_ticket_pair_runtime_v1.py",
    "src/react_agent/validation/room_control_native_release_v1.py",
    "src/react_agent/validation/room_control_pair_audit_v1.py",
    "src/react_agent/validation/room_inventory_review_v1.py",
    "src/react_agent/validation/room_prospective_run_manifest_v2.py",
    "src/react_agent/validation/room_ticket_native_release_v1.py",
    "src/react_agent/validation/room_ticket_pair_audit_v1.py",
    "src/react_agent/validation/room_ticket_run_manifest_v1.py",
}
PUBLIC = {
    "configs/agent/A0.yaml",
    "configs/runtime/default.yaml",
    "docs/evaluation/qwen7b_upstream_inventory_v1.json",
    "docs/evaluation/publisher_policy_v1/agent_generation_config.json",
    "docs/evaluation/publisher_policy_v1/guard_generation_config.json",
}


def worker_files(base_sources: dict[str, str]) -> dict[str, str]:
    """Reject evaluation/authoring sources and any non-public data before archive."""
    names = dependency_closure(ROOT, set(base_sources) | SEEDS) | PUBLIC
    allowed_data = {name for name in base_sources if name.startswith("data/")}
    files: dict[str, str] = {}
    for name in sorted(names):
        safe_name(name)
        if name.startswith("src/react_agent/authoring/") or (
            name.startswith("data/") and name not in allowed_data
        ):
            raise ValueError("authoring or non-public data in room-ticket worker")
        files[name] = digest(ROOT / name)
    if not SEEDS <= files.keys():
        raise ValueError("room-ticket worker entrypoint missing")
    return files


def committed_sources(files: dict[str, str], commit: str) -> None:
    """Refuse an untracked or modified worker file in committed mode."""
    for name, expected in files.items():
        try:
            frozen = subprocess.check_output(  # noqa: S603 - read-only Git blob
                ["git", "show", f"{commit}:{name}"],  # noqa: S607
                cwd=ROOT,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as error:
            raise ValueError("worker file is absent from committed source: " + name) from error
        if hashlib.sha256(frozen).hexdigest() != expected:
            raise ValueError("worker file differs from committed source: " + name)


def _inventory(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def rehearse(
    output: Path,
    layout: str,
    files: dict[str, str],
    bundle: dict[str, Any],
    *,
    committed: bool,
    source_commit: str,
) -> dict[str, Any]:
    evidence = output / "cpu" / layout
    evidence.mkdir(parents=True, exist_ok=False)
    base = load(ROOT / BASE)
    archive = output / "source.tar.gz"
    with tempfile.TemporaryDirectory(prefix="room-ticket-exact-") as temporary:
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
        subprocess.run(  # noqa: S603 - fresh isolated local venv
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
            env.update(
                PYTHONPATH=str(project / "src"),
                PYTHONNOUSERSITE="1",
                PYTHONDONTWRITEBYTECODE="1",
                HF_HUB_OFFLINE="1",
                TRANSFORMERS_OFFLINE="1",
            )
            subprocess.run(  # noqa: S603 - fixed local interpreter and declared arguments
                [str(python), *arguments], cwd=project, env=env, check=True
            )

        run(
            "-c",
            "import pathlib,sys,react_agent; "
            "from react_agent.llm.room_ticket_native_dispatch_v1 import run as native_dispatch; "
            "from react_agent.llm.room_control_native_dispatch_v1 import run as control_dispatch; "
            "from react_agent.validation.room_ticket_native_release_v1 "
            "import audit as release_audit; "
            "from react_agent.validation.room_ticket_run_manifest_v1 import admit_run; "
            "from react_agent.validation.room_prospective_run_manifest_v2 import audit_triplet; "
            "from react_agent.security_v1.room_ticket_pair_runtime_v1 import run_pair_task; "
            "from react_agent.validation.room_ticket_pair_audit_v1 import audit_join; "
            "from react_agent.validation.room_inventory_review_v1 import RoomInventoryReview; "
            "assert pathlib.Path(react_agent.__file__).resolve().is_relative_to"
            "(pathlib.Path('src').resolve()); "
            "assert not {'torch','transformers','tokenizers'} & sys.modules.keys(); "
            "assert not any(name.startswith('react_agent.authoring') for name in sys.modules); "
            "print('ROOM_TICKET_ISOLATED_IMPORT_OK')",
        )
        run("scripts/run_phase5_room_ticket_native_v1.py", "--help")
        run("scripts/run_phase5_room_prospective_native_v2.py", "--help")
        if committed:
            run(
                "-c",
                "import pathlib,sys; "
                "from react_agent.validation.room_ticket_native_release_v1 "
                "import admit_source; "
                "admit_source(pathlib.Path('.'),pathlib.Path(sys.argv[1]),"
                "sys.argv[2],sys.argv[3]); "
                "print('ROOM_PROSPECTIVE_COMMITTED_SOURCE_ADMITTED')",
                str(output / "source_manifest.json"),
                digest(output / "source_manifest.json"),
                source_commit,
            )
        run("scripts/preflight_clean_worker.py")
        dummy = evidence / "dummy"
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy))
        before = _inventory(dummy / "tasks")
        identity_hash = digest(dummy / "identity.json")
        run("scripts/run_clean_v11_dev.py", "--output", str(dummy), "--resume")
        if (
            _inventory(dummy / "tasks") != before
            or digest(dummy / "identity.json") != identity_hash
            or len(list((dummy / "tasks").iterdir())) != 21
        ):
            raise ValueError("completed clean Dev resume changed checkpoints")
        partial = evidence / "dummy_partial"
        partial.mkdir()
        shutil.copy2(dummy / "identity.json", partial / "identity.json")
        for task in sorted((dummy / "tasks").iterdir())[:-1]:
            shutil.copytree(task, partial / "tasks" / task.name)
        retained = _inventory(partial)
        run("scripts/run_clean_v11_dev.py", "--output", str(partial), "--resume")
        after = _inventory(partial)
        if len(list((partial / "tasks").iterdir())) != 21 or any(
            after.get(name) != sha for name, sha in retained.items()
        ):
            raise ValueError("missing-only clean Dev resume changed retained checkpoints")
        base.verify_tree(project, files)
        return {
            "layout": layout,
            "valid": True,
            "isolated_python": True,
            "offline_wheels": True,
            "tools": 8,
            "clean_dummy_tasks": 21,
            "clean_missing_only_resume": True,
            "native_inference_runs": 0,
            "committed_source_admitted": committed,
            "raw_sha256": _inventory(evidence),
        }


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
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=ROOT,
        text=True,
    ).strip()
    manifest_path = DATASET / "guard_bundle.json"
    if digest(manifest_path) != BUNDLE_SHA or digest(WHEEL) != WHEEL_SHA:
        raise ValueError("frozen offline dependency bundle changed")
    bundle: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in bundle["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("frozen worker base source changed")
    files = worker_files(bundle["source_sha256"])
    if args.committed:
        committed_sources(files, git_base)
    output.mkdir(parents=True)
    make_archive(ROOT, files, output / "source.tar.gz")
    write_receipt(
        output / "source_manifest.json",
        {
            "protocol": "phase5_room_ticket_source_v1"
            if args.committed
            else "phase5_room_ticket_package_dev_v1",
            "source_mode": "committed" if args.committed else "working_tree_cpu_only",
            "git_base_commit": git_base,
            "source_commit": git_base if args.committed else None,
            "source_sha256": files,
            "archive_sha256": digest(output / "source.tar.gz"),
        },
    )
    layouts = [
        rehearse(output, layout, files, bundle, committed=args.committed, source_commit=git_base)
        for layout in ("archive", "expanded")
    ]
    write_receipt(
        output / "preflight.json",
        {
            "protocol": "phase5_room_ticket_package_committed_v1"
            if args.committed
            else "phase5_room_ticket_package_dev_v1",
            "source_mode": "committed" if args.committed else "working_tree_cpu_only",
            "git_base_commit": git_base,
            "source_commit": git_base if args.committed else None,
            "source_manifest_sha256": digest(output / "source_manifest.json"),
            "archive_sha256": digest(output / "source.tar.gz"),
            "worker_files": len(files),
            "layouts": layouts,
            "selected_prospective_tasks": 0,
            "native_inference_runs": 0,
            "committed_source_admitted": args.committed,
            "release_admitted": False,
            "phase5_accepted": False,
        },
    )
    print("ROOM_TICKET_DEV_PACKAGE_PREFLIGHT_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
