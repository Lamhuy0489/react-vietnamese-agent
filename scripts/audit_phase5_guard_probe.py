#!/usr/bin/env python3
"""Audit a downloaded completed guard probe into a fresh, separate receipt."""

import argparse
from pathlib import Path

from react_agent.llm.guard_probe_v1 import write_json
from react_agent.validation.guard_probe_audit_v1 import audit_completed_probe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.raw.resolve()):
        raise ValueError("audit output must be outside immutable raw artifacts")
    result = audit_completed_probe(args.raw, args.bundle, args.preflight)
    write_json(args.output, result)
    print(f"INTEGRITY_PASS probe_valid={result['probe_valid']}")


if __name__ == "__main__":
    main()
