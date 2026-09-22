"""Run all eight declared Dev32 CPU shards, keeping immutable checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

from prepare_phase5_grouped_package_v3 import dependency_closure

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.clause_dev_runner_v1 import run
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.validation.context_stress_audit_v1 import equal

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    no_links(output)
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("fresh CPU results directory required")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=ROOT,
        text=True,
    ).strip()  # noqa: S603 - fixed read-only command
    sources = dependency_closure(ROOT, {"scripts/run_phase5_clause_dev32_cpu_v1.py"})
    pins = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    output.mkdir(parents=True)
    shards = []
    for shard in range(8):
        args = (
            output / f"shard{shard}",
            ROOT / "data/adversarial/release_v2",
            ROOT / "data/clean/v1_1/environment",
        )
        value = run(*args, commit=commit, shard=shard)
        before = inventory(args[0])
        equal(run(*args, commit=commit, shard=shard, resume=True), value, "resume result")
        equal(inventory(args[0]), before, "complete-resume raw unchanged")
        shards.append(value)
    equal(
        {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
        pins,
        "execution sources unchanged",
    )
    write_receipt(
        output / "summary.json",
        dict(
            protocol="clause_dev32_cpu_controls_v1",
            valid=True,
            git_base_commit=commit,
            source_identity="uncommitted working-tree pins",
            source_sha256=pins,
            shards=shards,
            runtime_tasks=sum(s["completed"] for s in shards),
            raw_sha256=inventory(output),
            model_inference_runs=0,
            gpu_runs=0,
            quality_scored=False,
            native_dispatch_allowed=False,
            phase5_accepted=False,
            test_payload_accessed=False,
            private_ground_truth_accessed=False,
        ),
    )


if __name__ == "__main__":
    main()
