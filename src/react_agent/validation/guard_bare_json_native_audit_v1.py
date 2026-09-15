"""Authenticate candidate native metrics and checkpoints using frozen audit bodies."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from react_agent.llm.guard_bare_json_probe_v1 import (
    checkpoint,
    execution_sources,
    fixed_identity,
)
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation.guard_bare_json_audit_v1 import audit_join
from react_agent.validation.observer_native_audit_v2 import audit as original


def audit(
    probe: Path,
    tokenizers: Path,
    publishers: Path,
    pin: GuardSnapshot,
    commit: str,
    model_inventory: Path,
    environment: Path,
) -> dict[str, Any]:
    body = bind(
        original,
        checkpoint=checkpoint,
        execution_sources=execution_sources,
        fixed_identity=fixed_identity,
        audit_guard=audit_join,
    )
    result = cast(
        dict[str, Any],
        body(probe, tokenizers, publishers, pin, commit, model_inventory, environment),
    )
    result["protocol"] = "guard_bare_json_native_audit_v1"
    return result
