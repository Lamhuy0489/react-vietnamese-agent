#!/usr/bin/env python3
"""Fresh unified QA of active unsplit candidates; never accepts an incomplete phase."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from react_agent.authoring.candidate_qa import load_candidates
from react_agent.authoring.candidate_review import group_audit, verify_review
from react_agent.authoring.linked_batch import verify_linked
from react_agent.authoring.mechanism_batch import verify_batch
from react_agent.authoring.workbench_qa import file_hashes

ROOT = Path(__file__).resolve().parents[1]


def verify_pool(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("output must be fresh under results/")
    pilot = ROOT / "data/adversarial/candidates_v2_2"
    mechanism = ROOT / "data/adversarial/mechanism_batch_v1"
    linked = ROOT / "data/adversarial/linked_scope_v1"
    sidecars = ROOT / "data/adversarial/candidate_review_v1"
    clean = ROOT / "data/clean/v1_1/environment"
    candidates = [c for path in (pilot, mechanism, linked) for c in load_candidates(path)]
    for ids in (
        [c.public.task_id for c in candidates],
        [c.metadata.family_id for c in candidates],
        [c.overlay.source_id for c in candidates],
    ):
        if len(ids) != len(set(ids)):
            raise ValueError("cross-batch identity collision")
    before = {
        str(p.relative_to(ROOT)): file_hashes(p)
        for p in (pilot, mechanism, linked, sidecars, clean)
    }
    reports = {
        "pilot": verify_review(pilot, sidecars, clean, output / "pilot"),
        "mechanism": verify_batch(mechanism, pilot, clean, output / "mechanism"),
        "linked": verify_linked(linked, clean, output / "linked"),
    }
    if before != {p: file_hashes(ROOT / p) for p in before}:
        raise ValueError("inputs changed during unified QA")
    # These are actual metadata gates, not a count-based automatic approval.
    blockers = [
        "canonical semantic/pair review pending under owner workflow",
        "40/30 grouped split not assigned",
        "350 attack and 350 benign variants not generated/reviewed",
        "release mapping, hashes and Test seal not frozen",
    ]
    if len(candidates) != 70:
        blockers.insert(0, f"canonical pool has {len(candidates)} candidates; target is 70")
    return {
        "qa_valid": True,
        "phase3_accepted": False,
        "scope": "unsplit authoring only; not model evaluation or release acceptance",
        "candidate_count": len(candidates),
        "approved_family_count": 0,
        "replay_runs": sum(r["replay_runs"] for r in reports.values()),
        "safe_reference_runs": sum(
            c["score"]["safe_utility"] for r in reports.values() for c in r["checks"]
        ),
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "variants_generated": 0,
        "group_audit": group_audit(candidates),
        "acceptance_blockers": blockers,
        "input_sets_sha256": before,
        "batches": reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--require-acceptance",
        action="store_true",
        help="exit 2 when Phase 3 acceptance is pending, even if fixture QA passes",
    )
    args = parser.parse_args()
    report_path = args.report.resolve()
    if report_path.exists() or not any(
        report_path.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")
    ):
        raise ValueError("report must be fresh under results/ or experiments/manifests/")
    report = verify_pool(args.output)
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git required for source identity")
    report["base_git_commit"] = subprocess.check_output(  # noqa: S603 - fixed read-only arguments
        [git, "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    report["source_sha256"] = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__).resolve(), *sorted((ROOT / "src").rglob("*.py"))]
    }
    report["source_identity_note"] = (
        "base commit plus exact hashes; may include uncommitted additions"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "qa_valid",
                    "phase3_accepted",
                    "candidate_count",
                    "replay_runs",
                    "acceptance_blockers",
                )
            },
            ensure_ascii=False,
        )
    )
    return 2 if args.require_acceptance and not report["phase3_accepted"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
