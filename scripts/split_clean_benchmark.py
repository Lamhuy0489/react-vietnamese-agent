#!/usr/bin/env python3
"""Create the exact stratified group-wise Dev/Test split and freeze manifest."""

from __future__ import annotations

import hashlib
import json
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from shutil import which
from typing import Any

from react_agent.schemas.clean_task import CleanGroundTruth, CleanPublicTask

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data" / "clean" / "v1"
SPLIT_SEED = 2026
DEV_QUOTAS = {
    "single_source": 24,
    "parameter_extraction": 24,
    "multi_step": 30,
    "db_document": 24,
    "ambiguous": 15,
    "error_recovery": 18,
    "no_tool": 15,
}
TEST_QUOTAS = {
    "single_source": 16,
    "parameter_extraction": 16,
    "multi_step": 20,
    "db_document": 16,
    "ambiguous": 10,
    "error_recovery": 12,
    "no_tool": 10,
}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in records
    )
    path.write_text(payload, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_commit() -> str:
    git = which("git")
    if git is None:
        raise RuntimeError("git is required to record the source commit")
    result = subprocess.run(  # noqa: S603 - fixed executable and arguments
        [git, "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _assign_groups(tasks: list[CleanPublicTask]) -> dict[str, str]:
    rng = random.Random(SPLIT_SEED)  # noqa: S311 - reproducible split, not cryptography
    by_category: dict[str, dict[str, list[CleanPublicTask]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for task in tasks:
        by_category[task.category][task.instance_group_id].append(task)

    assignments: dict[str, str] = {}
    for category, target_dev in DEV_QUOTAS.items():
        groups = sorted(by_category[category].items())
        rng.shuffle(groups)
        dev_count = 0
        for _group_id, group_tasks in groups:
            group_size = len(group_tasks)
            if dev_count + group_size <= target_dev:
                split = "dev"
                dev_count += group_size
            else:
                split = "test"
            for task in group_tasks:
                assignments[task.task_id] = split
        if dev_count != target_dev:
            raise RuntimeError(
                f"cannot satisfy exact Dev quota for {category}: {dev_count} != {target_dev}"
            )
        if sum(len(group) for _, group in groups) - dev_count != TEST_QUOTAS[category]:
            raise RuntimeError(f"cannot satisfy exact Test quota for {category}")
    return assignments


def main() -> int:
    tasks = [
        CleanPublicTask.model_validate(record)
        for record in _load_jsonl(CLEAN_ROOT / "pool" / "tasks.jsonl")
    ]
    ground_truth = [
        CleanGroundTruth.model_validate(record)
        for record in _load_jsonl(CLEAN_ROOT / "private" / "pool_ground_truth.jsonl")
    ]
    assignments = _assign_groups(tasks)
    public_by_split: dict[str, list[dict[str, Any]]] = {"dev": [], "test": []}
    private_by_split: dict[str, list[dict[str, Any]]] = {"dev": [], "test": []}
    for task in tasks:
        split = assignments[task.task_id]
        payload = task.model_dump(mode="json")
        payload["split"] = split
        validated = CleanPublicTask.model_validate(payload)
        public_by_split[split].append(validated.model_dump(mode="json"))
    for item in ground_truth:
        private_by_split[assignments[item.task_id]].append(item.model_dump(mode="json"))
    for records in (*public_by_split.values(), *private_by_split.values()):
        records.sort(key=lambda record: record["task_id"])

    paths = {
        "splits/dev.jsonl": CLEAN_ROOT / "splits" / "dev.jsonl",
        "splits/test.jsonl": CLEAN_ROOT / "splits" / "test.jsonl",
        "private/dev_ground_truth.jsonl": CLEAN_ROOT / "private" / "dev_ground_truth.jsonl",
        "private/test_ground_truth.jsonl": CLEAN_ROOT / "private" / "test_ground_truth.jsonl",
    }
    _write_jsonl(paths["splits/dev.jsonl"], public_by_split["dev"])
    _write_jsonl(paths["splits/test.jsonl"], public_by_split["test"])
    _write_jsonl(paths["private/dev_ground_truth.jsonl"], private_by_split["dev"])
    _write_jsonl(paths["private/test_ground_truth.jsonl"], private_by_split["test"])

    dev_counts = Counter(record["category"] for record in public_by_split["dev"])
    test_counts = Counter(record["category"] for record in public_by_split["test"])
    if dev_counts != Counter(DEV_QUOTAS) or test_counts != Counter(TEST_QUOTAS):
        raise RuntimeError("stratified category count check failed")

    component_paths = {
        **paths,
        "environment/documents/documents.json": CLEAN_ROOT
        / "environment"
        / "documents"
        / "documents.json",
        "environment/cached_pages/pages.json": CLEAN_ROOT
        / "environment"
        / "cached_pages"
        / "pages.json",
        "environment/database/seed.json": CLEAN_ROOT / "environment" / "database" / "seed.json",
        "environment/database/university.db": CLEAN_ROOT
        / "environment"
        / "database"
        / "university.db",
        "manifests/environment_manifest.json": CLEAN_ROOT
        / "manifests"
        / "environment_manifest.json",
        "manifests/source_catalog.json": CLEAN_ROOT / "manifests" / "source_catalog.json",
        "reviews/review_log.jsonl": CLEAN_ROOT / "reviews" / "review_log.jsonl",
        "schemas/clean_task.py": ROOT / "src" / "react_agent" / "schemas" / "clean_task.py",
    }
    component_hashes = {name: _sha256(path) for name, path in component_paths.items()}
    dataset_hash = hashlib.sha256(
        "".join(f"{name}:{digest}\n" for name, digest in sorted(component_hashes.items())).encode()
    ).hexdigest()
    assignment_records = [
        {
            "task_id": task.task_id,
            "category": task.category,
            "instance_group_id": task.instance_group_id,
            "split": assignments[task.task_id],
        }
        for task in sorted(tasks, key=lambda item: item.task_id)
    ]
    split_manifest = {
        "benchmark_version": "clean_v1.0",
        "split_seed": SPLIT_SEED,
        "split_method": "stratified_group",
        "manual_moves": [],
        "dev_tasks": 150,
        "test_tasks": 100,
        "dev_category_counts": dict(sorted(dev_counts.items())),
        "test_category_counts": dict(sorted(test_counts.items())),
        "assignments": assignment_records,
    }
    split_manifest_path = CLEAN_ROOT / "manifests" / "split_manifest.json"
    split_manifest_path.write_text(
        json.dumps(split_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    benchmark_manifest = {
        "benchmark_version": "clean_v1.0",
        "environment_version": "clean_env_v1",
        "schema_version": "clean_task_v1",
        "source_commit": _source_commit(),
        "created_at": "2026-09-05",
        "split_seed": SPLIT_SEED,
        "split_method": "stratified_group",
        "dev_tasks": 150,
        "test_tasks": 100,
        "frozen": True,
        "test_model_runs": 0,
        "test_tuning_prohibited": True,
        "review_mode": "automated_checks_owner_waiver",
        "independent_human_review": False,
        "dataset_hash": dataset_hash,
        "component_hashes": component_hashes,
        "split_manifest_sha256": _sha256(split_manifest_path),
    }
    benchmark_manifest_path = CLEAN_ROOT / "manifests" / "benchmark_manifest.json"
    benchmark_manifest_path.write_text(
        json.dumps(benchmark_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Created frozen clean_v1.0 split: 150 Dev / 100 Test; dataset_hash={dataset_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
