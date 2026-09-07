#!/usr/bin/env python3
"""Hash-bound synthetic A0–A6 runtime integration QA; no benchmark inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.dev_validation import prerequisites
from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.a6_qa import all_cases, cases

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    paths = [
        *sorted((ROOT / "src").rglob("*.py")),
        *sorted((ROOT / "configs/security_v1").glob("*.yaml")),
        ROOT / "tests/integration/test_phase5_a6_runtime.py",
        Path(__file__).resolve(),
        ROOT / "docs/architecture/phase5_a6_runtime_contract.md",
    ]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def prior_evidence() -> dict[str, Any]:
    receipts = {}
    count = 0
    for name in (
        "phase4_closure_v1_validation01.json",
        "phase5_components_v1_validation01.json",
        "phase5_runtime_v1_validation01.json",
        "phase5_a2_v2_validation01.json",
        "phase5_session_v1_validation01.json",
        "phase5_value_origin_v1_validation01.json",
        "phase5_value_gates_v1_validation02.json",
    ):
        path = ROOT / "experiments/manifests" / name
        receipt = json.loads(path.read_text())
        if receipt["valid"] is not True:
            raise ValueError("invalid prior evidence")
        for relative, expected in receipt["source_sha256"].items():
            if digest(ROOT / relative) != expected:
                raise ValueError("frozen source changed: " + relative)
            count += 1
        receipts[name] = digest(path)
    return {"receipt_sha256": receipts, "source_hash_entries_checked": count}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    output, report = args.output.resolve(), args.report.resolve()
    if output.exists() or report.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("fresh results output/report required")
    if not any(report.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")):
        raise ValueError("report must be under results/manifests")
    git = shutil.which("git")
    if git is None:
        raise ValueError("Git required")
    commit = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603
    clean = not subprocess.check_output([git, "status", "--porcelain"], cwd=ROOT, text=True)  # noqa: S603
    hashes = source_hashes()
    reference = json.loads(args.reference.read_text()) if args.reference else None
    if reference is not None and (not reference["valid"] or reference["source_sha256"] != hashes):
        raise ValueError("reference source mismatch")
    if report.is_relative_to(ROOT / "experiments/manifests") and (not clean or reference is None):
        raise ValueError("selected evidence requires clean source and matching preflight")
    before, prior = prerequisites(ROOT), prior_evidence()
    smoke = {
        p.relative_to(ROOT).as_posix(): digest(p)
        for p in sorted((ROOT / "data/smoke").rglob("*"))
        if p.is_file()
    }
    output.mkdir(parents=True)
    checks = all_cases(ROOT, output / "cases")
    if len(checks) != len(cases()) + 12 or any(not c["valid"] for c in checks):
        raise ValueError("complete synthetic runtime matrix and parity required")
    metadata = [json.loads(p.read_text()) for p in sorted(output.rglob("run_metadata.json"))]
    stable = text_hash(canonical_json(checks))
    if reference is not None and reference["stable_summary_sha256"] != stable:
        raise ValueError("preflight deterministic summary mismatch")
    quality = {}
    commands = {
        "setup": [sys.executable, "scripts/verify_setup.py"],
        "ruff": [str(ROOT / ".venv/bin/ruff"), "check", "."],
        "mypy": [str(ROOT / ".venv/bin/mypy"), "src", "scripts"],
        "pytest": [sys.executable, "-m", "pytest"],
        "knowledge": [sys.executable, "scripts/validate_knowledge.py"],
    }
    for name, command in commands.items():
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603
        path = output / (name + ".log")
        path.write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode:
            raise ValueError("quality check failed: " + str(path))
        quality[name] = {"returncode": 0, "log_sha256": digest(path)}
    if source_hashes() != hashes or prerequisites(ROOT) != before or prior_evidence() != prior:
        raise ValueError("source/input changed during validation")
    if any(digest(ROOT / p) != h for p, h in smoke.items()):
        raise ValueError("smoke changed during validation")
    result = {
        "schema_version": "phase5_a6_runtime_qa_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_git_commit": commit,
        "source_worktree_clean": clean,
        "source_sha256": hashes,
        "prior_evidence": prior,
        "prerequisites": before,
        "smoke_input_sha256": smoke,
        "a6_runtime_enabled": True,
        "synthetic_runtime_conditions": len(cases()),
        "prior_level_parity_pairs": 12,
        "mock_broker_calls": sum(m["control"]["tool_call_count"] for m in metadata),
        "fresh_replay_runs": len(metadata),
        "guard_classifications": sum(m["guard_classification_count"] for m in metadata),
        "checks": checks,
        "stable_summary_sha256": stable,
        "preflight_sha256": digest(args.reference) if args.reference else None,
        "preflight_matches": reference is not None,
        "quality": quality,
        "raw_output": output.relative_to(ROOT).as_posix(),
        "raw_sha256": {
            p.relative_to(output).as_posix(): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file() and not any(part.endswith("_env") for part in p.parts)
        },
        "real_model_runs": 0,
        "benchmark_dev_runs": 0,
        "test_payloads_parsed": 0,
        "scope": "Bounded A6 runtime integration; not Phase 5 acceptance or model metrics",
        "remaining": [
            "Production guard model/revision and efficient GPU worker validation",
            "General private-record final entitlement policy and broader origin coverage",
            "A4 general processing-scope controls beyond bounded destination anchors",
            "grouped Dev validation and freeze",
        ],
    }
    with report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("valid", "phase5_accepted", "fresh_replay_runs")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
