"""Join structural sidecars with authenticated runtime worker/guard attempts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from react_agent.foundation.artifacts import Immutable
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.security_v1.guard_diagnostics_v1 import GuardDiagnostic
from react_agent.validation.pair_runtime_audit_v3 import audit_task


class Sidecar(Immutable):
    protocol: Literal["guard_response_sidecar_v1"]
    sequence: int = Field(strict=True, gt=0)
    worker_pid: int = Field(strict=True, gt=0)
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    generation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_identity_matches: bool = Field(strict=True)
    diagnostic: GuardDiagnostic


def audit(execution: Path, sidecar: Path) -> dict[str, Any]:
    """Read only. Failed or absent classifications do not become successful paths."""
    from react_agent.llm.agent_mount_v1 import no_links

    no_links(sidecar)
    before = inventory(execution)
    audit_task(execution)
    receipt = json.loads((execution / "pair_runtime.json").read_text())
    workers = receipt["snapshot"]["workers"]
    if "guard" not in workers:
        raise ValueError("guard-enabled runtime required")
    payload = sidecar.read_bytes() if sidecar.exists() else b""
    records = [Sidecar.model_validate_json(line) for line in payload.splitlines()]
    attempts = [a for a in workers["guard"]["attempts"][1:] if a["status"] == "OK"]
    if len(records) != len(attempts):
        raise ValueError("one sidecar per returned guard response required")
    trace_path = execution / "runtime/trace_guard.jsonl"
    traces = (
        [json.loads(line) for line in trace_path.read_text().splitlines()]
        if trace_path.exists()
        else []
    )
    joined = []
    for sequence, (record, attempt) in enumerate(zip(records, attempts, strict=True), 1):
        if (
            record.sequence != sequence
            or record.worker_pid != attempt["pid"]
            or record.request_sha256 != attempt["request_sha256"]
            or record.generation_sha256 != attempt["generation_sha256"]
        ):
            raise ValueError("diagnostic worker/request/sequence binding mismatch")
        matches = [
            t
            for t in traces
            if any(
                a["sequence"] == attempt["sequence"] and a["pid"] == attempt["pid"]
                for a in t["execution_attempts"]
            )
        ]
        if len(matches) != 1:
            raise ValueError("one guard classification per returned response required")
        outcome = matches[0]["outcome"]
        category = record.diagnostic.category
        if not record.response_identity_matches:
            expected_status, expected_error = "ERROR", "IDENTITY_CHANGED"
        elif category == "valid":
            expected_status, expected_error = "OK", None
        elif record.diagnostic.parser_checked and category != "depth":
            expected_status, expected_error = "ERROR", "INVALID_OUTPUT"
        else:
            # Depth/size limits alone cannot assert the frozen parser's outcome.
            expected_status, expected_error = outcome["status"], outcome["error_code"]
        if (outcome["status"], outcome["error_code"]) != (expected_status, expected_error):
            raise ValueError("diagnostic category contradicts guard outcome")
        joined.append(
            dict(
                sequence=sequence,
                stage=matches[0]["stage"],
                classification_status=outcome["status"],
                diagnostic=record.diagnostic.model_dump(mode="json"),
            )
        )
    if (
        inventory(execution) != before
        or (sidecar.read_bytes() if sidecar.exists() else b"") != payload
    ):
        raise ValueError("diagnostic audit input changed")
    import hashlib

    return dict(
        protocol="guard_diagnostic_join_v1",
        valid=True,
        response_records=len(records),
        joined=joined,
        sidecar_sha256=hashlib.sha256(payload).hexdigest(),
        runtime_sha256=before,
        native_model_authenticated=False,
        guard_quality_validated=False,
    )
