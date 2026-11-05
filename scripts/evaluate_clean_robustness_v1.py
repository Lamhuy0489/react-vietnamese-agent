#!/usr/bin/env python3
"""Score a clean robustness run: each variant with its canonical task's ground truth.

Always uses the rebuild numeric-token fix (``clean_rebuild_v1``), as the clean rebuild
runs do. A Test run (``"split": "test"``) is scored only while ``final_config_v2`` still
matches and the variants are exactly the sealed 250; dry runs and Dev smoke runs skip the
freeze check. ``--canonical-eval`` (an ``evaluate_clean_rebuild_v1.py`` report for the same
model and split) adds paired lost/gained counts per variant type.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import react_agent.evaluation.final_config_v2 as final_config_v2
from react_agent.authoring.robustness_v1 import load_sealed
from react_agent.evaluation.clean_robustness_v1 import score_checkpoint, summarize
from react_agent.schemas.clean_task import CleanGroundTruth
from react_agent.validation import clean_rebuild_v1

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = ROOT / "data/clean/v1_1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--canonical-eval", type=Path)
    args = parser.parse_args()
    evaluator = clean_rebuild_v1.activate()
    if args.output.exists():
        raise ValueError("evaluation output already exists; preserve prior artifacts")
    identity = json.loads((args.artifacts / "identity.json").read_text())
    if identity.get("benchmark") != "clean_robustness_v1":
        raise ValueError("not a clean robustness run")
    split = identity["split"]
    expected = hashlib.sha256((CLEAN_ROOT / f"splits/{split}.jsonl").read_bytes()).hexdigest()
    if identity["file_sha256"][split] != expected:
        raise ValueError(f"public {split} identity mismatch")
    variants = identity["variants"]
    if split == "test":
        sealed = [r["variant_id"] for r in load_sealed(ROOT)]
        if [v["variant_id"] for v in variants] != sealed:
            raise ValueError("Test runs must cover exactly the sealed variants")
        if not identity.get("dry_run_dummy"):
            final_config_v2.verify(ROOT)
            if identity.get("final_config_sha256") != final_config_v2.manifest_sha256(ROOT):
                raise ValueError("Test run was not made under the current freeze manifest")
    truths = {item.task_id: item for item in (
        CleanGroundTruth.model_validate_json(line) for line in
        (CLEAN_ROOT / f"private/{split}_ground_truth.jsonl").read_text().splitlines())}
    canonical_success = None
    if args.canonical_eval:
        canonical = json.loads(args.canonical_eval.read_text())
        if canonical["source_identity"]["model_key"] != identity["model_key"] or (
                canonical["source_identity"].get("split", "dev") != split):
            raise ValueError("canonical evaluation is for another model or split")
        canonical_success = {r["task_id"]: bool(r["success"]) for r in canonical["results"]}
    rows = []
    for variant in variants:
        outcome = score_checkpoint(args.artifacts / "tasks" / variant["variant_id"],
                                   truths[variant["canonical_task_id"]],
                                   CLEAN_ROOT / "environment")
        rows.append({**variant, **outcome})
    report = {
        "evaluator": evaluator,
        "scope": ("DRY RUN with a CPU stand-in; not a result" if identity.get("dry_run_dummy")
                  else "Held-out Test (RQ3)" if split == "test"
                  else "Dev smoke diagnostic; not a thesis result"),
        "test_variants_read": len(rows) if split == "test" else 0,
        "evaluated_variants": len(rows),
        "successes": sum(bool(row["success"]) for row in rows),
        "per_type": summarize(rows, canonical_success),
        "failures": dict(Counter(reason for row in rows for reason in row["failures"])),
        "source_identity": identity,
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"results", "source_identity"}},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
