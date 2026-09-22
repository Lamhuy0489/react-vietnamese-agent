"""Fresh CPU-only paired integration evidence; never submits or loads native models."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path
from typing import Any

from prepare_phase5_grouped_package_v3 import dependency_closure

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.clause_pair_probe_v1 import SCHEDULE, checkpoint, run
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver
from react_agent.validation.clause_pair_controls_v1 import CASES, run_control
from react_agent.validation.context_stress_audit_v1 import equal

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    no_links(output)
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("fresh results root required")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=ROOT,
        text=True,
    ).strip()  # noqa: S603 - fixed read-only Git command
    sources = dependency_closure(ROOT, {"scripts/run_phase5_clause_pair_controls_v1.py"})
    pins = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    output.mkdir(parents=True)
    conditions: dict[str, Any] = {}
    for condition in ("valid", "backend_failure"):
        args = dict(
            backend="stub",
            commit=commit,
            observer_factory=SyntheticPairObserver,
            condition=condition,
        )
        root = output / condition
        result = run(root, ROOT / "data/clean/v1_1/environment", **args)
        before = inventory(root)
        audited = {key: checkpoint(root / "tasks" / key) for key in SCHEDULE}
        equal(
            run(root, ROOT / "data/clean/v1_1/environment", resume=True, **args),
            result,
            "complete resume unchanged",
        )
        equal(
            {key: checkpoint(root / "tasks" / key) for key in SCHEDULE},
            audited,
            "independent repeated checkpoint audits",
        )
        equal(inventory(root), before, "audit/resume writes no raw artifacts")
        conditions[condition] = result
    controls = []
    for name in CASES:
        record = run_control(ROOT, output / "egress" / name, name)
        write_receipt(output / "egress" / name / "control.json", record)
        controls.append({k: v for k, v in record.items() if k != "raw_sha256"})
        print(name, record["expectation_met"], flush=True)
    equal(
        {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
        pins,
        "execution source stable",
    )
    write_receipt(
        output / "summary.json",
        dict(
            protocol="phase5_clause_pair_controls_v1",
            valid=True,
            git_base_commit=commit,
            source_identity="uncommitted exact working-tree hashes",
            source_sha256=pins,
            conditions=conditions,
            egress_controls=controls,
            expectation_failures=sum(not c["expectation_met"] for c in controls),
            runtime_tasks=12,
            spawned_workers=24,
            raw_sha256=inventory(output),
            model_inference_runs=0,
            gpu_runs=0,
            test_payload_accessed=False,
            private_ground_truth_accessed=False,
            native_dispatch_allowed=False,
            phase5_accepted=False,
        ),
    )


if __name__ == "__main__":
    main()
