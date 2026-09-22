"""Dev32 native artifact adapter; publisher/source authentication stays a release gate."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation import grouped_dev_native_audit_v2 as baseline
from react_agent.validation.clause_dev_checkpoint_v1 import audit_checkpoint, audit_prefix
from react_agent.validation.clause_pair_audit_v1 import audit_join
from react_agent.validation.context_stress_audit_v1 import equal, inventory
from react_agent.validation.exit_pair_audit_v1 import checked_runtime


def audit_native_task(
    root: Path,
    identity: dict[str, Any],
    task: dict[str, Any],
    tokenizers: Path,
    publishers: Path,
    pin: GuardSnapshot,
) -> dict[str, Any]:
    before = inventory(root)
    if identity.get("protocol") != "clause_dev32_v1" or task["level"] not in {"A2", "A6"}:
        raise ValueError("paired candidate native identity required")
    runtime = checked_runtime(identity["exit_observer"]["runtime"])

    def joined(execution: Path, sidecar: Path) -> dict[str, Any]:
        return audit_join(execution, sidecar, root / "witness.jsonl", expected_runtime=runtime)

    result = bind(
        baseline.audit_native_task, audit_checkpoint=audit_checkpoint, audit_guard=joined
    )(
        root,
        identity,
        task,
        tokenizers,
        publishers,
        pin,
    )
    constraint = result["guard_diagnostics"]["constrained"]
    guard = result["roles"]["guard"]
    if guard["policy_attention_verified"]:
        equal(constraint["incomplete"], [], "verified guard cannot have incomplete constraints")
        equal(len(guard["calls"]), len(constraint["completed"]), "native constraint call count")
        for call, receipt in zip(guard["calls"], constraint["completed"], strict=True):
            equal(call["index"], receipt["request_index"], "native constraint request index")
            for field in ("input_tokens", "output_tokens"):
                equal(call[field], receipt[field], "native constraint " + field)
    elif guard["calls"]:
        raise ValueError("unverified native calls cannot enter timing denominators")
    equal(inventory(root), before, "native candidate audit read-only")
    return cast(
        dict[str, Any],
        {
            **result,
            "constrained_counts_verified": guard["policy_attention_verified"],
            "native_model_source_authenticated": False,
        },
    )


def audit(
    output: Path,
    identity: dict[str, Any],
    shard: int,
    tokenizers: Path,
    publishers: Path,
    pin: GuardSnapshot,
) -> dict[str, Any]:
    if identity.get("protocol") != "clause_dev32_v1" or identity.get("backend") != "hf":
        raise ValueError("candidate native identity required")
    result = bind(baseline.audit, audit_prefix=audit_prefix, audit_native_task=audit_native_task)(
        output,
        identity,
        shard,
        tokenizers,
        publishers,
        pin,
    )
    return cast(
        dict[str, Any],
        {
            **result,
            "protocol": "clause_dev32_native_audit_v1",
            "expected": 4,
            "complete": result["completed"] == 4,
        },
    )
