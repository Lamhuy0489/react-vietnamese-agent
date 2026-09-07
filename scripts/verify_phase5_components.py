#!/usr/bin/env python3
"""Audit frozen inputs and run synthetic Phase 5 component tests; no benchmark tuning."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from react_agent.foundation.dev_validation import prerequisites
from react_agent.security_v1.contracts import SecurityConfig
from react_agent.security_v1.guard import PROMPT

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    output, report = args.output.resolve(), args.report.resolve()
    if output.exists() or report.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("fresh results output and report required")
    if not any(report.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")):
        raise ValueError("report must be under results/manifests")
    git = shutil.which("git")
    if git is None:
        raise ValueError("Git required")
    commit = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603
    clean = not subprocess.check_output([git, "status", "--porcelain"], cwd=ROOT, text=True)  # noqa: S603
    if report.is_relative_to(ROOT / "experiments/manifests") and not clean:
        raise ValueError("selected evidence requires committed clean source")
    before = prerequisites(ROOT)
    old_path = ROOT / "experiments/manifests/phase4_closure_v1_validation01.json"
    old = json.loads(old_path.read_text())
    for name, expected in old["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("frozen Phase 4 source changed: " + name)
    paths = [
        *sorted((ROOT / "src").rglob("*.py")),
        *sorted((ROOT / "configs/security_v1").glob("*.yaml")),
        ROOT / "tests/integration/test_phase5_components.py",
        Path(__file__).resolve(),
        ROOT / "docs/architecture/phase5_policy_contract.md",
    ]
    hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    configs = [
        SecurityConfig.model_validate(yaml.safe_load(p.read_text()))
        for p in sorted((ROOT / "configs/security_v1").glob("*.yaml"))
    ]
    if [c.level for c in configs] != [f"A{i}" for i in range(7)]:
        raise ValueError("exactly seven security configs required")
    output.mkdir(parents=True)
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/integration/test_phase5_components.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )  # noqa: S603
    log = output / "pytest.log"
    log.write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode or prerequisites(ROOT) != before:
        raise ValueError("component tests failed or frozen data changed")
    if any(digest(ROOT / p) != h for p, h in hashes.items()):
        raise ValueError("source changed while validating")
    match = re.search(r"(\d+) passed", run.stdout)
    if match is None:
        raise ValueError("missing test completion evidence")
    result = {
        "schema_version": "phase5_components_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_git_commit": commit,
        "source_worktree_clean": clean,
        "source_sha256": hashes,
        "prior_phase4_receipt_sha256": digest(old_path),
        "prior_source_hashes_checked": len(old["source_sha256"]),
        "prerequisites": before,
        "micro_tests_passed": int(match[1]),
        "security_config_sha256": {c.level: c.identity for c in configs},
        "guard_prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
        "raw_output": output.relative_to(ROOT).as_posix(),
        "raw_sha256": {"pytest.log": digest(log)},
        "real_guard_model_runs": 0,
        "benchmark_dev_runs": 0,
        "test_payloads_parsed": 0,
        "scope": "synthetic A0/A1 Broker adapter and model-guard interface tests only",
        "remaining": [
            "shared ReAct runtime integration",
            "A2 real model identity and bounded inference",
            "A3-A6 policy enforcement",
            "grouped Dev tune/validation and phase freeze",
        ],
    }
    with report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("valid", "phase5_accepted", "micro_tests_passed")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
