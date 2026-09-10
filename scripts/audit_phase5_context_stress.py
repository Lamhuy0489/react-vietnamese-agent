#!/usr/bin/env python3
"""Audit complete paired stress records; does not authenticate a Kaggle release."""

from __future__ import annotations

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.context_stress_audit_v1 import audit_probe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.probe, args.snapshot, args.output):
        no_links(path)
    if args.output.exists() or args.output.resolve().is_relative_to(args.probe.resolve()):
        raise ValueError("fresh audit output outside immutable probe required")
    pin = GuardSnapshot.model_validate_json(args.snapshot.read_text())
    result = audit_probe(args.probe, pin, args.source_commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("CONTEXT_STRESS_ARTIFACT_AUDIT_COMPLETE source_authenticated=False phase5_accepted=False")


if __name__ == "__main__":
    main()
