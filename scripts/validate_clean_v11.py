#!/usr/bin/env python3
"""Run replacement-pool QA, write actual check evidence, and preview the split."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from react_agent.validation.clean_split import DEV_QUOTAS
from react_agent.validation.clean_v11 import load_pool, validate_pool
from react_agent.validation.group_split import assign_groups

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data/clean/v1_1"


def main() -> int:
    result = validate_pool(CLEAN_ROOT)
    tasks, _ = load_pool(CLEAN_ROOT)
    assignments = assign_groups(tasks, DEV_QUOTAS, seed=2026)
    report_root = CLEAN_ROOT / "reports"
    report_root.mkdir(parents=True, exist_ok=True)
    rows = result.pop("qa_records")
    for name, data in (("qa_records.json", rows), ("pool_validation.json", result)):
        (report_root / name).write_text(
            json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    counts = {
        split: dict(Counter(task.category for task in tasks if assignments[task.task_id] == split))
        for split in ("dev", "test")
    }
    print(json.dumps({**result, "split_preview": counts}, ensure_ascii=False, indent=2))
    return int(not result["valid"])


if __name__ == "__main__":
    raise SystemExit(main())
