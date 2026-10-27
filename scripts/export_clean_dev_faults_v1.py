#!/usr/bin/env python3
"""Export the tool fault plans of the clean v1.1 Dev (150) or Test (100) tasks for the API worker.

Fault plans configure the mock tool environment (which call times out), never the
prompt, so the worker may read them; answers and validators stay private. This
mirrors ``dev_pilot/fault_plans.json`` (copied from the same Dev ground truth)
for the full Dev split. ``--split test`` reads only the ``fault_plan`` field of the
Test ground truth, once, before the R3 freeze; nothing else of it leaves the file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data/clean/v1_1"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    split = parser.parse_args().split
    output = ROOT / f"configs/clean/{split}_fault_plans_v1.json"
    source = CLEAN_ROOT / f"private/{split}_ground_truth.jsonl"
    truths = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    public_ids = [json.loads(line)["task_id"] for line in
                  (CLEAN_ROOT / f"splits/{split}.jsonl").read_text(encoding="utf-8").splitlines()]
    if sorted(item["task_id"] for item in truths) != sorted(public_ids):
        raise ValueError(f"ground truth must cover exactly the public {split} split")
    plans = {item["task_id"]: item["fault_plan"] for item in truths if item["fault_plan"]}
    payload = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "split": split, "fault_plans": dict(sorted(plans.items()))}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(plans)} fault plans -> {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
