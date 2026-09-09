#!/usr/bin/env python3
"""Reproduce admission of saved public hash evidence, not live model/GPU loading."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.agent_runtime_input_v1 import (
    INVENTORY_SHA256,
    admit_runtime_scan,
    parameter_shapes,
    read_object,
)
from react_agent.llm.coexistence_placement_v1 import PARAMETERS, PlacementPlan

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    no_links(args.output)
    if args.output.exists() or not args.output.resolve().is_relative_to(ROOT / "results"):
        raise ValueError("fresh results-only output required")
    before = prerequisites(ROOT)
    inventory = ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json"
    scan_path = ROOT / "experiments/manifests/phase5_agent_mount_v1_scan01.json"
    qa_path = ROOT / "experiments/manifests/phase5_agent_mount_v1_release_qa01.json"
    qa = read_object(qa_path)
    if digest(inventory) != INVENTORY_SHA256 or any(
        digest(ROOT / name) != expected
        for name, expected in qa["source_and_evidence_sha256"].items()
    ):
        raise ValueError("frozen scan QA evidence changed")
    prior_path = ROOT / "experiments/manifests/phase5_guard_hf_v1_validation01.json"
    prior = read_object(prior_path)
    for name, expected in prior["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("frozen source changed: " + name)
    admission = admit_runtime_scan(read_object(scan_path), read_object(inventory))
    shapes = parameter_shapes()
    if len(shapes) != 339 or sum(math.prod(shape) for shape in shapes.values()) != PARAMETERS:
        raise ValueError("tensor geometry arithmetic mismatch")
    paths = [
        "scripts/verify_phase5_agent_loader.py",
        "src/react_agent/llm/agent_runtime_input_v1.py",
        "src/react_agent/llm/agent_hf_v1.py",
        "tests/unit/test_agent_runtime_input_v1.py",
        "tests/unit/test_agent_hf_v1.py",
        "docs/architecture/phase5_agent_hf_v1_contract.md",
    ]
    source = {name: digest(ROOT / name) for name in paths}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603,S607
    clean = not subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)  # noqa: S603,S607
    if prerequisites(ROOT) != before or any(digest(ROOT / n) != h for n, h in source.items()):
        raise ValueError("source or seal changed during validation")
    result = {
        "protocol": "phase5_agent_loader_cpu_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_git_commit": commit,
        "source_worktree_clean": clean,
        "source_sha256": source,
        "saved_scan_admission": admission,
        "expected_parameter_tensors": len(shapes),
        "parameters": PARAMETERS,
        "plan_sha256": PlacementPlan().sha256,
        "prior_source_hashes_verified": len(prior["source_sha256"]),
        "prerequisites": before,
        "evidence_sha256": {
            str(p.relative_to(ROOT)): digest(p) for p in (inventory, scan_path, qa_path, prior_path)
        },
        "live_header_validation": "NOT_RUN: synthetic headers tested separately",
        "model_loads": 0,
        "gpu_runs": 0,
        "local_agent_weight_downloads": 0,
        "test_payloads_parsed": 0,
        "combined_gpu_fit": "NOT_MEASURED",
        "scope": "Read-only saved hash evidence plus geometry arithmetic; not a live load permit",
    }
    args.output.mkdir(parents=True)
    write_receipt(args.output / "receipt.json", result)
    print(
        json.dumps(
            {
                "valid": True,
                "parameters": PARAMETERS,
                "model_loads": 0,
                "full_inventory_match": admission["full_inventory_match"],
            }
        )
    )


if __name__ == "__main__":
    main()
