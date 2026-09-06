#!/usr/bin/env python3
"""Verify the expanded canonical candidates with Replay only; preserve prior inputs/results."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from react_agent.authoring.candidate_qa import verify_candidates

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / "results"):
        raise ValueError("raw outputs must stay under ignored results/")
    if args.report.exists() or args.report.resolve().is_relative_to(ROOT / "data"):
        raise ValueError("report must be fresh and outside dataset inputs")
    report = verify_candidates(
        ROOT / "data/adversarial/candidates_v2_1", ROOT / "data/clean/v1_1/environment", args.output
    )
    report["source_sha256"] = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__).resolve(), *sorted((ROOT / "src").rglob("*.py"))]
    }
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required for source identity")
    report["base_git_commit"] = subprocess.check_output(  # noqa: S603 - fixed read-only args
        [git, "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    report["source_identity_note"] = (
        "base commit plus exact source hashes; may include uncommitted authoring additions"
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "valid",
                    "canonical_candidates",
                    "replay_runs",
                    "real_model_runs",
                    "review_status",
                )
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
