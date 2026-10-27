"""Externally pinned raw-doc proof audit; reuses frozen raw replay, not its scope."""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.security_v1.doc_read_final_proof_v1 import DocReadApproval, validate_catalog
from react_agent.security_v1.doc_read_final_runtime_v1 import (
    FINAL_PROFILE,
    RUNTIME_VERSION,
    DocReadFinalGate,
)
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation import final_literal_runtime_audit_v1 as previous
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record


def audit_runtime(
    output: Path, *, approval: DocReadApproval, expected_approval_sha256: str,
) -> dict[str, Any]:
    before = inventory(output)
    meta = read_record(output / "run_metadata.json")
    validate_catalog(approval, expected_approval_sha256,
                     SourceCatalog.model_validate(meta["source_catalog"]))
    receipt = read_record(output / "final_literal_gate.json")
    equal({k: v for k, v in receipt.items() if k != "records"}, dict(
        profile=FINAL_PROFILE, runtime_version=RUNTIME_VERSION,
        tool_policy_profile="clause_a6_v12", public_field_runtime_enabled=True,
        public_final_approval=approval.model_dump(mode="json"),
        expected_approval_sha256=expected_approval_sha256, native_admitted=False,
    ), "externally pinned doc_read final scope")

    def read_replay_record(path: Path) -> dict[str, Any]:
        value = read_record(path)
        if path == output / "final_literal_gate.json":
            # Scope was checked above against the EXTERNAL approval. Only adapt
            # the legacy auditor's header shape in memory; never rewrite files
            # or conceal any proof/decision/index field from its replay.
            value.pop("public_final_approval")
            value.pop("expected_approval_sha256")
            value["public_field_runtime_enabled"] = False
        return value

    body = bind(
        previous.audit_runtime, RUNTIME_VERSION=RUNTIME_VERSION,
        ROOM_RUNTIME_VERSION="unsupported_doc_read_room_route",
        FINAL_PROFILE=FINAL_PROFILE, read_record=read_replay_record,
        FinalLiteralGate=partial(DocReadFinalGate, approval, expected_approval_sha256),
    )
    result = cast(dict[str, Any], body(output))
    equal(inventory(output), before, "doc_read audit is read-only")
    return {**result, "protocol": "doc_read_final_runtime_audit_v1",
            "approval_sha256": expected_approval_sha256, "public_field_runtime_enabled": True}
