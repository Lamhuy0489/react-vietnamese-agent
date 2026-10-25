#!/usr/bin/env python3
"""Export the tool fault plans of all 150 clean v1.1 Dev tasks for the API worker.

Fault plans configure the mock tool environment (which call times out), never the
prompt, so the worker may read them; answers and validators stay private. This
mirrors ``dev_pilot/fault_plans.json`` (copied from the same Dev ground truth)
for the full Dev split. Test ground truth is never opened.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data/clean/v1_1"
OUTPUT = ROOT / "configs/clean/dev_fault_plans_v1.json"


def main() -> None:
    source = CLEAN_ROOT / "private/dev_ground_truth.jsonl"
    truths = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    dev_ids = [json.loads(line)["task_id"] for line in
               (CLEAN_ROOT / "splits/dev.jsonl").read_text(encoding="utf-8").splitlines()]
    if sorted(item["task_id"] for item in truths) != sorted(dev_ids):
        raise ValueError("ground truth must cover exactly the public Dev split")
    plans = {item["task_id"]: item["fault_plan"] for item in truths if item["fault_plan"]}
    payload = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "split": "dev", "fault_plans": dict(sorted(plans.items()))}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(plans)} fault plans -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
