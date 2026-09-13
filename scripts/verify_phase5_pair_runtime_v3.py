#!/usr/bin/env python3
"""Capture real-spawn synthetic ModelPair/runtime QA and immutable artifacts."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter

from verify_phase5_remediation import (
    ROOT,
    audit_receipt,
    contained,
    digest,
    executable,
    source_hashes,
    tracked_data_hashes,
)

from react_agent.validation.pair_runtime_audit_v3 import audit_task
from react_agent.validation.worker_shutdown_audit_v2 import audit_event


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    output = contained(ROOT / "results", args.output)
    destination = contained(ROOT / "experiments/manifests", args.receipt)
    if output.exists() or destination.exists():
        raise ValueError("fresh output and receipt required")
    source = source_hashes()
    contract = "docs/architecture/phase5_pair_runtime_v3_contract.md"
    source[contract] = digest(ROOT / contract)
    wrapper = "notebooks/kaggle/security_runtime_kernel_v1.py"
    source[wrapper] = digest(ROOT / wrapper)
    frozen = tracked_data_hashes()
    parent_receipt = ROOT / "experiments/manifests/phase5_worker_shutdown_v2_cpu01.json"
    prior = audit_receipt(ROOT, parent_receipt)
    if not prior["valid"]:
        raise ValueError("pair/runtime v2 prerequisite hashes do not match")
    commit = subprocess.check_output(  # noqa: S603 - fixed local read-only git arguments
        [executable("git"), "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    output.mkdir(parents=True, exist_ok=False)
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
            "tests/integration/test_phase5_pair_runtime_v3.py",
            "--basetemp",
            str(output / "cases"),
            "--junitxml",
            str(output / "focused.xml"),
        ],
        "pytest": [sys.executable, "-m", "pytest", "--junitxml", str(output / "pytest.xml")],
    }
    quality = {}
    for name, command in commands.items():
        print("START " + name, flush=True)
        start = perf_counter()
        log = output / (name + ".log")
        with log.open("x", encoding="utf-8") as stream:
            run = subprocess.run(  # noqa: S603 - fixed QA vectors, shell disabled
                command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False
            )
        quality[name] = {
            "command": command,
            "returncode": run.returncode,
            "seconds": perf_counter() - start,
            "log_sha256": digest(log),
        }
        print(f"DONE {name}: {run.returncode}", flush=True)
    current = source_hashes()
    current[contract] = digest(ROOT / contract)
    current[wrapper] = digest(ROOT / wrapper)
    source_valid = current == source
    data_valid = tracked_data_hashes() == frozen
    # Every retained runtime output is audited; mutation tests use in-memory views.
    paths = sorted((output / "cases").rglob("pair_runtime.json"))
    actual_paths = [
        p
        for p in paths
        if json.loads(p.read_text()).get("profile") == "model_pair_security_runtime_v3"
    ]
    cases = [json.loads(path.read_text()) for path in actual_paths]
    joined_audits = [audit_task(path.parent) for path in actual_paths]
    cleanup_valid = bool(cases) and all(
        case["cleanup_error_class"] is None
        and all(
            worker["closed"]
            and not worker["handle_pending"]
            and all(event["reaped"] for event in worker["lifecycle"])
            for worker in case["snapshot"]["workers"].values()
        )
        for case in cases
    )
    pair_cases = []
    for path in sorted((output / "cases").rglob("pair_shutdown.json")):
        snapshot = json.loads(path.read_text())
        for worker in snapshot["workers"].values():
            for event in worker["lifecycle"]:
                audit_event(event)
                if not event["reaped"]:
                    raise ValueError("unreaped pair teardown fixture")
        pair_cases.append(snapshot)
    raw = {
        path.relative_to(output).as_posix(): digest(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }
    valid = (
        source_valid
        and data_valid
        and cleanup_valid
        and len(pair_cases) == 4
        and all(q["returncode"] == 0 for q in quality.values())
    )
    report = {
        "schema_version": "phase5_pair_shutdown_runtime_qa_v3",
        "valid": valid,
        "phase5_accepted": False,
        "source_git_commit": commit,
        "validation_kind": "working_tree_cpu_qa",
        "source_sha256": source,
        "source_unchanged": source_valid,
        "frozen_data_sha256": frozen,
        "frozen_data_unchanged": data_valid,
        "prior_receipt_audit": prior,
        "quality": quality,
        "raw_output": output.relative_to(ROOT).as_posix(),
        "raw_sha256": raw,
        "pair_runtime_receipts": len(cases),
        "cleanup_valid": cleanup_valid,
        "joined_audits": joined_audits,
        "python": platform.python_version(),
        "real_model_runs": 0,
        "pair_teardown_fixtures": len(pair_cases),
        "benchmark_dev_runs": 0,
        "scope": "real spawn synthetic backends through runtime v7; no GPU or Test inference",
        "remaining": [
            "native Kaggle package/runtime validation",
            "guard quality/grouped Dev",
            "broader semantic scope/origin coverage",
            "Phase 5 freeze",
        ],
    }
    with (output / "report.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    verified = audit_receipt(ROOT, output / "report.json")
    if not valid or not verified["valid"]:
        raise ValueError("raw/source re-audit failed")
    with destination.open("x", encoding="utf-8") as stream:
        stream.write((output / "report.json").read_text(encoding="utf-8"))
    print(
        json.dumps({"valid": valid, "receipt": str(destination), "sha256": digest(destination)}),
        flush=True,
    )
    return int(not valid)


if __name__ == "__main__":
    raise SystemExit(main())
