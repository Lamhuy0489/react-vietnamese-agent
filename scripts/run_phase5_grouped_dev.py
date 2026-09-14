"""Grouped public Dev shard; HF mode requires an explicit GPU worker and pinned mounts."""

import argparse
import json
import os
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, resolve_mount
from react_agent.llm.grouped_dev_runner_v2 import run
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import verify_gpu_environment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("stub", "hf"), default="stub")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shard", type=int, choices=range(8), required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-new-tasks", type=int)
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--guard-path", type=Path)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    native = {}
    if args.backend == "hf":
        if args.guard_path is None or args.snapshot is None:
            raise ValueError("explicit guard and snapshot required")
        no_links(args.snapshot)
        verify_gpu_environment()
        native = dict(
            agent=resolve_mount(args.input_root),
            guard=args.guard_path,
            model_inventory=Path("docs/evaluation/qwen7b_upstream_inventory_v1.json"),
            snapshot=GuardSnapshot.model_validate_json(args.snapshot.read_text()),
        )
    elif args.guard_path is not None or args.snapshot is not None:
        raise ValueError("native options forbidden in stub mode")
    result = run(
        args.output,
        Path("data/adversarial/release_v2"),
        Path("data/clean/v1_1/environment"),
        commit=os.environ.get("PAIR_SOURCE_COMMIT", ""),
        shard=args.shard,
        backend=args.backend,
        resume=args.resume,
        max_new_tasks=args.max_new_tasks,
        **native,
    )
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
