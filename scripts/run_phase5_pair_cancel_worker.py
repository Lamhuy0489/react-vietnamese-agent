#!/usr/bin/env python3
"""Exact pair cancellation worker; factories load only inside owned spawn workers."""

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import MODEL, resolve_mount
from react_agent.llm.guard_hf_v1 import GuardHFConfig, GuardHFFactory
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import (
    AGENT_REVISION,
    AgentFactoryV2,
    GuardFactory,
    verify_gpu_environment,
)
from react_agent.llm.model_pair_probe_v1 import (
    PairCUDAObserver,
    SyntheticPairFactory,
    SyntheticPairObserver,
)
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig
from react_agent.llm.pair_cancellation_v1 import BusyFactory, run_pair_cancellation


@dataclass(frozen=True)
class CancellationPairs:
    agent_path: Path | None = None
    inventory_path: Path | None = None
    guard_path: Path | None = None
    snapshot: GuardSnapshot | None = None

    def __post_init__(self) -> None:
        supplied = (self.agent_path, self.inventory_path, self.guard_path, self.snapshot)
        if any(v is not None for v in supplied) and not all(v is not None for v in supplied):
            raise ValueError("all pinned HF inputs or none required")
        if (
            self.snapshot
            and self.snapshot.upstream_revision != "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
        ):
            raise ValueError("fixed guard revision required")

    def __call__(self, trial: str, root: Path) -> ModelPair:
        if self.snapshot is None:
            return ModelPair(
                BusyFactory(SyntheticPairFactory("agent", root), "agent", trial, root),
                BusyFactory(SyntheticPairFactory("guard", root), "guard", trial, root),
                PairConfig(
                    ModelIdentity("synthetic-agent", "v1"),
                    ModelIdentity("synthetic-guard", "v1"),
                    agent_start_seconds=5,
                    guard_start_seconds=5,
                    agent_call_seconds=0.2,
                    guard_call_seconds=0.2,
                ),
            )
        if self.agent_path is None or self.inventory_path is None or self.guard_path is None:
            raise ValueError("offline model paths required")
        return ModelPair(
            BusyFactory(
                AgentFactoryV2(
                    self.agent_path, self.inventory_path, root / "agent_hf_metrics.jsonl"
                ),
                "agent",
                trial,
                root,
                actual_cuda=True,
            ),
            BusyFactory(
                GuardFactory(
                    GuardHFFactory(
                        self.guard_path,
                        self.snapshot,
                        GuardHFConfig(),
                        root / "guard_hf_metrics.jsonl",
                    )
                ),
                "guard",
                trial,
                root,
                actual_cuda=True,
            ),
            PairConfig(
                ModelIdentity(MODEL, AGENT_REVISION),
                ModelIdentity(self.snapshot.model_id, self.snapshot.model_revision),
            ),
        )


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
        raise ValueError("frozen cancellation source commit required")
    identity: dict[str, Any] = {"backend": args.backend, "source_commit": commit}
    actual = args.backend == "hf"
    if actual:
        if args.guard_path is None or args.snapshot is None:
            raise ValueError("offline pinned guard required")
        pin = GuardSnapshot.model_validate_json(args.snapshot.read_text())
        identity.update(
            environment=verify_gpu_environment(),
            snapshot_sha256=pin.sha256,
            agent_adapter="agent_hf_dual_gpu_v2_tf550",
        )
        factory = CancellationPairs(
            resolve_mount(args.input_root),
            Path("docs/evaluation/qwen7b_upstream_inventory_v1.json"),
            args.guard_path,
            pin,
        )
        observer = PairCUDAObserver()
        result = run_pair_cancellation(args.output, factory, observer, identity, actual_cuda=True)
    else:
        result = run_pair_cancellation(
            args.output, CancellationPairs(), SyntheticPairObserver(), identity
        )
    print(f"PAIR_CANCEL_WORKER_COMPLETE backend={args.backend} valid={result['valid']}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
