"""Record public-Dev coverage and current-runtime synthetic acceptance controls."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

from prepare_phase5_grouped_package_v3 import dependency_closure

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.security_v1.a6_qa import cases
from react_agent.validation.acceptance_controls_v1 import run_control
from react_agent.validation.acceptance_coverage_v1 import coverage, validate_coverage

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("fresh results output required; no implicit resume/retry")
    release = ROOT / "data/adversarial/release_v2"
    plan = coverage(release)
    output.mkdir(parents=True)
    write_receipt(output / "coverage.json", plan)
    results = []
    for form in ("supported", "sentence"):
        for case in cases():
            result = run_control(ROOT, output / form / case.name, case, form=form)
            results.append({k: v for k, v in result.items() if k != "raw_sha256"})
            write_receipt(output / form / case.name / "control.json", result)
            print(form, case.name, result["expectation_met"], flush=True)
    validate_coverage(plan, release)
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=ROOT,
        text=True,
    ).strip()  # noqa: S603 - fixed read-only Git command
    sources = dependency_closure(ROOT, {"scripts/run_phase5_acceptance_controls_v1.py"})
    write_receipt(
        output / "summary.json",
        dict(
            protocol="phase5_acceptance_controls_v1",
            valid=True,
            controls=results,
            execution_count=len(results),
            expectation_failures=sum(not r["expectation_met"] for r in results),
            git_base_commit=commit,
            source_identity="working-tree hashes, not a new worker freeze",
            source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
            smoke_input_sha256=inventory(ROOT / "data/smoke"),
            raw_sha256=inventory(output),
            model_inference_runs=0,
            gpu_runs=0,
            private_ground_truth_accessed=False,
            test_payload_accessed=False,
            acceptance_passed=all(r["expectation_met"] for r in results),
            phase5_accepted=False,
        ),
    )


if __name__ == "__main__":
    main()
