"""Independent read-only checkpoint/source audit for prospective v12 controls."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.room_control_pair_audit_v1 import audit_join
from react_agent.validation.room_ticket_native_release_v1 import admit_source

RUN_PROTOCOL = "phase5_room_control_native_task_v1"


def audit(
    output: Path,
    project: Path,
    source_manifest: Path,
    expected_source_sha256: str,
    source_commit: str,
    expected_identity: dict[str, Any],
) -> dict[str, Any]:
    before = inventory(output)
    admit_source(project, source_manifest, expected_source_sha256, source_commit)
    equal(read_record(output / "identity.json"), expected_identity, "control run identity")
    if not (output / "checkpoint.json").is_file():
        raise ValueError("partial control task has no checkpoint; manual triage required")
    checkpoint = read_record(output / "checkpoint.json")
    equal(checkpoint["protocol"], RUN_PROTOCOL, "control checkpoint protocol")
    equal(
        checkpoint["identity_sha256"],
        text_hash(canonical_json(expected_identity)),
        "control checkpoint identity",
    )
    raw = dict(before)
    raw.pop("checkpoint.json")
    equal(checkpoint["raw_sha256"], raw, "control immutable raw")
    joined = audit_join(
        output / "execution",
        output / "native/guard_response_diagnostics.jsonl",
        output / "witness.jsonl",
        expected_arm=expected_identity["arm"],
        expected_review_ref=expected_identity["review_ref"],
        expected_draft_sha256=expected_identity["draft_sha256"],
        expected_pin_sha256=expected_identity["pin_sha256"],
        expected_source_commit=source_commit,
    )
    equal(joined["valid"], True, "control paired join")
    equal(inventory(output), before, "control release audit read-only")
    return {
        "protocol": RUN_PROTOCOL,
        "arm": expected_identity["arm"],
        "valid": True,
        "terminal": checkpoint["terminal"],
        "source_tree_matches_external_pin": True,
        "native_model_authenticated": False,
        "joined": joined,
        "phase5_accepted": False,
    }
