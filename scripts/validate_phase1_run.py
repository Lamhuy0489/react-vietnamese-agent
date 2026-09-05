#!/usr/bin/env python3
"""Validate terminal state and trace integrity of a Phase 1 run directory."""

from __future__ import annotations

import argparse
from pathlib import Path

from react_agent.validation.phase1_run import validate_phase1_run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    result = validate_phase1_run(args.run_directory)
    if not result["valid"]:
        for failure in result["failures"]:
            print(f"FAIL: {failure}")
        return 1
    print(
        f"PASS: {result['runs']} unique task runs, {result['trace_events']} schema-valid events, "
        "valid terminal boundaries/tool payloads/order and trace-derived summary"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
