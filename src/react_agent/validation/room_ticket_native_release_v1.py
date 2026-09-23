"""Independent read-only source and task audit for the room-ticket native route.

An externally supplied source-manifest hash is mandatory. Exact source bytes
are checked here, but model publisher and remote notebook identity remain
separate release gates; this module never asserts either automatically.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation import clause_dev_release_v1 as source
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.room_ticket_pair_audit_v1 import audit_join

SOURCE_PROTOCOL = "phase5_room_ticket_source_v1"
RUN_PROTOCOL = "phase5_room_ticket_native_task_v1"
REQUIRED = {
    "src/react_agent/security_v1/room_ticket_pair_runtime_v1.py",
    "src/react_agent/security_v1/room_control_pair_runtime_v1.py",
    "src/react_agent/security_v1/public_field_ticket_policy_v2.py",
    "src/react_agent/validation/room_inventory_review_v1.py",
    "src/react_agent/validation/room_ticket_pair_audit_v1.py",
    "src/react_agent/validation/room_ticket_native_release_v1.py",
    "src/react_agent/validation/room_ticket_run_manifest_v1.py",
    "src/react_agent/validation/room_prospective_run_manifest_v2.py",
    "src/react_agent/validation/room_control_pair_audit_v1.py",
    "src/react_agent/validation/room_control_native_release_v1.py",
    "src/react_agent/llm/room_ticket_native_dispatch_v1.py",
    "src/react_agent/llm/room_control_native_dispatch_v1.py",
    "scripts/run_phase5_room_ticket_native_v1.py",
    "scripts/run_phase5_room_prospective_native_v2.py",
}


def admit_source(
    project: Path, manifest: Path, expected_sha256: str, commit: str
) -> dict[str, Any]:
    """Require exact committed public bytes before native execution or audit."""
    admitted = bind(source.admit, PROTOCOL=SOURCE_PROTOCOL)(
        project, manifest, expected_sha256, commit, native=True
    )
    files = admitted["source_sha256"]
    if not REQUIRED <= files.keys() or any(
        name.startswith("src/react_agent/authoring/") for name in files
    ):
        raise ValueError("room-ticket source closure is missing or non-public")
    return dict(admitted)


def audit(
    output: Path,
    project: Path,
    source_manifest: Path,
    expected_source_sha256: str,
    source_commit: str,
    expected_identity: dict[str, Any],
) -> dict[str, Any]:
    """Read-only task/source audit; partial tasks cannot be silently resumed."""
    before = inventory(output)
    admit_source(project, source_manifest, expected_source_sha256, source_commit)
    equal(read_record(output / "identity.json"), expected_identity, "room-ticket run identity")
    if not (output / "checkpoint.json").is_file():
        raise ValueError("partial room-ticket task has no checkpoint; manual triage required")
    checkpoint = read_record(output / "checkpoint.json")
    equal(checkpoint["protocol"], RUN_PROTOCOL, "room-ticket checkpoint protocol")
    equal(
        checkpoint["identity_sha256"],
        text_hash(canonical_json(expected_identity)),
        "room-ticket checkpoint identity",
    )
    raw = dict(before)
    raw.pop("checkpoint.json")
    equal(checkpoint["raw_sha256"], raw, "room-ticket immutable raw")
    execution = output / "execution"
    joined = audit_join(
        execution,
        output / "native/guard_response_diagnostics.jsonl",
        output / "witness.jsonl",
        expected_pin_sha256=expected_identity["pin_sha256"],
    )
    equal(joined["valid"], True, "room-ticket pair join")
    metadata = read_record(execution / "runtime/run_metadata.json")
    equal(
        metadata["prospective_inventory"]["source_commit"],
        source_commit,
        "room-ticket runtime source",
    )
    equal(inventory(output), before, "room-ticket audit read-only")
    return {
        "protocol": RUN_PROTOCOL,
        "valid": True,
        "terminal": checkpoint["terminal"],
        "source_tree_matches_external_pin": True,
        "native_model_authenticated": False,
        "joined": joined,
        "phase5_accepted": False,
    }
