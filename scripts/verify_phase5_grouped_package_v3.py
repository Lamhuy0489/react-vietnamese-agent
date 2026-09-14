"""Full CPU source QA for native grouped packaging; never infer GPU acceptance."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter

from prepare_phase5_document_probe import committed_sources
from prepare_phase5_grouped_package_v3 import TEMPLATE, file_hashes
from verify_phase5_remediation import (
    ROOT,
    audit_receipt,
    contained,
    digest,
    executable,
    source_hashes,
    tracked_data_hashes,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = contained(ROOT / "results", args.output)
    if output.exists():
        raise ValueError("fresh QA output required")
    commit = subprocess.check_output(  # noqa: S603 - read-only Git object
        [executable("git"), "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    names = set(source_hashes()) | {
        TEMPLATE,
        "docs/architecture/phase5_grouped_package_v3_contract.md",
        "docs/architecture/phase5_grouped_native_v2_contract.md",
    }
    source = committed_sources(names, commit)
    data = tracked_data_hashes()
    output.mkdir(parents=True)
    commands = {
        "setup": [sys.executable, "scripts/verify_setup.py"],
        "ruff": [sys.executable, "-m", "ruff", "check", "."],
        "mypy": [sys.executable, "-m", "mypy", "src", "scripts"],
        "knowledge": [executable("make"), "knowledge-check"],
        "pytest": [sys.executable, "-m", "pytest", "--junitxml", str(output / "pytest.xml")],
    }
    quality = {}
    for name, command in commands.items():
        print("START " + name, flush=True)
        start = perf_counter()
        with (output / (name + ".log")).open("x") as stream:
            result = subprocess.run(  # noqa: S603 - explicit fixed QA arguments
                command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False
            )
        quality[name] = dict(
            command=command,
            returncode=result.returncode,
            seconds=perf_counter() - start,
            log_sha256=digest(output / (name + ".log")),
        )
        print(f"DONE {name}: {result.returncode}", flush=True)
    source_valid = source == committed_sources(names, commit)
    data_valid = data == tracked_data_hashes()
    valid = source_valid and data_valid and all(q["returncode"] == 0 for q in quality.values())
    receipt = dict(
        protocol="grouped_package_v3_full_cpu_qa",
        valid=valid,
        source_git_commit=commit,
        source_sha256=source,
        source_unchanged=source_valid,
        frozen_data_sha256=data,
        frozen_data_unchanged=data_valid,
        quality=quality,
        raw_output=output.relative_to(ROOT).as_posix(),
        raw_sha256=file_hashes(output),
        actual_model_loads=0,
        phase5_accepted=False,
        test_payload_accessed=False,
        scope="Full repository CPU QA; Test files hashed only, no native quality claim",
    )
    (output / "report.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if not valid or not audit_receipt(ROOT, output / "report.json")["valid"]:
        raise ValueError("QA failed; preserve evidence and do not submit")
    print("GROUPED_PACKAGE_V3_FULL_QA_OK", flush=True)


if __name__ == "__main__":
    main()
