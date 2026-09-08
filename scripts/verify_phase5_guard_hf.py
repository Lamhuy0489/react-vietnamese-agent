#!/usr/bin/env python3
"""Freeze synthetic CPU adapter checks and preserve prior source/Test seals."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from react_agent.foundation.dev_validation import prerequisites

ROOT = Path(__file__).resolve().parents[1]
NEW_FILES = (
    "src/react_agent/llm/guard_snapshot_v1.py",
    "src/react_agent/llm/guard_hf_v1.py",
    "tests/unit/test_guard_hf_v1.py",
    "scripts/verify_phase5_guard_hf.py",
    "docs/architecture/phase5_guard_hf_contract.md",
    "knowledge/guard_model_preflight_evidence.md",
)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def sources() -> dict[str, str]:
    paths = {p.relative_to(ROOT).as_posix() for p in (ROOT / "src").rglob("*.py")}
    paths.update(NEW_FILES)
    return {p: digest(ROOT / p) for p in sorted(paths)}


def prior_sources() -> dict[str, Any]:
    manifests = ROOT / "experiments/manifests"
    latest = "phase5_warm_guard_v1_validation01.json"
    current = json.loads((manifests / latest).read_text())
    expected = current["prior_evidence"]["receipt_sha256"] | {latest: digest(manifests / latest)}
    entries = 0
    for name, expected_digest in expected.items():
        path = manifests / name
        if digest(path) != expected_digest:
            raise ValueError("prior receipt changed")
        receipt = json.loads(path.read_text())
        if receipt["valid"] is not True:
            raise ValueError("invalid prior receipt")
        for relative, sha256 in receipt["source_sha256"].items():
            if digest(ROOT / relative) != sha256:
                raise ValueError("prior source changed: " + relative)
            entries += 1
    return {"receipt_sha256": expected, "source_hash_entries_checked": entries}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
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
    commit = subprocess.check_output([git, "rev-parse", "HEAD"], text=True, cwd=ROOT).strip()  # noqa: S603
    clean = not subprocess.check_output([git, "status", "--porcelain"], cwd=ROOT)  # noqa: S603
    hashes, prior, seals = sources(), prior_sources(), prerequisites(ROOT)
    reference = json.loads(args.reference.read_text()) if args.reference else None
    if reference is not None and (
        reference["valid"] is not True
        or reference["source_sha256"] != hashes
        or reference["prior_evidence"] != prior
        or reference["prerequisites"] != seals
    ):
        raise ValueError("preflight source/evidence/seal mismatch")
    if report.is_relative_to(ROOT / "experiments/manifests") and (not clean or reference is None):
        raise ValueError("selected receipt requires clean source and matching preflight")
    output.mkdir(parents=True)
    commands = {
        "setup": [sys.executable, "scripts/verify_setup.py"],
        "ruff": [str(ROOT / ".venv/bin/ruff"), "check", "."],
        "mypy": [str(ROOT / ".venv/bin/mypy"), "src", "scripts"],
        "adapter_tests": [sys.executable, "-m", "pytest", "tests/unit/test_guard_hf_v1.py", "-q"],
        "pytest": [sys.executable, "-m", "pytest"],
        "knowledge": [sys.executable, "scripts/validate_knowledge.py"],
    }
    quality = {}
    for name, command in commands.items():
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603
        path = output / (name + ".log")
        path.write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode:
            raise ValueError("quality check failed: " + str(path))
        quality[name] = {"returncode": 0, "log_sha256": digest(path)}
        print(name + ": pass", flush=True)
    if sources() != hashes or prior_sources() != prior or prerequisites(ROOT) != seals:
        raise ValueError("source/evidence/seal changed during checks")
    result = {
        "schema_version": "phase5_guard_hf_cpu_qa_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_git_commit": commit,
        "source_worktree_clean": clean,
        "source_sha256": hashes,
        "prior_evidence": prior,
        "prerequisites": seals,
        "preflight_sha256": digest(args.reference) if args.reference else None,
        "preflight_matches": reference is not None,
        "quality": quality,
        "raw_output": output.relative_to(ROOT).as_posix(),
        "raw_sha256": {p.name: digest(p) for p in sorted(output.iterdir())},
        "real_model_runs": 0,
        "benchmark_dev_runs": 0,
        "test_payloads_parsed": 0,
        "scope": "Fake tensor/tokenizer CPU adapter checks only; no CUDA/HF inference proof",
        "remaining": [
            "Independently authenticated snapshot acquisition and exact offline bundle preflight",
            "Real cache-bypassed A-B-A/fresh-A probe, warm worker/GPU cancellation",
            "Versioned agent placement and concurrent residency/context stress",
            "Grouped Dev guard quality, A4 scope, broader final entitlements and Phase 5 freeze",
        ],
    }
    with report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"valid": True, "phase5_accepted": False, "real_model_runs": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
