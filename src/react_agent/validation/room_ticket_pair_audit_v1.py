"""Versioned read-only audit of the pinned prospective room-ticket route."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.room_ticket_pair_runtime_v1 import RUNTIME_VERSION
from react_agent.validation import clause_pair_audit_v1 as baseline
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record


def audit_task(output: Path, *, expected_pin_sha256: str) -> dict[str, Any]:
    before = inventory(output)
    result = cast(
        dict[str, Any], bind(baseline.audit_task, RUNTIME_VERSION=RUNTIME_VERSION)(output)
    )
    if result["runtime_present"]:
        metadata = read_record(output / "runtime/run_metadata.json")
        equal(metadata["runtime_version"], RUNTIME_VERSION, "room ticket runtime version")
        equal(
            metadata["prospective_inventory"]["pin_sha256"],
            expected_pin_sha256,
            "prospective run inventory pin",
        )
        equal(
            metadata["room_ticket_candidate"]["host_inventory_attested"],
            False,
            "no automatic human attestation",
        )
    equal(inventory(output), before, "room ticket task audit read-only")
    return result


def audit_join(
    execution: Path, sidecar: Path, witness: Path, *, expected_pin_sha256: str
) -> dict[str, Any]:
    def pinned_task(output: Path) -> dict[str, Any]:
        return audit_task(output, expected_pin_sha256=expected_pin_sha256)

    def pinned_exit(
        output: Path, *, expected_runtime: dict[str, str] | None = None
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            bind(baseline.audit_exit, audit_task=pinned_task)(
                output, expected_runtime=expected_runtime
            ),
        )

    result = bind(baseline.audit_join, audit_task=pinned_task, audit_exit=pinned_exit)(
        execution, sidecar, witness
    )
    return cast(dict[str, Any], {**result, "protocol": "room_ticket_pair_join_v1"})
