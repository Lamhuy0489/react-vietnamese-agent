"""Read-only structural/hash validation of replacement data, never model evaluation."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from react_agent.schemas.clean_task import CleanGroundTruth, CleanPublicTask
from react_agent.validation.clean_integrity import dataset_digest, semantic_instance_signature
from react_agent.validation.clean_split import DEV_QUOTAS, TEST_QUOTAS

ROOT = Path(__file__).resolve().parents[3]
REQUIRED = {
    "pool/tasks.jsonl",
    "private/pool_ground_truth.jsonl",
    "splits/dev.jsonl",
    "splits/test.jsonl",
    "private/dev_ground_truth.jsonl",
    "private/test_ground_truth.jsonl",
    "private/robustness_canonical_ids.json",
    "environment/documents/documents.json",
    "environment/cached_pages/pages.json",
    "environment/database/seed.json",
    "environment/database/university.db",
    "manifests/source_catalog.json",
    "manifests/environment_manifest.json",
    "manifests/split_manifest.json",
    "dev_pilot/task_ids.json",
    "dev_pilot/fault_plans.json",
    "reports/qa_records.json",
    "reports/pool_validation.json",
}


def validate_seal(root: Path) -> list[str]:
    failures: list[str] = []
    try:
        manifest = json.loads((root / "manifests/benchmark_manifest.json").read_text())
        hashes = manifest["component_hashes"]
        if set(hashes) != REQUIRED:
            failures.append("component inventory mismatch")
        for relative in sorted(REQUIRED):
            path = root / relative
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != hashes.get(
                relative
            ):
                failures.append(f"component hash mismatch: {relative}")
        if manifest["dataset_hash"] != dataset_digest(hashes):
            failures.append("aggregate hash mismatch")
        if manifest.get("frozen") is not True or manifest.get("benchmark") != "clean_v1.1":
            failures.append("missing clean_v1.1 freeze")
        if (
            manifest["schema_sha256"]
            != hashlib.sha256(
                (ROOT / "src/react_agent/schemas/clean_task.py").read_bytes()
            ).hexdigest()
        ):
            failures.append("schema hash mismatch")
        groups: dict[str, set[str]] = {}
        signatures: dict[str, set[str]] = {}
        all_ids: set[str] = set()
        split_ids: dict[str, set[str]] = {}
        for split, quotas in (("dev", DEV_QUOTAS), ("test", TEST_QUOTAS)):
            tasks = [
                CleanPublicTask.model_validate_json(line)
                for line in (root / f"splits/{split}.jsonl").read_text().splitlines()
            ]
            truth = [
                CleanGroundTruth.model_validate_json(line)
                for line in (root / f"private/{split}_ground_truth.jsonl").read_text().splitlines()
            ]
            ids = [task.task_id for task in tasks]
            if len(set(ids)) != len(ids) or set(ids) & all_ids:
                failures.append("duplicate/cross-split task IDs")
            split_ids[split] = set(ids)
            all_ids.update(ids)
            if [item.task_id for item in truth] != ids or any(
                task.split != split for task in tasks
            ):
                failures.append("public/private split join mismatch")
            if Counter(task.category for task in tasks) != Counter(quotas):
                failures.append("category quotas mismatch")
            groups[split] = {task.instance_group_id for task in tasks}
            signatures[split] = {semantic_instance_signature(item) for item in truth}
        if groups["dev"] & groups["test"] or signatures["dev"] & signatures["test"]:
            failures.append("cross-split semantic/group overlap")
        if all_ids != {f"clean_{index:04d}" for index in range(1, 251)}:
            failures.append("split union mismatch")
        pilot = json.loads((root / "dev_pilot/task_ids.json").read_text())["task_ids"]
        robustness = json.loads((root / "private/robustness_canonical_ids.json").read_text())[
            "task_ids"
        ]
        if len(pilot) != 21 or len(set(pilot)) != 21 or not set(pilot) <= split_ids["dev"]:
            failures.append("pilot selection invalid")
        if (
            len(robustness) != 50
            or len(set(robustness)) != 50
            or not set(robustness) <= split_ids["test"]
        ):
            failures.append("robustness selection invalid")
    except (OSError, ValueError, KeyError, TypeError) as error:
        failures.append(f"invalid seal: {error}")
    return failures
