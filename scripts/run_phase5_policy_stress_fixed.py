#!/usr/bin/env python3
"""Corrected readiness/factory composition; native policy and stress backends unchanged."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from react_agent.llm.agent_mount_v1 import resolve_mount
from react_agent.llm.context_stress_probe_v1 import run_context_probe
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import hf_pair, verify_gpu_environment
from react_agent.llm.model_pair_probe_v1 import PairCUDAObserver
from react_agent.llm.policy_stress_factory_v2 import instrument_pair


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--policy-output", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--guard-path", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()
    commit = os.environ.get("PAIR_SOURCE_COMMIT", "")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("exact committed source identity required")
    from react_agent.llm.agent_mount_v1 import no_links

    for path in (args.output, args.policy_output):
        no_links(path)
        if path.exists():
            raise ValueError("fresh probe and policy roots required")
    output, policy = args.output.resolve(), args.policy_output.resolve()
    if output.is_relative_to(policy) or policy.is_relative_to(output):
        raise ValueError("separate non-nested probe and policy roots required")
    pin = GuardSnapshot.model_validate_json(args.snapshot.read_text())
    environment = verify_gpu_environment()
    pair = hf_pair(
        resolve_mount(args.input_root),
        Path("docs/evaluation/qwen7b_upstream_inventory_v1.json"),
        args.guard_path,
        pin,
        args.output,
    )
    instrument_pair(pair, args.output, args.policy_output)
    result = run_context_probe(
        args.output,
        pair,
        PairCUDAObserver(),
        {
            "backend": "hf",
            "source_commit": commit,
            "snapshot_sha256": pin.sha256,
            "environment": environment,
            "progress_policy": "worker_thread_progress_v1",
        },
    )
    print(
        f"POLICY_STRESS_WORKER_COMPLETE valid={result['valid']} "
        "independent_policy_audit_pending=True"
    )
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
