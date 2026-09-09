#!/usr/bin/env python3
"""Bounded pair worker entry point for the exact private offline Kaggle bundle."""

import argparse
import os
from pathlib import Path

from react_agent.llm.agent_mount_v1 import resolve_mount
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import hf_pair, verify_gpu_environment
from react_agent.llm.model_pair_probe_v1 import (
    PairCUDAObserver,
    SyntheticPairFactory,
    SyntheticPairObserver,
    run_pair_probe,
)
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("stub", "hf"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--guard-path", type=Path)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    commit = os.environ.get("PAIR_SOURCE_COMMIT", "")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("frozen pair overlay commit required")
    if args.backend == "hf":
        if args.guard_path is None or args.snapshot is None:
            raise ValueError("offline guard snapshot and model required")
        pin = GuardSnapshot.model_validate_json(args.snapshot.read_text())
        environment = verify_gpu_environment()
        instance = hf_pair(
            resolve_mount(args.input_root),
            Path("docs/evaluation/qwen7b_upstream_inventory_v1.json"),
            args.guard_path,
            pin,
            args.output,
        )
        observer = PairCUDAObserver()
        result = run_pair_probe(
            args.output,
            instance,
            observer,
            {
                "backend": "hf",
                "source_commit": commit,
                "snapshot_sha256": pin.sha256,
                "environment": environment,
                "agent_adapter": "agent_hf_dual_gpu_v2_tf550",
            },
        )
    else:
        instance = ModelPair(
            SyntheticPairFactory("agent", args.output),
            SyntheticPairFactory("guard", args.output),
            PairConfig(
                ModelIdentity("synthetic-agent", "v1"),
                ModelIdentity("synthetic-guard", "v1"),
                agent_start_seconds=5,
                guard_start_seconds=5,
                agent_call_seconds=2,
                guard_call_seconds=2,
            ),
        )
        result = run_pair_probe(
            args.output,
            instance,
            SyntheticPairObserver(),
            {"backend": "stub", "source_commit": commit},
        )
    print(f"PAIR_WORKER_COMPLETE backend={args.backend} valid={result['valid']}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
