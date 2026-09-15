"""Read-only three-way join: runtime attempts, worker diagnostic, host response."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal, Self, TypeVar

from pydantic import Field, model_validator

from react_agent.foundation.artifacts import Immutable
from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.security_v1.guard_diagnostics_v1 import MAX_DIAGNOSTIC_CHARS
from react_agent.security_v1.guard_diagnostics_v2 import GuardDiagnosticV2
from react_agent.validation.pair_runtime_audit_v3 import audit_task


class Binding(Immutable):
    sequence: int = Field(strict=True, gt=0)
    worker_pid: int = Field(strict=True, gt=0)
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    generation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_identity_matches: bool = Field(strict=True)


class Sidecar(Binding):
    protocol: Literal["guard_response_sidecar_v2"]
    diagnostic: GuardDiagnosticV2

    @model_validator(mode="after")
    def consistent(self) -> Self:
        d = self.diagnostic
        b = d.baseline
        oversized = b.response_chars > MAX_DIAGNOSTIC_CHARS
        if (b.category == "size") != oversized or b.parser_checked == oversized:
            raise ValueError("size/parser consistency required")
        if (d.framing == "not_inspected") != oversized:
            raise ValueError("inspection consistency required")
        if b.category == "schema":
            if (
                not b.issues
                or tuple(sorted(set(b.issues), key=lambda i: (i.field, i.kind))) != b.issues
            ):
                raise ValueError("canonical schema issues required")
        elif b.issues:
            raise ValueError("schema issues on non-schema category")
        if b.response_chars == 0 and d.framing != "empty":
            raise ValueError("empty response framing required")
        if b.category == "valid" and (d.framing != "object" or d.terminal_fence):
            raise ValueError("valid guard object framing required")
        if d.framing in {"empty", "not_inspected"} and d.terminal_fence:
            raise ValueError("impossible terminal fence")
        if b.category == "json_syntax":
            if (
                d.syntax_kind == "none"
                or d.error_offset is None
                or d.error_at_end is None
                or d.trailing_comma_at_error is None
                or d.error_offset > b.response_chars
                or d.error_at_end != (d.error_offset == b.response_chars)
                or (d.trailing_comma_at_error and d.error_at_end)
            ):
                raise ValueError("syntax diagnostic consistency required")
        elif (
            d.syntax_kind != "none"
            or d.error_offset is not None
            or d.error_at_end is not None
            or d.trailing_comma_at_error is not None
        ):
            raise ValueError("syntax fields on non-syntax category")
        return self


class Witness(Binding):
    protocol: Literal["guard_response_witness_v2"]
    host_pid: int = Field(strict=True, gt=0)
    worker_sequence: int = Field(strict=True, gt=0)
    response_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_chars: int = Field(strict=True, ge=0)


Record = TypeVar("Record", bound=Immutable)


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate audit key")
        result[key] = value
    return result


def _records(payload: bytes, model: type[Record]) -> list[Record]:
    try:
        records = []
        for line in payload.splitlines():
            json.loads(line, object_pairs_hook=_pairs)
            records.append(model.model_validate_json(line, strict=True))
        return records
    except (ValueError, RecursionError):
        # ValidationError includes input values; never let it reach audit logs.
        raise ValueError("invalid diagnostic record") from None


def audit(execution: Path, sidecar: Path, witness: Path) -> dict[str, Any]:
    """No model/text replay. Shape checks cannot prove exact syntax hints from hashes."""
    for path in (execution, sidecar, witness):
        no_links(path)
    if sidecar.resolve() == witness.resolve():
        raise ValueError("independent observer files required")
    before = inventory(execution)
    payloads = [p.read_bytes() if p.exists() else b"" for p in (sidecar, witness)]
    audit_task(execution)
    receipt = json.loads((execution / "pair_runtime.json").read_text())
    workers = receipt["snapshot"]["workers"]
    if "guard" not in workers:
        raise ValueError("guard-enabled runtime required")
    records = _records(payloads[0], Sidecar)
    witnesses = _records(payloads[1], Witness)
    attempts = [a for a in workers["guard"]["attempts"][1:] if a["status"] == "OK"]
    if not len(records) == len(witnesses) == len(attempts):
        raise ValueError("one worker and host record per returned response required")
    trace_path = execution / "runtime/trace_guard.jsonl"
    traces = (
        [json.loads(line) for line in trace_path.read_text().splitlines()]
        if trace_path.exists()
        else []
    )
    joined = []
    for sequence, (record, host, attempt) in enumerate(
        zip(records, witnesses, attempts, strict=True), 1
    ):
        for item in (record, host):
            if (
                item.sequence != sequence
                or item.worker_pid != attempt["pid"]
                or item.request_sha256 != attempt["request_sha256"]
                or item.generation_sha256 != attempt["generation_sha256"]
            ):
                raise ValueError("diagnostic worker/request/sequence binding mismatch")
        baseline = record.diagnostic.baseline
        if (
            host.host_pid != receipt["owner_pid"]
            or host.worker_sequence != attempt["sequence"]
            or host.response_sha256 != baseline.response_sha256
            or host.response_chars != baseline.response_chars
            or host.response_identity_matches != record.response_identity_matches
        ):
            raise ValueError("host response witness mismatch")
        matches = [
            t
            for t in traces
            if any(
                a["sequence"] == attempt["sequence"] and a["pid"] == attempt["pid"]
                for a in t["execution_attempts"]
            )
        ]
        if len(matches) != 1:
            raise ValueError("one classification per returned response required")
        outcome = matches[0]["outcome"]
        expected: tuple[str, str | None]
        if not host.response_identity_matches:
            expected = ("ERROR", "IDENTITY_CHANGED")
        elif baseline.category == "valid":
            expected = ("OK", None)
        elif baseline.parser_checked and baseline.category != "depth":
            expected = ("ERROR", "INVALID_OUTPUT")
        else:
            expected = (outcome["status"], outcome["error_code"])
        if (outcome["status"], outcome["error_code"]) != expected:
            raise ValueError("diagnostic category contradicts guard outcome")
        joined.append(
            dict(
                sequence=sequence,
                stage=matches[0]["stage"],
                classification_status=outcome["status"],
                diagnostic=record.diagnostic.model_dump(mode="json"),
            )
        )
    if inventory(execution) != before or payloads != [
        p.read_bytes() if p.exists() else b"" for p in (sidecar, witness)
    ]:
        raise ValueError("diagnostic audit input changed")
    return dict(
        protocol="guard_diagnostic_join_v2",
        valid=True,
        response_records=len(records),
        joined=joined,
        runtime_sha256=before,
        sidecar_sha256=hashlib.sha256(payloads[0]).hexdigest(),
        witness_sha256=hashlib.sha256(payloads[1]).hexdigest(),
        response_hash_cross_checked=True,
        syntax_hints_rederived=False,
        native_model_authenticated=False,
        guard_quality_validated=False,
    )
