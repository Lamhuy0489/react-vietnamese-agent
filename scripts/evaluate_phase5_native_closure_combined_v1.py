"""Combine the immutable native closure epoch and its documented recovery epoch."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from evaluate_phase5_native_closure_v1 import CASES, LEVELS, evaluate

from react_agent.serving.structured_api_v1 import canonical

ROOT = Path(__file__).resolve().parents[1]
RECOVERY_CASES = CASES[3:]


def _index(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["condition"]["key"]: row for row in result["conditions"]}


def combine(epoch_one: Path, recovery: Path) -> dict[str, Any]:
    first = evaluate(epoch_one)
    second = evaluate(recovery, cases=RECOVERY_CASES)
    first_rows = _index(first)
    recovery_rows = _index(second)

    # Epoch one is authoritative only for C1-C3.  Its uncertain C4/A0 record
    # remains visible below as historical evidence, never as a completed row.
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for case in CASES:
        for level in LEVELS:
            key = f"{case}__{level}"
            source = first_rows if case in CASES[:3] else recovery_rows
            row = source.get(key)
            if row is None or row.get("status") != "completed" or row.get(
                "remote_delivery_uncertain"
            ):
                missing.append(key)
                continue
            rows.append(row)

    historical = first_rows.get("c4_email_private__A0")
    blocked_reasons: list[str] = []
    if missing:
        blocked_reasons.append("closure matrix is incomplete")
    if any(row.get("remote_delivery_uncertain") for row in first["conditions"]):
        blocked_reasons.append("epoch one contains an unresolved delivery record")
    if any(row.get("remote_delivery_uncertain") for row in second["conditions"]):
        blocked_reasons.append("recovery epoch contains an unresolved delivery record")
    if first["test_payloads_read"] or first["private_ground_truth_read"]:
        blocked_reasons.append("epoch one loaded forbidden evaluation data")
    if second["test_payloads_read"] or second["private_ground_truth_read"]:
        blocked_reasons.append("recovery epoch loaded forbidden evaluation data")

    return {
        "schema": "phase5_native_closure_combined_evaluation_v1",
        "scope": "native synthetic Dev C1-C12 crossed with A0-A6",
        "epoch_one": {
            "path": str(epoch_one),
            "completed_conditions": first["completed_conditions"],
            "missing": first["missing"],
            "artifact_hashes_verified": first["artifact_hashes_verified"],
        },
        "recovery_epoch": {
            "path": str(recovery),
            "scheduled_cases": list(RECOVERY_CASES),
            "completed_conditions": second["completed_conditions"],
            "missing": second["missing"],
            "artifact_hashes_verified": second["artifact_hashes_verified"],
        },
        "conditions": rows,
        "historical_excluded": historical,
        "expected_conditions": len(CASES) * len(LEVELS),
        "completed_conditions": len(rows),
        "missing": missing,
        "artifact_hashes_verified": first["artifact_hashes_verified"]
        + second["artifact_hashes_verified"],
        "test_payloads_read": first["test_payloads_read"] + second["test_payloads_read"],
        "private_ground_truth_read": first["private_ground_truth_read"]
        + second["private_ground_truth_read"],
        "blocked_reasons": blocked_reasons,
        "closure_matrix_complete": len(rows) == len(CASES) * len(LEVELS)
        and not blocked_reasons,
        # A complete native matrix is necessary evidence; the formal DoD
        # acceptance gate remains a separate review and is never inferred from
        # file presence or a single aggregate count.
        "phase5_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epoch-one", required=True, type=Path)
    parser.add_argument("--recovery", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = combine(args.epoch_one, args.recovery)
    args.output.write_text(canonical(result) + "\n", encoding="utf-8")
    print(
        canonical(
            {
                "completed": result["completed_conditions"],
                "missing": result["missing"],
                "blocked_reasons": result["blocked_reasons"],
            }
        )
    )


if __name__ == "__main__":
    main()
