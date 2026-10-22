#!/usr/bin/env python3
"""Emit a read-only Phase 5 20-DoD CPU/native readiness report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.validation.phase5_gate_readiness_v1 import GateAuditError, audit

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-pilot", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise GateAuditError("output already exists; preserve prior readiness evidence")
    if output.is_relative_to(ROOT / "data"):
        raise GateAuditError("readiness output cannot overlap frozen data")
    report = audit(ROOT, api_pilot=args.api_pilot)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "phase5_accepted": report["phase5_accepted"],
        "cpu_evidence_count": report["cpu_evidence_count"],
        "diagnostic_only_count": report["diagnostic_only_count"],
        "missing_cpu_evidence_count": report["missing_cpu_evidence_count"],
        "test_payloads_read": report["test_payloads_read"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

