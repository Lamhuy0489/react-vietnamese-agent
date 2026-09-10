#!/usr/bin/env python3
"""One packaged dispatcher: unchanged HF stress entry or explicitly synthetic rehearsal."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links


def invoke(main: Callable[[], int], arguments: list[str]) -> int:
    previous = sys.argv
    try:
        sys.argv = [previous[0], *arguments]
        return main()
    finally:
        sys.argv = previous


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("stub", "hf"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--policy-output", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--guard-path", type=Path)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    for path in (args.output, args.policy_output):
        no_links(path)
        if path.exists():
            raise ValueError("fresh output roots required")
    if args.output.resolve().is_relative_to(args.policy_output.resolve()) or (
        args.policy_output.resolve().is_relative_to(args.output.resolve())
    ):
        raise ValueError("separate output roots required")
    commit = os.environ.get("PAIR_SOURCE_COMMIT", "")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("exact source identity required")
    if args.backend == "hf":
        if args.guard_path is None or args.snapshot is None:
            raise ValueError("offline guard inputs required")
        from run_phase5_policy_stress_fixed import main as native

        return invoke(
            native,
            [
                "--output",
                str(args.output),
                "--policy-output",
                str(args.policy_output),
                "--input-root",
                str(args.input_root),
                "--guard-path",
                str(args.guard_path),
                "--snapshot",
                str(args.snapshot),
            ],
        )
    if args.guard_path is not None or args.snapshot is not None:
        raise ValueError("synthetic rehearsal cannot receive model inputs")
    from run_phase5_context_stress_worker import main as synthetic
    from run_phase5_policy_native_compat import run

    code = invoke(synthetic, ["--backend", "stub", "--output", str(args.output)])
    if code:
        return code
    run(args.policy_output, "stub", commit)
    print("POLICY_STRESS_STUB_COMPLETE native_model_calls=0 native_library_verified=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
