"""Versioned synthetic guard diagnostic; HF requires explicit prepared Kaggle mounts."""

import argparse
import os
from pathlib import Path

from react_agent.llm.agent_mount_v1 import resolve_mount
from react_agent.llm.guard_observer_probe_v2 import run
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import verify_gpu_environment
from react_agent.llm.model_pair_probe_v1 import PairCUDAObserver, SyntheticPairObserver


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("stub", "hf"), default="stub")
    parser.add_argument("--condition", choices=("valid", "trailing_comma"), default="valid")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--guard-path", type=Path)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    if args.backend == "hf":
        if args.guard_path is None or args.snapshot is None or args.condition != "valid":
            raise ValueError("native mounts required; output injection forbidden")
        verify_gpu_environment()
        result = run(
            args.output,
            Path("data/clean/v1_1/environment"),
            backend="hf",
            commit=os.environ.get("PAIR_SOURCE_COMMIT", ""),
            observer_factory=PairCUDAObserver,
            resume=args.resume,
            agent=resolve_mount(args.input_root),
            model_inventory=Path("docs/evaluation/qwen7b_upstream_inventory_v1.json"),
            guard=args.guard_path,
            snapshot=GuardSnapshot.model_validate_json(args.snapshot.read_text()),
        )
    else:
        if args.guard_path is not None or args.snapshot is not None:
            raise ValueError("native options forbidden in stub mode")
        result = run(
            args.output,
            Path("data/clean/v1_1/environment"),
            backend="stub",
            commit=os.environ.get("PAIR_SOURCE_COMMIT", ""),
            condition=args.condition,
            observer_factory=SyntheticPairObserver,
            resume=args.resume,
        )
    print(result, flush=True)


if __name__ == "__main__":
    main()
