#!/usr/bin/env python3
"""Fresh forty-candidate authoring QA, preserving the earlier verifier and inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from verify_phase3_pool import verify_pool

from react_agent.authoring.transaction_batch import verify_transactions

ROOT = Path(__file__).resolve().parents[1]


def verify_expanded_pool(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("output must be fresh under results/")
    old = verify_pool(output / "prior_pool")
    new = verify_transactions(
        ROOT / "data/adversarial/transaction_batch_v1",
        [
            ROOT / "data/adversarial" / name
            for name in (
                "candidates_v2_2",
                "mechanism_batch_v1",
                "linked_scope_v1",
            )
        ],
        ROOT / "data/clean/v1_1/environment",
        output / "transactions",
    )
    count = new["combined_candidates"]
    return {
        "qa_valid": True,
        "phase3_accepted": False,
        "scope": "unsplit canonical authoring; no model or held-out evaluation",
        "candidate_count": count,
        "approved_family_count": 0,
        "replay_runs": old["replay_runs"] + new["replay_runs"],
        "safe_reference_runs": old["safe_reference_runs"]
        + sum(c["score"]["safe_utility"] for c in new["checks"]),
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "variants_generated": 0,
        "group_audit": new["group_audit"],
        "acceptance_blockers": [
            f"canonical pool has {count} candidates; target is 70",
            "per-family release decisions pending after author self-review",
            "40/30 grouped split not assigned",
            "350 attack and 350 benign variants not generated/reviewed",
            "release mapping, hashes and Test seal not frozen",
        ],
        "prior_pool": old,
        "transaction_batch": new,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--require-acceptance", action="store_true")
    args = parser.parse_args()
    report_path = args.report.resolve()
    if report_path.exists() or not any(
        report_path.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")
    ):
        raise ValueError("report must be fresh under results/ or experiments/manifests/")
    report = verify_expanded_pool(args.output)
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git required for source identity")
    report["base_git_commit"] = subprocess.check_output(  # noqa: S603 - fixed read-only args
        [git, "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    sources = [Path(__file__).resolve(), ROOT / "scripts/verify_phase3_pool.py"]
    sources.extend(sorted((ROOT / "src").rglob("*.py")))
    report["source_sha256"] = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources
    }
    report["author_review_sha256"] = {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
        for p in (
            "docs/benchmark/pool_author_review_v1.md",
            "data/adversarial/transaction_batch_v1/README.md",
        )
    }
    report["source_identity_note"] = "base commit plus exact hashes; may include new additions"
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
                    "safe_reference_runs",
                )
            }
        )
    )
    return 2 if args.require_acceptance and not report["phase3_accepted"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
