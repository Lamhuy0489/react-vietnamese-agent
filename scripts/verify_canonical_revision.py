#!/usr/bin/env python3
"""Verify the v2.2 wording/grouping revision with preserved v2.1 objectives."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from react_agent.authoring.canonical_revision import verify_revision

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    output, report_path = args.output.resolve(), args.report.resolve()
    if not output.is_relative_to(ROOT / "results"):
        raise ValueError("raw outputs must remain under ignored results/")
    if report_path.exists() or not any(
        report_path.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")
    ):
        raise ValueError("report must be fresh under results/ or experiments/manifests/")
    report = verify_revision(
        ROOT / "data/adversarial/candidates_v2_1",
        ROOT / "data/adversarial/candidates_v2_2",
        ROOT / "data/adversarial/candidate_review_v1",
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
    report["source_identity_note"] = "base commit plus exact hashes; may include new source files"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "valid": report["valid"],
                "replay_runs": report["replay_runs"],
                "review_units": report["group_audit"]["review_unit_count"],
                "canonical_approval": report["revision_checks"]["canonical_approval"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
