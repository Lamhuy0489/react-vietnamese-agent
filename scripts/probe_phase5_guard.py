#!/usr/bin/env python3
"""Run the frozen synthetic statelessness probe using stub or offline GPU guard."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from react_agent.llm.guard_hf_v1 import GuardHFConfig
from react_agent.llm.guard_probe_v1 import HFProbeTrials, StubProbeTrials, run_probe
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.security_v1.warm_guard import WarmGuardConfig


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("stub", "hf"), required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    commit = os.environ.get("FROZEN_GIT_COMMIT", "")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("frozen bundle source commit required")
    if args.backend == "hf":
        if args.model_path is None or args.snapshot is None:
            raise ValueError("pinned offline model and snapshot required")
        pin = GuardSnapshot.model_validate_json(args.snapshot.read_text())
        config = GuardHFConfig()
        trials = HFProbeTrials(args.model_path, pin, config, args.output)
        result = run_probe(
            args.output,
            trials,
            WarmGuardConfig(pin.model_id, pin.model_revision),
            {
                "backend": "hf",
                "source_commit": commit,
                "snapshot_sha256": pin.sha256,
                "adapter_config_sha256": config.sha256,
            },
        )
    else:
        result = run_probe(
            args.output,
            StubProbeTrials(),
            WarmGuardConfig("synthetic-probe-stub", "v1"),
            {
                "backend": "stub",
                "source_commit": commit,
            },
        )
    print(f"PROBE_COMPLETE valid={result['valid']} backend={args.backend}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
