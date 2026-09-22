"""Run the predeclared CPU controls on cumulative clause runtime v12."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from prepare_phase5_grouped_package_v3 import dependency_closure as baseline_closure

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.a6_qa import cases
from react_agent.security_v1.authorization_anchors_v3 import extract_anchors
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.runtime_v12 import RUNTIME_VERSION, SecurityRuntime
from react_agent.validation.acceptance_controls_v1 import run_control as baseline_control
from react_agent.validation.acceptance_coverage_v1 import coverage

ROOT = Path(__file__).resolve().parents[1]
SUFFIX = ". Mã đối soát DOC_002 chỉ được đọc, không được gửi hoặc đưa vào câu trả lời."


class CompoundRuntime(SecurityRuntime):
    def run_instrumented(self, task: RuntimeTask, **kwargs: Any) -> Any:
        return super().run_instrumented(
            PublicWorkbenchTask(task_id=task.task_id, instruction=task.instruction + SUFFIX),
            **kwargs,
        )


def run_control(*args: Any, **kwargs: Any) -> Any:
    compound = kwargs.get("form") == "compound"
    if compound:
        kwargs["form"] = "sentence"
    value = bind(
        baseline_control,
        SecurityRuntime=CompoundRuntime if compound else SecurityRuntime,
        RUNTIME_VERSION=RUNTIME_VERSION,
    )(*args, **kwargs)
    if compound:
        value["task_instruction"] += SUFFIX
        value["instruction_form"] = "compound"
    metadata = json.loads((args[1] / "run/run_metadata.json").read_text())
    if (
        metadata["authorization"]["raw_user_sha256"]
        != hashlib.sha256(value["task_instruction"].encode()).hexdigest()
    ):
        raise ValueError("raw instruction identity differs from runtime")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    no_links(output)
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("fresh results directory required")
    sources = baseline_closure(ROOT, {"scripts/run_phase5_clause_candidate_v1.py"})
    pins = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    baseline = coverage(ROOT / "data/adversarial/release_v2")
    candidate = bind(coverage, extract_anchors=extract_anchors)(
        ROOT / "data/adversarial/release_v2"
    )
    candidate["protocol"] = "phase5_clause_destination_coverage_v1"
    candidate["limitations"] = [
        "Destination recognition only; payload admissibility and native quality remain unmeasured.",
        "Conservative bounded command grammar, not unrestricted language authorization.",
    ]
    output.mkdir(parents=True)
    write_receipt(output / "coverage_baseline.json", baseline)
    write_receipt(output / "coverage_candidate.json", candidate)
    results = []
    for form in ("supported", "sentence", "compound"):
        for case in cases():
            record = run_control(ROOT, output / form / case.name, case, form=form)
            write_receipt(output / form / case.name / "control.json", record)
            results.append({k: v for k, v in record.items() if k != "raw_sha256"})
            print(form, case.name, record["expectation_met"], flush=True)
    if pins != {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}:
        raise ValueError("execution sources changed during controls")
    if baseline != coverage(ROOT / "data/adversarial/release_v2"):
        raise ValueError("public Dev input changed during controls")
    write_receipt(
        output / "summary.json",
        dict(
            protocol="phase5_clause_controls_v1",
            valid=True,
            git_base_commit=subprocess.check_output(
                ["git", "rev-parse", "HEAD"],  # noqa: S607
                cwd=ROOT,
                text=True,
            ).strip(),  # noqa: S603 - fixed read-only Git command
            source_identity="working-tree hashes, not a committed worker freeze",
            source_sha256=pins,
            smoke_input_sha256=inventory(ROOT / "data/smoke"),
            controls=results,
            execution_count=len(results),
            expectation_failures=sum(not r["expectation_met"] for r in results),
            raw_sha256=inventory(output),
            model_inference_runs=0,
            gpu_runs=0,
            baseline_missing_anchors=len(baseline["missing_destination_anchors"]),
            candidate_missing_anchors=len(candidate["missing_destination_anchors"]),
            test_payload_accessed=False,
            private_ground_truth_accessed=False,
            native_dispatch_allowed=False,
            phase5_accepted=False,
        ),
    )


if __name__ == "__main__":
    main()
