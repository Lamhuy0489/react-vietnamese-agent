#!/usr/bin/env python3
"""Run predeclared residency/cancellation trials without model text generation."""

import argparse
import functools
import os
from pathlib import Path

from react_agent.llm.guard_cancellation_v1 import (
    CUDAObserver,
    ResidentFactory,
    StubObserver,
    run_cancellation,
)
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.security_v1.warm_guard import WarmGuardConfig


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("stub", "hf"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--model-path", type=Path)
    args = parser.parse_args()
    commit = os.environ.get("CANCELLATION_SOURCE_COMMIT", "")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("frozen overlay source required")
    if args.backend == "hf":
        if args.snapshot is None or args.model_path is None:
            raise ValueError("offline snapshot and model required")
        pin = GuardSnapshot.model_validate_json(args.snapshot.read_text())
        result = run_cancellation(
            args.output,
            functools.partial(ResidentFactory, snapshot=pin, model_path=args.model_path),
            CUDAObserver(),
            WarmGuardConfig(pin.model_id, pin.model_revision),
            {"backend": "hf", "source_commit": commit, "snapshot_sha256": pin.sha256},
        )
    else:
        result = run_cancellation(
            args.output,
            ResidentFactory,
            StubObserver(),
            WarmGuardConfig("synthetic-resident-stub", "v1", timeout_seconds=2),
            {"backend": "stub", "source_commit": commit},
        )
    print(f"CANCELLATION_COMPLETE backend={args.backend} valid={result['valid']}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
