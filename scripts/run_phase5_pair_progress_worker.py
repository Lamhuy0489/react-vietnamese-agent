#!/usr/bin/env python3
"""Versioned worker-local progress prevention; frozen cancellation transport unchanged."""

from __future__ import annotations

import argparse
import gc
import os
import platform
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from run_phase5_pair_cancel_worker import CancellationPairs

from react_agent.llm.agent_mount_v1 import no_links, resolve_mount, write_receipt
from react_agent.llm.base import LLMBackend
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.ipc_trace_v1 import TracedFactory, TrackerTrace
from react_agent.llm.model_pair_hf_v1 import verify_gpu_environment
from react_agent.llm.model_pair_probe_v1 import (
    PairCUDAObserver,
    PairObserver,
    SyntheticPairObserver,
)
from react_agent.llm.model_pair_v1 import ModelPair
from react_agent.llm.pair_cancellation_v1 import run_pair_cancellation
from react_agent.llm.worker_progress_v1 import configure_worker_progress


@dataclass(frozen=True)
class ProgressReceiptFactory:
    factory: Callable[[], LLMBackend]
    path: Path
    role: str

    def __call__(self) -> LLMBackend:
        # Outer TracedFactory has installed tracing before this native import.
        policy = configure_worker_progress()
        write_receipt(self.path, {"pid": os.getpid(), "role": self.role, "policy": policy})
        return self.factory()


@dataclass(frozen=True)
class ProgressPairs:
    factory: CancellationPairs
    trace_root: Path
    policy_root: Path

    def __call__(self, trial: str, output: Path) -> ModelPair:
        pair = self.factory(trial, output)
        # Warm transport has not started either process. Wrap only the lazy
        # factory, never replace the worker target, graces, requests or policy.
        for role, worker in pair._workers.items():
            if worker._process is not None:
                raise ValueError("only untouched lazy factory may be instrumented")
            worker.factory = TracedFactory(
                ProgressReceiptFactory(
                    worker.factory, self.policy_root / f"{trial}_{role}.json", role
                ),
                self.trace_root / f"{trial}_{role}.jsonl",
                role,
            )
        return pair


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
        raise ValueError("frozen source commit required")
    no_links(args.output)
    args.output.mkdir(parents=True, exist_ok=False)
    traces = args.output / "tracker"
    traces.mkdir()
    policies = args.output / "progress_policy"
    policies.mkdir()
    trace = TrackerTrace(traces / "owner.jsonl", "owner")
    actual = args.backend == "hf"
    identity: dict[str, Any] = {
        "backend": args.backend,
        "source_commit": commit,
        "instrumentation": "ipc_tracker_trace_v1",
        "python_version": platform.python_version(),
    }
    write_receipt(
        args.output / "progress_identity.json",
        {"protocol": "pair_progress_v1", "source_commit": commit, "owner_pid": os.getpid()},
    )
    observer: PairObserver
    if actual:
        if args.guard_path is None or args.snapshot is None:
            raise ValueError("offline pinned guard required")
        pin = GuardSnapshot.model_validate_json(args.snapshot.read_text())
        identity.update(environment=verify_gpu_environment(), snapshot_sha256=pin.sha256)
        factory = CancellationPairs(
            resolve_mount(args.input_root),
            Path("docs/evaluation/qwen7b_upstream_inventory_v1.json"),
            args.guard_path,
            pin,
        )
        observer = PairCUDAObserver()
    else:
        factory = CancellationPairs()
        observer = SyntheticPairObserver()
    write_receipt(args.output / "identity.json", identity)
    result = run_pair_cancellation(
        args.output / "pair_cancellation",
        ProgressPairs(factory, traces, policies),
        observer,
        identity,
        actual_cuda=actual,
    )
    # Not a cleanup workaround: do not collect/modify live workers or unregister
    # their resources manually. After the suite dropped all pairs, this checkpoint
    # distinguishes normal parent finalization from the child-owned registrations.
    collected = gc.collect()
    trace.record("PROBE_DONE", valid=result["valid"], gc_collected=collected)
    print(f"PAIR_PROGRESS_WORKER_COMPLETE backend={args.backend} valid={result['valid']}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
