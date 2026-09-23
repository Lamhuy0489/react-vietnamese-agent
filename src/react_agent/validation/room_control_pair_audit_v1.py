"""Read-only v12 control-arm join with prospective pin/arm identity."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from react_agent.validation.clause_pair_audit_v1 import audit_join as baseline_join
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record


def audit_join(
    execution: Path,
    sidecar: Path,
    witness: Path,
    *,
    expected_arm: str,
    expected_review_ref: str,
    expected_draft_sha256: str,
    expected_pin_sha256: str,
    expected_source_commit: str,
) -> dict[str, Any]:
    if expected_arm not in {"baseline", "metadata"}:
        raise ValueError("known prospective control arm required")
    before = inventory(execution)
    result = baseline_join(execution, sidecar, witness)
    equal(result["valid"], True, "v12 control pair join")
    metadata = read_record(execution / "runtime/run_metadata.json")
    equal(
        metadata["prospective_control"],
        {
            "arm": expected_arm,
            "review_ref": expected_review_ref,
            "draft_sha256": expected_draft_sha256,
            "pin_sha256": expected_pin_sha256,
            "source_commit": expected_source_commit,
            "metadata_enabled": expected_arm == "metadata",
            "host_inventory_attested": False,
            "source_authenticated_by_release_audit": False,
        },
        "prospective control identity",
    )
    equal(inventory(execution), before, "prospective control audit read-only")
    return {**result, "protocol": "room_control_pair_join_v1", "valid": True}
