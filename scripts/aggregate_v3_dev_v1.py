#!/usr/bin/env python3
"""Aggregate Dev v3 evaluations into one table (Study 2, Dev round 1).

Reads ``results/rebuild_b/v3_dev_<CONFIG>_<model>_eval.json`` (written by
``evaluate_v3_v1.py``) and, per run, counts model errors whose trace records
``OUTPUT_TRUNCATED`` (output longer than the pinned max_new_tokens). Prints a
Markdown table and writes JSON; aggregates only, never fixture text::

    .venv/bin/python scripts/aggregate_v3_dev_v1.py --output results/rebuild_b/v3_dev_round1.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/rebuild_b"
MODELS = ("gemma4_12b", "llama31_8b", "qwen35_9b")
CONFIGS = ("A0", "P1", "P2", "G1", "MEL", "PRG", "R1", "D2", "D2P1", "D2P2")
MECHANISMS = ("M1", "M2", "M3", "M4", "M5", "M6")


def truncated(run: Path) -> int:
    count = 0
    for result in run.glob("runs/*/*/result.json"):
        if json.loads(result.read_text())["status"] != "model_error":
            continue
        trace = result.parent / "execution/trace_legacy.jsonl"
        count += "OUTPUT_TRUNCATED" in trace.read_text(encoding="utf-8")
    return count


def row(model: str, config: str) -> dict[str, Any] | None:
    run = RESULTS / f"v3_dev_{config}_{model}"
    path = run.with_name(run.name + "_eval.json")
    if not path.exists():
        return None
    report = json.loads(path.read_text(encoding="utf-8"))
    (level, s), = report["summary"].items()
    errors = sum(v for k, v in s["statuses"].items() if k.endswith(":model_error"))
    denied = sum(v for k, v in s["statuses"].items()
                 if k.startswith("benign_auth:") and not k.endswith(":completed"))
    mech = {m: f"{v['harmful']}/{v['families']}" for m, v in s["per_mechanism"].items()}
    return {"model": model, "config": config, "level": level,
            "executions": report["executions"],
            "harmful_families": s["attack_harmful_families"],
            "harmful_fixtures": s["attack_harmful_fixtures"],
            "per_mechanism": {m: mech.get(m, "-") for m in MECHANISMS},
            "benign_plain_utility": s["benign_plain_utility"],
            "benign_plain_harmful": s["benign_plain_harmful"],
            "benign_auth_utility": s["benign_auth_utility"],
            "benign_auth_not_completed": denied,
            "model_errors": errors, "output_truncated": truncated(run)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    rows = [r for m in MODELS for c in CONFIGS if (r := row(m, c))]
    head = ["model", "config", "harm fam", "harm fix", *MECHANISMS, "plain util",
            "plain harm", "auth util", "auth !done", "model_err", "truncated"]
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for r in rows:
        cells = [r["model"], r["config"], r["harmful_families"], r["harmful_fixtures"],
                 *r["per_mechanism"].values(), r["benign_plain_utility"],
                 r["benign_plain_harmful"], r["benign_auth_utility"],
                 r["benign_auth_not_completed"], r["model_errors"], r["output_truncated"]]
        print("| " + " | ".join(str(c) for c in cells) + " |")
    if args.output:
        args.output.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
        print(f"WROTE {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
