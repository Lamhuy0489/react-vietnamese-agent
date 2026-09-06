#!/usr/bin/env python3
"""Run local Phase 3 executable fixture QA with fresh outputs; never invoke an LLM."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from react_agent.authoring.workbench_qa import run_workbench

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / "results"):
        raise ValueError("raw QA output must be under ignored results/")
    if args.report.exists() or args.report.resolve().is_relative_to(ROOT / "data"):
        raise ValueError("report must be fresh and outside data inputs")
    report = run_workbench(
        ROOT / "data/adversarial/workbench_v2", ROOT / "data/clean/v1_1/environment", args.output
    )
    report["verifier_sha256"] = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [
            Path(__file__).resolve(),
            ROOT / "src/react_agent/schemas/adversarial_workbench.py",
            *(
                ROOT / f"src/react_agent/authoring/{name}.py"
                for name in ("overlays", "fixture_oracle", "workbench_qa")
            ),
        ]
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "valid",
                    "scope",
                    "canonical_pairs",
                    "replay_runs",
                    "real_model_runs",
                    "review_status",
                )
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
