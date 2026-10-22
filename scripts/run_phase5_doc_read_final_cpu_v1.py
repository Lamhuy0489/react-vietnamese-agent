"""Run the predeclared fresh synthetic doc_read proof matrix, CPU Replay only."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.validation.doc_read_final_controls_v1 import BENIGN, CASES, NEGATIVE, run_control

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/evaluation"):
        raise ValueError("fresh build/evaluation output required")
    sources = (
        "docs/evaluation/phase5_doc_read_final_proof_v1_protocol.md",
        "src/react_agent/security_v1/doc_read_final_proof_v1.py",
        "src/react_agent/security_v1/doc_read_final_runtime_v1.py",
        "src/react_agent/validation/doc_read_final_runtime_audit_v1.py",
        "src/react_agent/validation/doc_read_final_controls_v1.py",
        "src/react_agent/security_v1/final_literal_proof_v1.py",
        "src/react_agent/security_v1/final_literal_runtime_v1.py",
        "src/react_agent/security_v1/value_origin_v4.py",
        "scripts/run_phase5_doc_read_final_cpu_v1.py",
    )
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    output.mkdir(parents=True)
    git = shutil.which("git")
    if git is None:
        raise ValueError("Git executable required for source identity")
    base = subprocess.run(  # noqa: S603 - resolved host Git, fixed read-only arguments
                          [git, "rev-parse", "HEAD"], cwd=ROOT, check=True,
                          text=True, capture_output=True).stdout.strip()
    declaration = dict(
        protocol="doc_read_final_cpu_declaration_v1", cases=list(CASES),
        git_base=base, source_commit=None, working_tree_sources=hashes,
        native_model_runs=0, held_out_test_loaded=False, native_admitted=False,
    )
    with (output / "declaration.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(declaration, ensure_ascii=False, indent=2) + "\n")
    rows: list[dict[str, Any]] = []
    for case in CASES:
        row = run_control(ROOT, output / case, case)
        rows.append(row)
        print(json.dumps(dict(case=case, checks=row["checks"])), flush=True)
    if hashes != {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}:
        raise ValueError("declared CPU source changed during run")
    summary = {
        group: {arm: dict(total=len(names), desired_pass=sum(
            row["arms"][arm]["desired_pass"] for row in rows if row["case"] in names
        )) for arm in ("baseline", "candidate")}
        for group, names in (("benign", BENIGN), ("negative", NEGATIVE))
    }
    receipt = dict(
        declaration, protocol="doc_read_final_cpu_matrix_receipt_v1", summary=summary,
        case_count=len(rows), runtime_count=2 * len(rows),
        all_gates_passed=all(row["expectation_met"] for row in rows),
        phase5_accepted=False,
        case_receipt_sha256={case: hashlib.sha256((output / case / "receipt.json").read_bytes())
                            .hexdigest() for case in CASES},
    )
    with (output / "receipt.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(summary=summary, all_gates_passed=receipt["all_gates_passed"])))
    if not receipt["all_gates_passed"]:
        raise SystemExit("CPU matrix failed; preserve raw outputs, do not promote")


if __name__ == "__main__":
    main()
