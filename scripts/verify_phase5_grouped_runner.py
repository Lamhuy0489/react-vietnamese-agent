#!/usr/bin/env python3
"""Freeze grouped scripted CPU QA; keep tampering fixtures separate from valid runs."""

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

from react_agent.llm.grouped_dev_identity_v1 import identity
from react_agent.validation.grouped_dev_checkpoint_v1 import audit_prefix


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    output = contained(ROOT / "results", args.output)
    destination = contained(ROOT / "experiments/manifests", args.receipt)
    if output.exists() or destination.exists():
        raise ValueError("fresh output and receipt required")
    contract = "docs/architecture/phase5_grouped_runner_v1_contract.md"
    source = source_hashes()
    source[contract] = digest(ROOT / contract)
    frozen = tracked_data_hashes()
    prior = audit_receipt(ROOT, ROOT / "experiments/manifests/phase5_sql_scope_v5_cpu01.json")
    if not prior["valid"]:
        raise ValueError("SQL scope prerequisite hashes do not match")
    commit = subprocess.check_output(  # noqa: S603 - resolved executable, fixed read-only args
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
            "tests/unit/test_grouped_dev_identity_v1.py",
            "tests/integration/test_grouped_dev_runner_v1.py",
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
            result = subprocess.run(  # noqa: S603 - fixed QA vectors, no shell
                command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False
            )
        quality[name] = dict(
            command=command,
            returncode=result.returncode,
            seconds=perf_counter() - start,
            log_sha256=digest(log),
        )
        print(f"DONE {name}: {result.returncode}", flush=True)
    current = source_hashes()
    current[contract] = digest(ROOT / contract)
    source_valid = source == current
    data_valid = frozen == tracked_data_hashes()
    # Only the full-coverage fixture roots are accepted. Other tests intentionally
    # corrupt raw files/metadata or inject a malformed agent response. Preserve
    # their hashes but never count them as clean benchmark task executions.
    roots = sorted(
        p / "run"
        for p in (output / "cases").iterdir()
        if p.is_dir() and not p.is_symlink() and p.name.startswith("test_all_112_")
    )
    manifest, _ = identity(
        ROOT / "data/adversarial/release_v2", ROOT / "data/clean/v1_1/environment", "a" * 40
    )
    shards: list[int] = []
    keys: list[str] = []
    statuses: list[str] = []
    for root in roots:
        saved = json.loads((root / "identity.json").read_text())
        shard = saved["shard"]
        checks = audit_prefix(root, manifest, shard)
        if len(checks) != 14:
            raise ValueError("incomplete retained shard")
        shards.append(shard)
        keys.extend(c["key"] for c in checks)
        statuses.extend(c["terminal"] for c in checks)
    coverage_valid = sorted(shards) == list(range(8)) and (
        len(keys) == 112 and set(keys) == {t["key"] for t in manifest["tasks"]}
    )
    raw = {
        p.relative_to(output).as_posix(): digest(p)
        for p in sorted(output.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }
    valid = (
        source_valid
        and data_valid
        and coverage_valid
        and all(q["returncode"] == 0 for q in quality.values())
    )
    report = dict(
        schema_version="phase5_grouped_runner_qa_v1",
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
        grouped_checkpoint_audit=dict(
            valid=coverage_valid,
            shards=sorted(shards),
            task_keys=keys,
            terminal_statuses=statuses,
            roots=[p.relative_to(output).as_posix() for p in roots],
            test_manifest_commit="a" * 40,
            note="Test sentinel only; source_git_commit and source_sha256 bind actual QA code.",
        ),
        diagnostic_sidecar_records=sum(
            len(p.read_text().splitlines())
            for root in roots
            for p in root.rglob("guard_diagnostics.jsonl")
        ),
        negative_fixture_policy="Other focused roots retained as tamper/failure controls, "
        "excluded from the 112 audited keys and diagnostic count.",
        python=platform.python_version(),
        real_model_runs=0,
        quality_scoring=False,
        test_payload_accessed=False,
        scope="112 real-spawn scripted public Dev runtime-v10 tasks; no native or quality claim",
        remaining=[
            "native grouped adapter/auditor",
            "exact Kaggle package preflight",
            "grouped Dev native quality/timing/lifecycle",
            "Phase 5 freeze",
        ],
    )
    with (output / "report.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    verified = audit_receipt(ROOT, output / "report.json")
    if not valid or not verified["valid"]:
        raise ValueError("grouped QA or source/raw re-audit failed; preserve output")
    with destination.open("x", encoding="utf-8") as stream:
        stream.write((output / "report.json").read_text(encoding="utf-8"))
    print(
        json.dumps(dict(valid=True, receipt=str(destination), sha256=digest(destination))),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
