#!/usr/bin/env python3
"""Reproducible Phase 4 Dev/overhead closure, with separate measurement workers."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from react_agent.foundation.closure_qa import run_closure_qa
from react_agent.foundation.dev_validation import prerequisites
from react_agent.foundation.overhead_study import measure_worker, run_study

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ("phase4_primitives_v1_validation01.json", "phase4_runtime_v1_validation01.json")


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    paths = [
        *sorted((ROOT / "src").rglob("*.py")),
        *sorted((ROOT / "tests").rglob("*.py")),
        Path(__file__).resolve(),
        ROOT / "docs/architecture/phase4_closure_protocol.md",
        ROOT / "docs/architecture/phase4_design.md",
        ROOT / "configs/normalization/profiles_v1.yaml",
    ]
    return {p.relative_to(ROOT).as_posix(): hash_file(p) for p in paths}


def audit_prior(root: Path) -> dict[str, Any]:
    receipts = {}
    checked = 0
    for name in PRIOR:
        path = root / "experiments/manifests" / name
        receipt = json.loads(path.read_text())
        if receipt.get("valid") is not True:
            raise ValueError("invalid prior Phase 4 evidence")
        for relative, digest in receipt["source_sha256"].items():
            if hash_file(root / relative) != digest:
                raise ValueError("frozen foundation source changed: " + relative)
            checked += 1
        if "raw_output" in receipt:
            for relative, digest in receipt["raw_artifact_sha256"].items():
                if hash_file(root / receipt["raw_output"] / relative) != digest:
                    raise ValueError("prior raw evidence changed")
                checked += 1
        receipts[name] = hash_file(path)
    return {"receipt_sha256": receipts, "verified_hash_entries": checked}


def quality_checks(output: Path) -> dict[str, Any]:
    commands = {
        "setup": [sys.executable, "scripts/verify_setup.py"],
        "ruff": [str(ROOT / ".venv/bin/ruff"), "check", "."],
        "mypy": [str(ROOT / ".venv/bin/mypy"), "src", "scripts"],
        "pytest": [sys.executable, "-m", "pytest"],
        "knowledge": [sys.executable, "scripts/validate_knowledge.py"],
    }
    directory = output / "quality"
    directory.mkdir()
    results = {}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603
        log = directory / (name + ".log")
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        results[name] = {"returncode": result.returncode, "log_sha256": hash_file(log)}
        if result.returncode:
            raise ValueError("quality check failed; see " + str(log))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--worker", choices=("legacy", "foundation"))
    parser.add_argument("--memory", action="store_true")
    parser.add_argument("--stress", action="store_true")
    parser.add_argument("--qa-only", action="store_true")
    parser.add_argument("--quality", action="store_true")
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("output must be fresh under results")
    if args.worker:
        worker = measure_worker(ROOT, output, args.worker, memory=args.memory, stress=args.stress)
        (output / "worker.json").write_text(json.dumps(worker, ensure_ascii=False, indent=2) + "\n")
        return 0
    if args.report is None:
        raise ValueError("report required")
    report = args.report.resolve()
    if report.exists() or not any(
        report.is_relative_to(ROOT / p) for p in ("results", "experiments/manifests")
    ):
        raise ValueError("report must be fresh under results/manifests")
    before = prerequisites(ROOT)
    prior = audit_prior(ROOT)
    frozen_source = source_hashes()
    git = shutil.which("git")
    if git is None:
        raise ValueError("Git required")
    source = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603
    dirty = bool(subprocess.check_output([git, "status", "--porcelain"], cwd=ROOT, text=True))  # noqa: S603
    reference = None
    if args.reference:
        reference = json.loads(args.reference.read_text())
        if not reference["valid"] or reference["source_sha256"] != frozen_source:
            raise ValueError("reference must be valid with exactly matching source hashes")
    if report.is_relative_to(ROOT / "experiments/manifests") and (dirty or reference is None):
        raise ValueError("selected receipt requires clean committed source and matching preflight")
    output.mkdir(parents=True)
    qa = run_closure_qa(ROOT, output / "dev")
    study = None if args.qa_only else run_study(ROOT, output / "overhead")
    quality = quality_checks(output) if args.quality else None
    if prerequisites(ROOT) != before or audit_prior(ROOT) != prior:
        raise ValueError("frozen inputs/evidence changed during closure")
    if source_hashes() != frozen_source:
        raise ValueError("source changed during closure; preserve run but do not accept")
    reference_match = (
        reference is not None
        and reference["qa"]["stable_summary_sha256"] == qa["stable_summary_sha256"]
    )
    if reference is not None and not reference_match:
        raise ValueError("Dev stable summary differs from preflight")
    valid = qa["valid"] and (study is None or study["valid"])
    result = {
        "schema_version": "phase4_closure_v1",
        "valid": valid,
        "phase4_accepted": bool(
            valid and study is not None and quality is not None and reference_match and not dirty
        ),
        "source_git_commit": source,
        "source_worktree_clean": not dirty,
        "source_sha256": frozen_source,
        "preflight_receipt_sha256": hash_file(args.reference) if args.reference else None,
        "preflight_stable_summary_matches": reference_match,
        "prior_evidence": prior,
        "qa": qa,
        "overhead": study,
        "quality": quality,
        "raw_output": output.relative_to(ROOT).as_posix(),
        "real_model_runs": 0,
        "test_payloads_parsed": 0,
        "limitations": [
            "owner-waived self-review, not independent review",
            "conservative collection/context lineage, not token/row-level",
            "scripted Dev plumbing, not utility/ASR or model inference",
            "local Replay overhead; no GPU/model generalization",
        ],
    }
    result["raw_artifact_sha256"] = {
        p.relative_to(output).as_posix(): hash_file(p)
        for p in sorted(output.rglob("*"))
        if p.is_file() and not any(part.endswith("_env") for part in p.parts)
    }
    with report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in ("valid", "phase4_accepted", "real_model_runs", "test_payloads_parsed")
            }
        )
    )
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
