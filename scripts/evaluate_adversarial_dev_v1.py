#!/usr/bin/env python3
"""Score saved A0–A6 adversarial Dev executions offline (no inference).

Reads ``run_adversarial_dev_api_v1.py`` output, scores every execution with the
frozen per-case scorer and writes per-execution scores plus the per-level
metrics of docs/metrics_spec.md. The split comes from the run identity: Dev by
default; a Test run is scored only while the R3 freeze manifest still matches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import react_agent.evaluation.final_config_v1 as final_config_v1
from react_agent.adversarial_release import load_split
from react_agent.authoring.selected_runtime import load_selected
from react_agent.evaluation.adversarial_v1 import score_execution, summarize

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    identity = json.loads((args.run / "identity.json").read_text())
    split = identity.get("split", "dev")
    if split == "test" and not identity.get("dry_run_dummy"):
        final_config_v1.verify(ROOT)
        if identity.get("final_config_sha256") != final_config_v1.manifest_sha256(ROOT):
            raise ValueError("Test run was not made under the current freeze manifest")
    rows = {row.variant_id: row for row in load_split(
        ROOT / "data/adversarial/release_v2", split, allow_held_out=split == "test")}
    _, cases = load_selected(ROOT)
    records = []
    for path in sorted(args.run.glob("runs/*/*/result.json")):
        saved = json.loads(path.read_text())
        folder = path.parent
        trace = folder / "execution/trace_legacy.jsonl"
        if hashlib.sha256(trace.read_bytes()).hexdigest() != saved["trace_sha256"]:
            raise ValueError(f"trace changed after checkpoint: {folder}")
        row = rows[saved["variant_id"]]
        case = cases[row.task.task_id]
        if case.selection["split"] != split:
            raise ValueError(f"case outside the run's {split} split")
        score = score_execution(case, folder / "execution",
                                folder / "environment/database/university.db")
        records.append({key: saved[key] for key in ("level", "variant_id", "branch", "family_id")}
                       | {"variant_type": row.variant_type, "score": score})
    report = summarize(records) | {
        "run_identity_sha256": hashlib.sha256(
            (args.run / "identity.json").read_bytes()).hexdigest(),
        "model_id": identity["model_id"],
        "scope": ("DRY RUN with CPU stand-ins; not a result" if identity.get("dry_run_dummy")
                  else "Held-out Test" if split == "test" else "Dev diagnostic; not a Test result"),
        "test_cases_scored": len(records) if split == "test" else 0, "executions": len(records)}
    output = args.output or args.run.with_name(args.run.name + "_eval.json")
    output.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (output.with_suffix(".records.jsonl")).write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    for level, entry in report["levels"].items():
        asr, util = entry.get("asr", {}), entry.get("benign_utility", {})
        print(level, "ASR", asr.get("k"), "/", asr.get("n"),
              "benign utility", util.get("k"), "/", util.get("n"),
              "model_error", entry["model_error"])


if __name__ == "__main__":
    main()
