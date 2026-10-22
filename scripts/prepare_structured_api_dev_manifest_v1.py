#!/usr/bin/env python3
"""Freeze a credential-free public Dev manifest for the structured API runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from react_agent.adversarial_release import load_split
from react_agent.agent.state import RuntimeConfig
from react_agent.llm.base import GenerationConfig
from react_agent.llm.structured_api_dev_v1 import ApiDevManifest, write_manifest

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    git = shutil.which("git")
    if git is None:
        return "unavailable"
    dirty = subprocess.run(  # noqa: S603, S607 - fixed executable and arguments
        [
            git,
            "status",
            "--porcelain",
            "--",
            "src/react_agent",
            "scripts",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if dirty.returncode == 0 and dirty.stdout.strip():
        return "working-tree"
    value = subprocess.run(  # noqa: S603, S607 - fixed executable and arguments
        [git, "rev-parse", "HEAD"],  # noqa: S603 - fixed executable
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return value.stdout.strip() if value.returncode == 0 else "unavailable"


def source_files() -> dict[str, str]:
    paths = sorted((ROOT / "src/react_agent").rglob("*.py"))
    paths.append(Path(__file__).resolve())
    return {str(path.relative_to(ROOT)): sha(path) for path in paths}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clean-root", type=Path, default=ROOT / "data/clean/v1_1")
    parser.add_argument(
        "--adversarial-root", type=Path, default=ROOT / "data/adversarial/release_v2"
    )
    parser.add_argument(
        "--api-directory",
        type=Path,
        default=ROOT / "build/kaggle/structured_pair_release01",
        help="directory containing non-secret *_live_metadata.json files",
    )
    parser.add_argument("--guard-pairs", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    clean_root = args.clean_root.resolve()
    adversarial_root = args.adversarial_root.resolve()
    if args.guard_pairs < 1:
        raise ValueError("at least one guard pair required")
    selection_path = clean_root / "dev_pilot/task_ids.json"
    split_path = clean_root / "splits/dev.jsonl"
    faults_path = clean_root / "dev_pilot/fault_plans.json"
    selected = json.loads(selection_path.read_text(encoding="utf-8"))
    task_ids = tuple(selected["task_ids"])
    rows = {
        json.loads(line)["task_id"]: json.loads(line)
        for line in split_path.read_text(encoding="utf-8").splitlines()
        if line
    }
    if any(task_id not in rows for task_id in task_ids):
        raise ValueError("selected task missing from public Dev split")
    fixtures = load_split(adversarial_root)
    attacks = {row.pair_id: row for row in fixtures if row.branch == "attack"}
    benign = {row.pair_id: row for row in fixtures if row.branch == "benign"}
    pairs = sorted(set(attacks) & set(benign))[: args.guard_pairs]
    if len(pairs) != args.guard_pairs:
        raise ValueError("insufficient complete public guard pairs")
    guard_ids = tuple(
        variant for pair in pairs for variant in (attacks[pair].variant_id, benign[pair].variant_id)
    )
    source = source_files()
    generation = GenerationConfig().model_dump(mode="json")

    def identity(role: str) -> dict[str, str]:
        metadata = json.loads(
            (args.api_directory / f"{role}_live_metadata.json").read_text(encoding="utf-8")
        )
        rows = metadata.get("data")
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise ValueError(f"{role} metadata must expose one model")
        return {
            "model_id": str(rows[0]["id"]),
            "model_revision": str(metadata["model_revision"]),
            "session_id": str(metadata["session_id"]),
            "source_commit": str(metadata["source_commit"]),
            "worker_sha256": str(metadata["worker_sha256"]),
        }

    manifest = ApiDevManifest(
        source_commit=git_commit(),
        source_files=source,
        clean_split_sha256=sha(split_path),
        clean_selection_sha256=sha(selection_path),
        clean_task_ids=task_ids,
        clean_task_categories={task_id: rows[task_id]["category"] for task_id in task_ids},
        clean_input_root=str(clean_root),
        fault_plans_sha256=sha(faults_path),
        adversarial_release_root=str(adversarial_root),
        adversarial_attack_sha256=sha(adversarial_root / "dev_attack.jsonl"),
        adversarial_benign_sha256=sha(adversarial_root / "dev_benign.jsonl"),
        guard_variant_ids=guard_ids,
        guard_pairs=tuple((attacks[pair].variant_id, benign[pair].variant_id) for pair in pairs),
        agent_identity=identity("agent"),
        guard_identity=identity("guard"),
        agent_generation=generation,
        guard_generation={"temperature": 0.0, "max_new_tokens": 128, "seed": 42},
        runtime=RuntimeConfig().model_dump(mode="json"),
    )
    write_manifest(args.output.resolve(), manifest)
    print(
        json.dumps(
            {
                "manifest": str(args.output.resolve()),
                "identity_sha256": manifest.identity,
                "clean_tasks": len(task_ids),
                "guard_pairs": len(pairs),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
