#!/usr/bin/env python3
"""Seal the independently versioned replacement after executable pool QA."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from build_clean_v11 import write_jsonl

from react_agent.validation.clean_integrity import assert_clean_version_writable, dataset_digest
from react_agent.validation.clean_split import DEV_QUOTAS, TEST_QUOTAS
from react_agent.validation.clean_v11 import load_pool, validate_pool
from react_agent.validation.group_split import assign_groups

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data/clean/v1_1"


def main() -> int:
    assert_clean_version_writable(CLEAN_ROOT)
    qa = validate_pool(CLEAN_ROOT)
    if not qa["valid"]:
        raise ValueError(f"refusing to seal invalid pool: {qa['failures']}")
    tasks, truth = load_pool(CLEAN_ROOT)
    assignment = assign_groups(tasks, DEV_QUOTAS, seed=2026)
    quotas = {"dev": DEV_QUOTAS, "test": TEST_QUOTAS}
    for split, expected in quotas.items():
        if Counter(task.category for task in tasks if assignment[task.task_id] == split) != Counter(
            expected
        ):
            raise ValueError("split quota mismatch")
    for split in quotas:
        write_jsonl(
            CLEAN_ROOT / f"splits/{split}.jsonl",
            [
                {**task.model_dump(mode="json"), "split": split}
                for task in tasks
                if assignment[task.task_id] == split
            ],
        )
        write_jsonl(
            CLEAN_ROOT / f"private/{split}_ground_truth.jsonl",
            [item.model_dump(mode="json") for item in truth if assignment[item.task_id] == split],
        )
    selection = [
        task.task_id
        for category in DEV_QUOTAS
        for task in [t for t in tasks if t.category == category and assignment[t.task_id] == "dev"][
            :3
        ]
    ]
    robustness = [task.task_id for task in tasks if assignment[task.task_id] == "test"]
    random.Random(2026).shuffle(robustness)  # noqa: S311 - frozen selection, not cryptography
    records = {
        "dev_pilot/task_ids.json": {
            "task_ids": selection,
            "method": "first_three_per_category_before_inference",
        },
        "dev_pilot/fault_plans.json": {
            item.task_id: [spec.model_dump(mode="json") for spec in item.fault_plan]
            for item in truth
            if item.task_id in selection and item.fault_plan
        },
        "private/robustness_canonical_ids.json": {
            "task_ids": sorted(robustness[:50]),
            "seed": 2026,
            "variants_not_created": True,
        },
        "reports/qa_records.json": qa.pop("qa_records"),
        "reports/pool_validation.json": qa,
        "manifests/split_manifest.json": {
            "benchmark": "clean_v1.1",
            "seed": 2026,
            "manual_moves": [],
            "assignments": [
                {
                    "task_id": task.task_id,
                    "category": task.category,
                    "instance_group_id": task.instance_group_id,
                    "split": assignment[task.task_id],
                }
                for task in tasks
            ],
        },
    }
    for relative, value in records.items():
        path = CLEAN_ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    hashes = {
        path.relative_to(CLEAN_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(CLEAN_ROOT.rglob("*"))
        if path.is_file()
    }
    manifest = {
        "benchmark": "clean_v1.1",
        "frozen": True,
        "test_model_runs": 0,
        "component_hashes": hashes,
        "dataset_hash": dataset_digest(hashes),
        "schema_sha256": hashlib.sha256(
            (ROOT / "src/react_agent/schemas/clean_task.py").read_bytes()
        ).hexdigest(),
        "supersedes": "clean_v1.0_quarantined",
        "human_review": "waived_not_claimed",
        "acceptance_scope": "executable_structural_QA; not human language-quality certification",
    }
    (CLEAN_ROOT / "manifests/benchmark_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "sealed": True,
                "dataset_hash": manifest["dataset_hash"],
                "dev": 150,
                "test": 100,
                "pilot": 21,
                "robustness_canonicals": 50,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
