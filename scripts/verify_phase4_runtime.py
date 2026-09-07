#!/usr/bin/env python3
"""Run fresh CPU paired A0/foundation parity on smoke and Dev only."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from react_agent.foundation.runtime_qa import run_suite

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    if report.exists() or not any(
        report.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")
    ):
        raise ValueError("report must be fresh under results or manifests")
    result = run_suite(ROOT, args.output)
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git required for source identity")
    result["source_git_commit"] = subprocess.check_output(  # noqa: S603 - fixed read-only args
        [git, "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    paths = [
        *sorted((ROOT / "src").rglob("*.py")),
        Path(__file__).resolve(),
        ROOT / "docs/architecture/phase4_runtime_contract.md",
    ]
    result["source_sha256"] = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
    }
    output = args.output.resolve()
    result["raw_output"] = output.relative_to(ROOT).as_posix()
    result["raw_artifact_sha256"] = {
        p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(output.rglob("*.json*"))
        if not any(part.endswith("_env") for part in p.parts)
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
                    "paired_conditions",
                    "fresh_replay_runs",
                    "test_payloads_parsed",
                )
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
