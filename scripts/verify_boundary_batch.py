#!/usr/bin/env python3
"""Verify eight paired boundary cases, not final Phase 3 acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from react_agent.authoring.boundary_batch import verify_boundaries

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--require-acceptance", action="store_true")
    args = parser.parse_args()
    output, path = args.output.resolve(), args.report.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("output must be fresh under results/")
    if path.exists() or not any(
        path.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")
    ):
        raise ValueError("report must be fresh under results/ or experiments/manifests/")
    report = verify_boundaries(
        ROOT,
        ROOT / "data/adversarial/boundary_batch_v1",
        ROOT / "data/clean/v1_1/environment",
        output,
    )
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git required for source identity")
    report["base_git_commit"] = subprocess.check_output(  # noqa: S603 - fixed read-only args
        [git, "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    report["source_sha256"] = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__).resolve(), *sorted((ROOT / "src").rglob("*.py"))]
    }
    report["source_identity_note"] = "base commit plus exact source hashes; may include additions"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "valid",
                    "phase3_accepted",
                    "working_candidates",
                    "retained_representatives",
                    "remaining_to_target",
                    "fresh_replay_runs",
                )
            }
        )
    )
    return 2 if args.require_acceptance and not report["phase3_accepted"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
