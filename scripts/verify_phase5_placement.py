#!/usr/bin/env python3
"""Reproduce CPU placement arithmetic against historical hash-bound metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.coexistence_placement_v1 import PARAMETERS, PlacementPlan
from react_agent.llm.guard_probe_v1 import write_json

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or not args.output.resolve().is_relative_to(ROOT / "results"):
        raise ValueError("fresh results-only output required")
    pilot_receipt = ROOT / "experiments/manifests/measured_qwen7b_v1_audit.json"
    pilot = json.loads(pilot_receipt.read_text())
    name = "phase2_clean_dev_pilot/model_setup.json"
    setup_path = ROOT / "results/phase2/measured_qwen7b_v1" / name
    # Only historical setup metadata; no task result, trace, GT or Test payload reads.
    if (
        pilot["valid"] is not True
        or pilot["model_source"] != "qwen-lm/qwen2.5/transformers/7b-instruct/1"
        or digest(setup_path) != pilot["raw_artifact_sha256"][name]
    ):
        raise ValueError("historical setup hash mismatch")
    setup = json.loads(setup_path.read_text())
    if setup["parameters_loaded"] != PARAMETERS or setup["dtype"] != "float16":
        raise ValueError("parameter geometry disagrees with historical setup")
    prior_path = ROOT / "experiments/manifests/phase5_guard_hf_v1_validation01.json"
    prior = json.loads(prior_path.read_text())
    for relative, expected in prior["source_sha256"].items():
        if digest(ROOT / relative) != expected:
            raise ValueError("frozen source changed: " + relative)
    before = prerequisites(ROOT)
    plan = PlacementPlan()
    # Total capacity is historical; it is not a live free-memory admission sample.
    totals = [g["total_memory_bytes"] for g in setup["gpus"]]
    if len(totals) != 2 or any(
        n > t for n, t in zip(plan.required_free_bytes(), totals, strict=True)
    ):
        raise ValueError("combined budgets exceed historical capacity")
    source_paths = [
        Path(__file__),
        ROOT / "src/react_agent/llm/coexistence_placement_v1.py",
        ROOT / "tests/unit/test_coexistence_placement_v1.py",
        ROOT / "docs/architecture/phase5_coexistence_placement_v1_contract.md",
    ]
    source = {str(p.relative_to(ROOT)): digest(p) for p in source_paths}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S607,S603
    clean = not subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)  # noqa: S607,S603
    if prerequisites(ROOT) != before or any(digest(ROOT / p) != h for p, h in source.items()):
        raise ValueError("source or seal changed during validation")
    result = {
        "protocol": "phase5_placement_cpu_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_git_commit": commit,
        "source_worktree_clean": clean,
        "source_sha256": source,
        "plan": plan.model_dump(mode="json"),
        "plan_sha256": plan.sha256,
        "device_map": plan.device_map(),
        "parameters": PARAMETERS,
        "fp16_weight_bytes": plan.weight_bytes(),
        "dynamic_kv_bytes": plan.kv_bytes(),
        "estimated_agent_bytes": plan.estimated_bytes(),
        "required_free_bytes_before_either_load": plan.required_free_bytes(),
        "historical_device_total_bytes": totals,
        "evidence_sha256": {
            str(p.relative_to(ROOT)): digest(p) for p in (pilot_receipt, setup_path, prior_path)
        },
        "prior_source_hashes_verified": len(prior["source_sha256"]),
        "prerequisites": before,
        "model_loads": 0,
        "gpu_runs": 0,
        "test_payloads_parsed": 0,
        "live_free_memory_admission": "NOT_RUN",
        "combined_gpu_fit": "NOT_MEASURED",
        "agent_snapshot_authenticated": False,
        "scope": "Analytical CPU budget admission only; workspace is not a peak bound",
    }
    args.output.mkdir(parents=True)
    write_json(args.output / "receipt.json", result)
    print(
        json.dumps(
            {
                "valid": True,
                "plan_sha256": plan.sha256,
                "estimated_agent_gib": [n / 1024**3 for n in plan.estimated_bytes()],
                "combined_gpu_fit": "NOT_MEASURED",
            }
        )
    )


if __name__ == "__main__":
    main()
