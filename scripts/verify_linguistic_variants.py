#!/usr/bin/env python3
"""Execute linguistic reference parity QA without model inference or Test sealing."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from react_agent.authoring.linguistic_variants import verify_linguistic

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inputs", type=Path, default=ROOT / "data/adversarial/linguistic_variants_v1"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--require-acceptance", action="store_true")
    args = parser.parse_args()
    report_path = args.report.resolve()
    if report_path.exists() or not any(
        report_path.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")
    ):
        raise ValueError("report must be fresh under results/ or experiments/manifests/")
    report = verify_linguistic(ROOT, args.inputs, args.output)
    report["source_sha256"] = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [
            Path(__file__).resolve(),
            ROOT / "scripts/build_linguistic_variants.py",
            ROOT / "docs/benchmark/linguistic_variants_contract.md",
            *sorted((ROOT / "src").rglob("*.py")),
        ]
    }
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git required for source identity")
    report["base_git_commit"] = subprocess.check_output(  # noqa: S603
        [git, "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    report["source_identity_note"] = "base commit plus exact source hashes; may include additions"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "valid",
                    "linguistic_variants_accepted",
                    "variant_count",
                    "fresh_replay_runs",
                    "phase3_accepted",
                    "test_sealed",
                    "test_assigned_reference_runs",
                )
            }
        )
    )
    return 2 if args.require_acceptance and not report["phase3_accepted"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
