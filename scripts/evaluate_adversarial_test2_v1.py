#!/usr/bin/env python3
"""Score the Test-2 runs (A0, A1, A6, D2, D2+G) offline with the sealed oracles.

Pass every run directory of the matrix (``run_adversarial_e2_api_v1.py --release test2``
output). Each ``runs/<level>`` folder becomes a configuration: the level name for the
closure runtime, or the defense name from the identity (``runs/A1`` = D2, ``runs/A2`` =
D2+G). Checks: trace hashes, one model, each configuration once, all 200 fixtures per
configuration, and ``final_config_v2`` unchanged for real runs (dry runs skip it).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import react_agent.evaluation.final_config_v2 as final_config_v2
from react_agent.authoring.test2_v1 import load_test2
from react_agent.evaluation.test2_eval_v1 import CONFIGS, score_execution, summarize_test2

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("evaluation output already exists; preserve prior artifacts")
    fixtures, privates = load_test2(ROOT)
    rows = {row.variant_id: row for row in fixtures}
    identities = [json.loads((run / "identity.json").read_text()) for run in args.runs]
    dry = {bool(i.get("dry_run_dummy")) for i in identities}
    if len(dry) != 1 or len({i["model_id"] for i in identities}) != 1:
        raise ValueError("all runs must share one model and be all real or all dry runs")
    if any(i.get("benchmark") != "adversarial_release_test2" for i in identities):
        raise ValueError("not a Test-2 run")
    if not dry.pop():
        final_config_v2.verify(ROOT)
        if {i.get("final_config_sha256") for i in identities} != {
                final_config_v2.manifest_sha256(ROOT)}:
            raise ValueError("a run was not made under the current freeze manifest")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for run, identity in zip(args.runs, identities, strict=True):
        for level_dir in sorted(p for p in (run / "runs").iterdir() if p.is_dir()):
            config = identity["defense"]["name"] if identity.get("defense") else level_dir.name
            if config not in CONFIGS or config in seen:
                raise ValueError(f"{config}: not in the matrix or given twice")
            seen.add(config)
            folders = sorted(level_dir.glob("*/result.json"))
            if {p.parent.name for p in folders} != set(rows):
                raise ValueError(f"{config}: does not cover the 200 Test-2 fixtures")
            for path in folders:
                saved = json.loads(path.read_text())
                folder = path.parent
                trace = folder / "execution/trace_legacy.jsonl"
                if hashlib.sha256(trace.read_bytes()).hexdigest() != saved["trace_sha256"]:
                    raise ValueError(f"trace changed after checkpoint: {folder}")
                row = rows[saved["variant_id"]]
                score = score_execution(privates[row.family_id], folder / "execution",
                                        folder / "environment/database/university.db")
                records.append({"config": config, "variant_id": row.variant_id,
                                "branch": row.branch, "family_id": row.family_id,
                                "variant_type": row.variant_type, "score": score})
    report = summarize_test2(records) | {
        "scope": "DRY RUN with CPU stand-ins; not a result" if identities[0].get(
            "dry_run_dummy") else "Held-out Test-2 (single pre-registered run)",
        "model_id": identities[0]["model_id"], "executions": len(records),
        "run_identity_sha256": {str(run): hashlib.sha256(
            (run / "identity.json").read_bytes()).hexdigest() for run in args.runs}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    args.output.with_suffix(".records.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    for config, entry in report["configs"].items():
        side, util = entry["side_effect"].get("paired_asr", {}), entry["v1"].get(
            "benign_utility", {})
        print(config, "paired side-effect ASR", side.get("k"), "/", side.get("n"),
              "benign utility", util.get("k"), "/", util.get("n"),
              "model_error", entry["v1"]["model_error"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
