#!/usr/bin/env python3
"""Rescore saved A0–A6 adversarial executions with the side-effect harm metric (no inference).

Same checks as ``evaluate_adversarial_dev_v1.py`` (trace hashes, Test freeze manifest),
except that files added after the freeze are allowed: every file the v1 manifest pins
must still match, so the frozen scorer is the one that scored R4. Each record keeps
the frozen v1 score next to the side-effect fields. On Test v1 the result is a post-hoc
secondary metric (decision log 2026-10-28).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import react_agent.evaluation.final_config_v1 as final_config_v1
from react_agent.adversarial_release import load_split
from react_agent.authoring.selected_runtime import load_selected
from react_agent.evaluation.adversarial_v1 import score_execution
from react_agent.evaluation.side_effect_harm_v1 import side_effect_score, summarize_side_effect
from react_agent.schemas.trace import TraceEvent

ROOT = Path(__file__).resolve().parents[1]


def verify_pinned() -> None:
    """Every v1-pinned file unchanged; new files (v2 work) do not touch the v1 scorer."""
    manifest = json.loads((ROOT / final_config_v1.MANIFEST).read_text(encoding="utf-8"))
    current = final_config_v1.frozen_hashes(ROOT)
    changed = sorted(k for k, sha in manifest["files"].items() if current.get(k) != sha)
    if changed:
        raise final_config_v1.FrozenConfigError("pinned files changed: " + ", ".join(changed[:10]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    identity = json.loads((args.run / "identity.json").read_text())
    split = identity.get("split", "dev")
    if split == "test" and not identity.get("dry_run_dummy"):
        verify_pinned()
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
        database = folder / "environment/database/university.db"
        events = [TraceEvent.model_validate_json(line)
                  for line in trace.read_text(encoding="utf-8").splitlines()]
        score = score_execution(case, folder / "execution", database)
        score |= side_effect_score(events, case.score(events, database))
        records.append({key: saved[key] for key in ("level", "variant_id", "branch", "family_id")}
                       | {"variant_type": row.variant_type, "score": score})
    report = summarize_side_effect(records) | {
        "run_identity_sha256": hashlib.sha256(
            (args.run / "identity.json").read_bytes()).hexdigest(),
        "model_id": identity["model_id"],
        "scope": ("DRY RUN with CPU stand-ins; not a result" if identity.get("dry_run_dummy")
                  else "Held-out Test v1: post-hoc secondary metric" if split == "test"
                  else "Dev diagnostic; not a Test result"),
        "executions": len(records)}
    output = args.output or args.run.with_name(args.run.name + "_side_effect.json")
    output.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (output.with_suffix(".records.jsonl")).write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    for level, entry in report["levels"].items():
        paired, util = entry.get("attributable_asr", {}), entry.get("benign_utility", {})
        harm = sum(r["score"]["side_effect_harm"] for r in records
                   if r["level"] == level and r["branch"] == "benign")
        print(level, "paired side-effect ASR", paired.get("k"), "/", paired.get("n"),
              "benign harm", harm, "benign utility", util.get("k"), "/", util.get("n"))


if __name__ == "__main__":
    main()
