"""Validate the sealed stratified group-wise clean benchmark split."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from react_agent.schemas.clean_task import CleanGroundTruth, CleanPublicTask

ROOT = Path(__file__).resolve().parents[3]
CLEAN_ROOT = ROOT / "data" / "clean" / "v1"
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic_signature(item: CleanGroundTruth) -> str:
    return json.dumps(
        {
            "facts": [fact.model_dump(mode="json") for fact in item.required_answer_facts],
            "retrieval_targets": item.retrieval_targets,
            "evidence": [entry.model_dump(mode="json") for entry in item.required_evidence],
            "missing_slots": item.missing_slots,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def validate_clean_split(clean_root: Path = CLEAN_ROOT) -> dict[str, Any]:
    failures: list[str] = []
    paths = {
        "dev": clean_root / "splits" / "dev.jsonl",
        "test": clean_root / "splits" / "test.jsonl",
        "dev_gt": clean_root / "private" / "dev_ground_truth.jsonl",
        "test_gt": clean_root / "private" / "test_ground_truth.jsonl",
        "split_manifest": clean_root / "manifests" / "split_manifest.json",
        "benchmark_manifest": clean_root / "manifests" / "benchmark_manifest.json",
    }
    for name, path in paths.items():
        if not path.is_file():
            failures.append(f"missing {name}: {path}")
    if failures:
        return {"valid": False, "failures": failures}

    try:
        dev = [CleanPublicTask.model_validate(item) for item in _load_jsonl(paths["dev"])]
        test = [CleanPublicTask.model_validate(item) for item in _load_jsonl(paths["test"])]
        dev_gt = [CleanGroundTruth.model_validate(item) for item in _load_jsonl(paths["dev_gt"])]
        test_gt = [CleanGroundTruth.model_validate(item) for item in _load_jsonl(paths["test_gt"])]
    except ValidationError as error:
        return {"valid": False, "failures": [f"split schema validation failed: {error}"]}

    if len(dev) != 150 or len(test) != 100:
        failures.append(f"expected 150/100 records, found {len(dev)}/{len(test)}")
    if any(task.split != "dev" for task in dev) or any(task.split != "test" for task in test):
        failures.append("public split labels do not match their physical files")
    dev_ids = {task.task_id for task in dev}
    test_ids = {task.task_id for task in test}
    if dev_ids & test_ids:
        failures.append("task IDs overlap between Dev and Test")
    expected_ids = {f"clean_{index:04d}" for index in range(1, 251)}
    if dev_ids | test_ids != expected_ids:
        failures.append("Dev/Test union does not reconstruct the 250-task pool")
    if {item.task_id for item in dev_gt} != dev_ids:
        failures.append("private Dev ground truth does not align with public Dev")
    if {item.task_id for item in test_gt} != test_ids:
        failures.append("private Test ground truth does not align with public Test")
    dev_groups = {task.instance_group_id for task in dev}
    test_groups = {task.instance_group_id for task in test}
    if dev_groups & test_groups:
        failures.append("instance groups overlap between Dev and Test")

    dev_counts = Counter(task.category for task in dev)
    test_counts = Counter(task.category for task in test)
    if dev_counts != Counter(DEV_QUOTAS):
        failures.append(f"Dev category quota mismatch: {dict(dev_counts)}")
    if test_counts != Counter(TEST_QUOTAS):
        failures.append(f"Test category quota mismatch: {dict(test_counts)}")

    dev_signatures = {_semantic_signature(item) for item in dev_gt}
    test_signatures = {_semantic_signature(item) for item in test_gt}
    semantic_overlap = dev_signatures & test_signatures
    if semantic_overlap:
        failures.append(f"semantic instance overlap between Dev/Test: {len(semantic_overlap)}")

    dev_sources = {entry.source_id for item in dev_gt for entry in item.required_evidence}
    test_sources = {entry.source_id for item in test_gt for entry in item.required_evidence}
    source_overlap = sorted(dev_sources & test_sources)
    manifest = json.loads(paths["benchmark_manifest"].read_text(encoding="utf-8"))
    split_manifest = json.loads(paths["split_manifest"].read_text(encoding="utf-8"))
    if manifest.get("frozen") is not True or manifest.get("test_tuning_prohibited") is not True:
        failures.append("benchmark manifest does not seal Test")
    if manifest.get("test_model_runs") != 0:
        failures.append("benchmark manifest records a model run on held-out Test")
    if manifest.get("split_seed") != 2026 or split_manifest.get("split_seed") != 2026:
        failures.append("split seed is not 2026")
    if split_manifest.get("manual_moves") != []:
        failures.append("split manifest contains an unapproved manual move")
    assignment_map = {
        item["task_id"]: item["split"] for item in split_manifest.get("assignments", [])
    }
    for task_id in dev_ids:
        if assignment_map.get(task_id) != "dev":
            failures.append(f"split manifest mismatch for {task_id}")
    for task_id in test_ids:
        if assignment_map.get(task_id) != "test":
            failures.append(f"split manifest mismatch for {task_id}")

    component_hashes = manifest.get("component_hashes", {})
    for relative, expected_hash in component_hashes.items():
        path = (
            ROOT / "src" / "react_agent" / "schemas" / "clean_task.py"
            if relative == "schemas/clean_task.py"
            else clean_root / relative
        )
        if not path.is_file() or _sha256(path) != expected_hash:
            failures.append(f"frozen component hash mismatch: {relative}")
    if manifest.get("split_manifest_sha256") != _sha256(paths["split_manifest"]):
        failures.append("split manifest hash mismatch")

    return {
        "valid": not failures,
        "failures": failures,
        "dev_tasks": len(dev),
        "test_tasks": len(test),
        "dev_category_counts": dict(sorted(dev_counts.items())),
        "test_category_counts": dict(sorted(test_counts.items())),
        "group_overlap": len(dev_groups & test_groups),
        "semantic_overlap": len(semantic_overlap),
        "source_overlap_count": len(source_overlap),
        "source_overlap": source_overlap,
        "dataset_hash": manifest.get("dataset_hash"),
        "test_sha256": _sha256(paths["test"]),
        "test_ground_truth_sha256": _sha256(paths["test_gt"]),
    }
