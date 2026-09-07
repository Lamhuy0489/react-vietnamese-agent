#!/usr/bin/env python3
"""Assemble selected evidence, seal after committing, or check integrity without Test parsing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.authoring.release_v2 import assemble, seal, validate_integration, verify_seal

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=ROOT / "data/adversarial/release_v2")
    parser.add_argument(
        "--action", choices=("assemble", "validate", "seal", "check"), required=True
    )
    args = parser.parse_args()
    if (args.release / "seal.json").exists() and args.action != "check":
        raise ValueError("sealed release permits hash-only checks, not authoring/reference replay")
    function = {
        "assemble": assemble,
        "validate": validate_integration,
        "seal": seal,
        "check": verify_seal,
    }[args.action]
    result = function(ROOT, args.release)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "valid",
                    "release_integration_accepted",
                    "phase3_accepted",
                    "test_sealed",
                    "variants",
                    "reused_reference_paths",
                    "fresh_replay_runs",
                    "mode",
                )
                if k in result
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
