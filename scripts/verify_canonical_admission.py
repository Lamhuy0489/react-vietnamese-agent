#!/usr/bin/env python3
"""Validate rule revision and bound 48-candidate author-admission decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from react_agent.authoring.admission_review import (
    AdmissionRegister,
    evidence_checks,
    load_bound_previous,
    validate_admission,
)
from react_agent.authoring.mechanism_revision import verify_revision
from react_agent.authoring.workbench_qa import file_hashes

ROOT = Path(__file__).resolve().parents[1]


def verify(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("output must be fresh under results/")
    review_root = ROOT / "data/adversarial/admission_review_v1"
    before = file_hashes(review_root)
    register = AdmissionRegister.model_validate_json((review_root / "reviews.json").read_text())
    previous = load_bound_previous(ROOT, register)
    revision = verify_revision(
        ROOT / "data/adversarial/mechanism_batch_v1",
        ROOT / "data/adversarial/mechanism_batch_v2",
        ROOT / "data/adversarial/candidates_v2_2",
        ROOT / "data/clean/v1_1/environment",
        output,
    )
    checks = evidence_checks(previous, revision)
    admission = validate_admission(ROOT, register, checks)
    if before != file_hashes(review_root):
        raise ValueError("review changed during validation")
    return {
        **admission,
        "fresh_replay_runs": revision["fresh_replay_runs"],
        "fresh_standard_paths": 32,
        "fresh_counterexample_paths": 6,
        "reused_standard_paths": 160,
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "variants_generated": 0,
        "split": "unassigned",
        "revision": revision,
        "previous_evidence": {
            "path": register.previous_receipt,
            "sha256": register.previous_receipt_sha256,
        },
        "review_sha256": before,
        "input_sha256": register.input_sha256,
        "evidence_identity": [
            {k: c[k] for k in ("task_id", "branch", "fixture", "trace_sha256", "observable_sha256")}
            for c in checks
        ],
        "acceptance_blockers": [
            "46 retained representatives; 24 further retained scenarios needed for 70",
            "whole-pool final semantic admission and grouped 40/30 split pending",
            "350 attack and 350 benign variants not generated/reviewed",
            "release mapping and Test seal not frozen",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--require-acceptance", action="store_true")
    args = parser.parse_args()
    path = args.report.resolve()
    if path.exists() or not any(
        path.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")
    ):
        raise ValueError("report must be fresh under results/ or experiments/manifests/")
    report = verify(args.output)
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
                    "reused_standard_paths",
                )
            }
        )
    )
    return 2 if args.require_acceptance and not report["phase3_accepted"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
