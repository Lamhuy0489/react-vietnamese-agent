#!/usr/bin/env python3
"""Separate maximum-context diagnostic entry; not packaged or GPU-validated yet."""

import argparse
import os
from pathlib import Path

from react_agent.llm.agent_mount_v1 import resolve_mount
from react_agent.llm.context_stress_probe_v1 import SyntheticStressFactory, run_context_probe
from react_agent.llm.context_stress_v1 import ContextStressFactory
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import hf_pair, verify_gpu_environment
from react_agent.llm.model_pair_probe_v1 import PairCUDAObserver, SyntheticPairObserver
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory


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
        raise ValueError("exact committed source identity required")
    if args.backend == "hf":
        if args.guard_path is None or args.snapshot is None:
            raise ValueError("offline guard snapshot and model required")
        pin = GuardSnapshot.model_validate_json(args.snapshot.read_text())
        environment = verify_gpu_environment()
        pair = hf_pair(
            resolve_mount(args.input_root),
            Path("docs/evaluation/qwen7b_upstream_inventory_v1.json"),
            args.guard_path,
            pin,
            args.output,
        )
        for role in ("agent", "guard"):
            worker = pair._workers[role]
            worker.factory = ThreadProgressFactory(
                ContextStressFactory(
                    worker.factory,
                    role,
                    args.output / f"{role}_stress",
                )
            )
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
    else:
        pair = ModelPair(
            SyntheticStressFactory("agent", args.output),
            SyntheticStressFactory("guard", args.output),
            PairConfig(
                ModelIdentity("synthetic-agent", "v1"),
                ModelIdentity("synthetic-guard", "v1"),
                agent_start_seconds=5,
                guard_start_seconds=5,
                agent_call_seconds=2,
                guard_call_seconds=2,
            ),
        )
        result = run_context_probe(
            args.output,
            pair,
            SyntheticPairObserver(),
            {
                "backend": "stub",
                "source_commit": commit,
            },
        )
    print(f"CONTEXT_STRESS_WORKER_COMPLETE backend={args.backend} valid={result['valid']}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
