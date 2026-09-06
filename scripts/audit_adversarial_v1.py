#!/usr/bin/env python3
"""Audit the preserved draft. Exit 1 means NOT ACCEPTED, not an infrastructure failure."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from react_agent.validation.adversarial_audit import audit

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "data/adversarial/v1")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and (
        args.output.exists() or args.output.resolve().is_relative_to(args.root.resolve())
    ):
        raise ValueError("audit output must be fresh and outside benchmark inputs")
    report = audit(args.root)
    report["auditor_sha256"] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in (
            "scripts/audit_adversarial_v1.py",
            "src/react_agent/validation/adversarial_v1.py",
            "src/react_agent/validation/adversarial_audit.py",
        )
    }
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(output)
    print(output, end="")
    return 1  # v1 diagnostic only; cannot substitute for semantic/executable acceptance.


if __name__ == "__main__":
    raise SystemExit(main())
