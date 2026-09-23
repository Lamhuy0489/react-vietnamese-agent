"""Versioned three-arm prospective identity and matched-manifest checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

from pydantic import Field

from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation import clause_dev_release_v1 as source
from react_agent.validation import room_ticket_run_manifest_v1 as ticket
from react_agent.validation.context_stress_audit_v1 import equal

ARMS = frozenset({"baseline", "metadata", "ticket"})


class RoomProspectiveRunManifest(ticket.RoomTicketRunManifest):
    """One arm/condition; all three arms share every other frozen field."""

    protocol: Literal["phase5_room_prospective_run_manifest_v2"]  # type: ignore[assignment]
    arm: Literal["baseline", "metadata", "ticket"]  # type: ignore[assignment]
    comparison_id: str = Field(pattern=r"^room_[a-z0-9_]+$")


def admit_run(*args: Any, **kwargs: Any) -> tuple[Any, ...]:
    """Reuse v1 byte admission with the v2 schema, without weakening v1."""
    admitted = bind(ticket.admit_run, RoomTicketRunManifest=RoomProspectiveRunManifest)(
        *args, **kwargs
    )
    return cast(tuple[Any, ...], admitted)


def audit_triplet(paths: dict[str, tuple[Path, str]]) -> dict[str, Any]:
    """Read-only pairing check; no model output or evaluator oracle is read."""
    if set(paths) != ARMS:
        raise ValueError("exact baseline/metadata/ticket manifests required")
    frozen: dict[str, Any] | None = None
    identities = {}
    for arm in sorted(ARMS):
        path, expected_sha256 = paths[arm]
        equal(source.digest(path), expected_sha256, "external arm manifest pin")
        item = RoomProspectiveRunManifest.model_validate_json(path.read_bytes())
        equal(item.arm, arm, "prospective arm identity")
        values = item.model_dump(mode="json")
        values.pop("arm")
        if frozen is None:
            frozen = values
        else:
            equal(values, frozen, "matched three-arm inputs")
        identities[arm] = expected_sha256
    return {
        "protocol": "room_prospective_triplet_v2",
        "valid": True,
        "comparison_id": frozen["comparison_id"] if frozen else None,
        "manifest_sha256": identities,
        "model_runs": 0,
    }
