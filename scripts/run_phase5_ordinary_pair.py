#!/usr/bin/env python3
"""Ordinary A/B/A runner; stub default, explicit HF mode only on a prepared GPU worker."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, resolve_mount
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import verify_gpu_environment
from react_agent.llm.model_pair_probe_v1 import (
    PairCUDAObserver,
    PairObserver,
    SyntheticPairFactory,
    SyntheticPairObserver,
)
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig
from react_agent.llm.ordinary_pair_probe_v1 import fresh_roots, native_pair, run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("stub", "hf"), default="stub")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--policy-output", type=Path)
    parser.add_argument("--attention-output", type=Path)
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--guard-path", type=Path)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    fresh_roots(args.output)
    commit = os.environ.get("PAIR_SOURCE_COMMIT", "")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("exact committed source identity required")
    identity: dict[str, Any] = dict(backend=args.backend, source_commit=commit)
    observer: PairObserver
    if args.backend == "stub":
        if any(
            value is not None
            for value in (args.policy_output, args.attention_output, args.guard_path, args.snapshot)
        ):
            raise ValueError("native options are not used by stub mode")
        pair = ModelPair(
            SyntheticPairFactory("agent", args.output),
            SyntheticPairFactory("guard", args.output),
            PairConfig(
                ModelIdentity("synthetic-agent", "v1"), ModelIdentity("synthetic-guard", "v1")
            ),
        )
        observer = SyntheticPairObserver()
    else:
        if any(
            value is None
            for value in (args.policy_output, args.attention_output, args.guard_path, args.snapshot)
        ):
            raise ValueError("HF requires policy, attention, guard and snapshot paths")
        fresh_roots(args.output, args.policy_output, args.attention_output)
        no_links(args.snapshot)
        pin = GuardSnapshot.model_validate_json(args.snapshot.read_text())
        pair = native_pair(
            resolve_mount(args.input_root),
            Path("docs/evaluation/qwen7b_upstream_inventory_v1.json"),
            args.guard_path,
            pin,
            args.output,
            args.attention_output,
            args.policy_output,
        )
        try:
            identity["environment"] = verify_gpu_environment()
            identity["snapshot_sha256"] = pin.sha256
            identity["progress_policy"] = "worker_thread_progress_v1"
            observer = PairCUDAObserver()
        except BaseException:
            pair.close()
            raise
    try:
        result = run(args.output, pair, observer, identity)
    finally:
        pair.close()
    print(
        f"ORDINARY_PAIR_COMPLETE execution_valid={result['execution_valid']} native_validated=False"
    )
    return 0 if result["execution_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
