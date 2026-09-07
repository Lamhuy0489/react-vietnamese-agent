#!/usr/bin/env python3
"""Validate versioned Phase 4 primitives on Dev only; never declare whole-phase acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path

from react_agent.foundation.dev_validation import validate_dev

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    if report.exists() or not any(
        report.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")
    ):
        raise ValueError("report must be fresh under results or experiments/manifests")
    result = validate_dev(ROOT)
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git source identity required")
    result["source_git_commit"] = subprocess.check_output(  # noqa: S603 - fixed read-only Git args
        [git, "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    result["python_version"] = platform.python_version()
    paths = [
        *sorted((ROOT / "src/react_agent/foundation").glob("*.py")),
        Path(__file__).resolve(),
        ROOT / "docs/architecture/phase4_foundation_contract.md",
    ]
    result["source_sha256"] = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "valid",
                    "phase4_accepted",
                    "clean_dev_instructions",
                    "adversarial_dev_payloads",
                    "profile_checks",
                    "test_payloads_parsed_by_this_validator",
                )
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
