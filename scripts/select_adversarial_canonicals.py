#!/usr/bin/env python3
"""Select reviewed canonicals and split complete groups; never seal incomplete Test."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from react_agent.authoring.canonical_selection import select_canonicals

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--check-existing", action="store_true")
    parser.add_argument("--require-acceptance", action="store_true")
    args = parser.parse_args()
    path = args.report.resolve()
    if not any(path.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")):
        raise ValueError("report must be under results/ or experiments/manifests/")
    if not args.check_existing and path.exists():
        raise ValueError("report must be fresh; existing selection cannot be overwritten")
    report = select_canonicals(ROOT, ROOT / "data/adversarial/canonical_selection_v1/review.json")
    report["source_sha256"] = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [
            Path(__file__).resolve(),
            ROOT / "src/react_agent/authoring/canonical_selection.py",
            ROOT / "docs/benchmark/canonical_selection_contract.md",
        ]
    }
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git required for source identity")
    report["base_git_commit"] = subprocess.check_output(  # noqa: S603 - fixed read-only args
        [git, "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    report["source_identity_note"] = (
        "base commit plus exact new source and inherited evidence hashes"
    )
    if args.check_existing:
        existing = json.loads(path.read_text())
        report["base_git_commit"] = existing["base_git_commit"]
        if existing != report:
            raise ValueError("selection, split, evidence or source changed")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "valid",
                    "canonical_authoring_admitted",
                    "canonical_split_valid",
                    "admitted_canonicals",
                    "group_count",
                    "phase3_accepted",
                    "test_sealed",
                )
            }
        )
    )
    return 2 if args.require_acceptance and not report["phase3_accepted"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
