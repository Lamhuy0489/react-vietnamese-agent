"""Join constrained guard tokens to existing native policy/attention/timing audits."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from react_agent.llm.constrained_probe_v1 import (
    audit_join,
    checkpoint,
    execution_sources,
    fixed_identity,
)
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_v1 import Role
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation import observer_native_audit_v2 as original
from react_agent.validation.context_stress_audit_v1 import equal
from react_agent.validation.guard_probe_audit_v2 import require


def role_evidence(
    root: Path,
    role: Role,
    worker: dict[str, Any],
    identity: dict[str, Any],
    tokenizers: Path,
    publishers: Path,
    pin: GuardSnapshot,
    totals: list[int],
) -> dict[str, Any]:
    result = original.role_evidence(
        root, role, worker, identity, tokenizers, publishers, pin, totals
    )
    if role != "guard":
        return result
    joined = audit_join(
        root / "execution", root / "native/guard_response_diagnostics.jsonl", root / "witness.jsonl"
    )
    compared = []
    if result["policy_attention_verified"]:
        require(not joined["incomplete"], "complete native role cannot contain partial constraints")
        require(len(result["calls"]) == len(joined["completed"]), "one constraint per native call")
        for call, constraint in zip(result["calls"], joined["completed"], strict=True):
            equal(call["index"], constraint["request_index"], "constraint/native request index")
            for key in ("input_tokens", "output_tokens"):
                equal(call[key], constraint[key], "constraint/native " + key)
            compared.append(
                dict(
                    request_index=call["index"],
                    input_tokens=call["input_tokens"],
                    output_tokens=call["output_tokens"],
                )
            )
    else:
        require(not result["calls"], "partial role cannot contribute native timing denominators")
    return dict(
        result,
        constrained_native_counts_verified=result["policy_attention_verified"],
        constraint_calls=compared,
        incomplete_constraint_requests=len(joined["incomplete"]),
    )


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
        original.audit,
        checkpoint=checkpoint,
        execution_sources=execution_sources,
        fixed_identity=fixed_identity,
        role_evidence=role_evidence,
        audit_guard=audit_join,
    )
    result = cast(
        dict[str, Any],
        body(probe, tokenizers, publishers, pin, commit, model_inventory, environment),
    )
    result["protocol"] = "constrained_native_audit_v1"
    return result
