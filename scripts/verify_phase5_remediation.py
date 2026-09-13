#!/usr/bin/env python3
"""Fresh, exclusive Phase 5 repair QA with raw-file audits, not flag trust.

No model inference or held-out payload parsing. Historical corrupt receipts
are reported separately and never promoted to valid evidence by this run.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FOCUSED = [
    "tests/unit/test_phase5_remediation_v2.py",
    "tests/integration/test_phase5_runtime_v7.py",
    "tests/unit/test_phase5_receipt_audit.py",
]
HISTORICAL = [
    "phase5_final_entitlements_v1_validation01.json",
    "phase5_runtime_v6_entitlement_v1_validation01.json",
    "phase5_processing_scope_v1_validation01.json",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contained(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("artifact path escapes repository")
    return resolved


def audit_receipt(root: Path, path: Path) -> dict[str, Any]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    raw_root = contained(root, root / receipt["raw_output"])
    mismatches: list[dict[str, str]] = []
    checked = 0
    for group, base, mapping in (
        ("source", root, receipt["source_sha256"]),
        ("raw", raw_root, receipt["raw_sha256"]),
    ):
        for relative, expected in mapping.items():
            target = contained(base, base / relative)
            actual = digest(target) if target.is_file() else "MISSING"
            checked += 1
            if actual != expected:
                mismatches.append(
                    {
                        "group": group,
                        "path": relative,
                        "expected_sha256": expected,
                        "actual_sha256": actual,
                    }
                )
    return {
        "receipt": path.name,
        "receipt_sha256": digest(path),
        "checked": checked,
        "valid": bool(checked) and not mismatches,
        "mismatches": mismatches,
    }


def tracked_data_hashes() -> dict[str, str]:
    # Enumerate paths and hash bytes only; no payload/ground-truth parser.
    listing = subprocess.check_output(  # noqa: S603 - resolved git, fixed read-only arguments
        [executable("git"), "ls-files", "-z", "data"], cwd=ROOT
    )
    return {name: digest(ROOT / name) for name in listing.decode().split("\0") if name}


def executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise ValueError("required executable unavailable: " + name)
    return path


def source_hashes() -> dict[str, str]:
    paths = [ROOT / "pyproject.toml", ROOT / "docs/architecture/phase5_remediation_v2_contract.md"]
    for directory in ("src", "scripts", "tests"):
        paths.extend((ROOT / directory).rglob("*.py"))
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(paths)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--focused-only", action="store_true")
    args = parser.parse_args()
    output = contained(ROOT / "results", args.output)
    receipt_path = contained(ROOT / "experiments/manifests", args.receipt) if args.receipt else None
    if output.exists() or (receipt_path is not None and receipt_path.exists()):
        raise ValueError("fresh output and receipt identity required; never reuse a run")
    source = source_hashes()
    frozen = tracked_data_hashes()
    prior = [audit_receipt(ROOT, ROOT / "experiments/manifests" / name) for name in HISTORICAL]
    output.mkdir(parents=True, exist_ok=False)
    revision = subprocess.check_output(  # noqa: S603 - resolved git, fixed read-only arguments
        [executable("git"), "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    dirty = bool(
        subprocess.check_output(  # noqa: S603 - resolved git, fixed read-only arguments
            [executable("git"), "status", "--porcelain"], cwd=ROOT
        )
    )
    commands = {
        "setup": [sys.executable, "scripts/verify_setup.py"],
        "ruff": [sys.executable, "-m", "ruff", "check", "."],
        "mypy": [sys.executable, "-m", "mypy", "src", "scripts"],
        "knowledge": [executable("make"), "knowledge-check"],
        "focused": [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *FOCUSED,
            "--basetemp",
            str(output / "focused_cases"),
            "--junitxml",
            str(output / "focused.xml"),
        ],
    }
    if not args.focused_only:
        commands["pytest"] = [
            sys.executable,
            "-m",
            "pytest",
            "--junitxml",
            str(output / "pytest.xml"),
        ]
    quality = {}
    for name, command in commands.items():
        print("START " + name, flush=True)
        started = perf_counter()
        log = output / (name + ".log")
        with log.open("x", encoding="utf-8") as stream:
            result = subprocess.run(  # noqa: S603 - fixed local QA argument vectors, no shell
                command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False
            )
        quality[name] = {
            "command": command,
            "returncode": result.returncode,
            "seconds": perf_counter() - started,
            "log_sha256": digest(log),
        }
        print(f"DONE {name}: returncode={result.returncode}", flush=True)
    source_unchanged = source_hashes() == source
    frozen_unchanged = tracked_data_hashes() == frozen
    raw = {
        p.relative_to(output).as_posix(): digest(p)
        for p in sorted(output.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }
    valid = (
        source_unchanged
        and frozen_unchanged
        and all(q["returncode"] == 0 for q in quality.values())
    )
    report = {
        "schema_version": "phase5_remediation_qa_v2",
        "valid": valid,
        "phase5_accepted": False,
        "source_git_commit": revision,
        "source_worktree_clean": not dirty,
        "validation_kind": "working_tree_cpu_qa" if dirty else "clean_source_cpu_qa",
        "source_sha256": source,
        "source_unchanged": source_unchanged,
        "frozen_data_sha256": frozen,
        "frozen_data_unchanged": frozen_unchanged,
        "historical_receipt_audits": prior,
        "quality": quality,
        "raw_output": output.relative_to(ROOT).as_posix(),
        "raw_sha256": raw,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {
                name: importlib.metadata.version(name)
                for name in ("pydantic", "pytest", "ruff", "mypy")
            },
        },
        "model": "ReplayBackend and synthetic guard only",
        "real_model_runs": 0,
        "benchmark_dev_runs": 0,
        "test_payloads_parsed": False,
        "remaining": [
            "production ModelPair runtime/GPU integration and lifecycle",
            "production guard quality and grouped Dev validation",
            "broader semantic origin/scope coverage",
            "Phase 5 freeze",
        ],
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    with (output / "report.json").open("x", encoding="utf-8") as stream:
        stream.write(serialized)
    if receipt_path is not None:
        # A second audit of CURRENT raw bytes, not a reused validity boolean.
        if not audit_receipt(ROOT, output / "report.json")["valid"]:
            raise ValueError("new raw/source receipt failed independent recheck")
        with receipt_path.open("x", encoding="utf-8") as stream:
            stream.write(serialized)
    print(
        json.dumps(
            {
                "valid": valid,
                "phase5_accepted": False,
                "output": str(output),
                "report_sha256": digest(output / "report.json"),
            }
        ),
        flush=True,
    )
    return int(not valid)


if __name__ == "__main__":
    raise SystemExit(main())
