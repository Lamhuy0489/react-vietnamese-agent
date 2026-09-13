"""Freeze bounded synthetic shutdown QA; never launch GPU or parse held-out data."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
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

from react_agent.validation.worker_shutdown_audit_v2 import audit_event

CONTRACT = "docs/architecture/phase5_worker_shutdown_v2_contract.md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    output = contained(ROOT / "results", args.output)
    destination = contained(ROOT / "experiments/manifests", args.receipt)
    if output.exists() or destination.exists():
        raise ValueError("fresh output/receipt required")
    source = source_hashes() | {CONTRACT: digest(ROOT / CONTRACT)}
    frozen = tracked_data_hashes()
    prior = audit_receipt(
        ROOT, ROOT / "experiments/manifests/phase5_security_runtime_gpu_release_cpu01.json"
    )
    if not prior["valid"]:
        raise ValueError("frozen parent evidence changed")
    commit = subprocess.check_output(  # noqa: S603 - fixed read-only Git operation
        [executable("git"), "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    output.mkdir(parents=True)
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
            "tests/integration/test_phase5_worker_shutdown_v2.py",
            "tests/unit/test_worker_shutdown_audit_v2.py",
            "tests/integration/test_phase5_warm_guard.py",
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
            run = subprocess.run(  # noqa: S603 - fixed local QA vectors, no shell
                command,
                cwd=ROOT,
                stdout=stream,
                stderr=subprocess.STDOUT,
                check=False,
            )
        quality[name] = dict(
            command=command,
            returncode=run.returncode,
            seconds=perf_counter() - start,
            log_sha256=digest(log),
        )
        print(f"DONE {name}: {run.returncode}", flush=True)
    case_paths = sorted((output / "cases").rglob("shutdown_case.json"))
    methods: Counter[str] = Counter()
    cases, controls = 0, 0
    for path in case_paths:
        value = json.loads(path.read_text())
        if value["native_model"] is not False:
            raise ValueError("synthetic scope required")
        for event in value["lifecycle"]:
            if event.get("schema_version") == "worker_shutdown_v2":
                audit_event(event)
                if not event["reaped"]:
                    raise ValueError("unreaped synthetic worker")
                methods[event["method"]] += 1
                cases += 1
            else:
                if event["method"] not in {"TERMINATE", "KILL"} or not event["reaped"]:
                    raise ValueError("legacy short-budget control changed")
                controls += 1
    source_valid = source_hashes() | {CONTRACT: digest(ROOT / CONTRACT)} == source
    data_valid = tracked_data_hashes() == frozen
    raw = {
        p.relative_to(output).as_posix(): digest(p)
        for p in sorted(output.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }
    valid = (
        source_valid
        and data_valid
        and cases == 8
        and controls == 1
        and all(q["returncode"] == 0 for q in quality.values())
    )
    report = dict(
        schema_version="phase5_worker_shutdown_cpu_qa_v2",
        valid=valid,
        phase5_accepted=False,
        validation_kind="working_tree_cpu_qa",
        source_git_commit=commit,
        source_sha256=source,
        source_unchanged=source_valid,
        frozen_data_sha256=frozen,
        frozen_data_unchanged=data_valid,
        prior_receipt_audit=prior,
        quality=quality,
        raw_output=output.relative_to(ROOT).as_posix(),
        raw_sha256=raw,
        shutdown_events=cases,
        legacy_controls=controls,
        shutdown_methods=dict(methods),
        actual_model_loads=0,
        gpu_runs=0,
        scope="Real-spawn synthetic teardown QA only; no native cause, ModelPair integration "
        "or GPU graceful cleanup claim. Held-out data is hash-only.",
    )
    encoded = json.dumps(report, indent=2) + "\n"
    with (output / "report.json").open("x", encoding="utf-8") as stream:
        stream.write(encoded)
    if not valid or not audit_receipt(ROOT, output / "report.json")["valid"]:
        raise ValueError("QA/raw/source acceptance failed; preserve output")
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(encoded)
    print(json.dumps({"valid": valid, "receipt": str(destination), "sha256": digest(destination)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
