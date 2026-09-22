"""Dev32 checkpoint integrity plus candidate constraint/origin/exit joins."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation import grouped_dev_checkpoint_v2 as baseline
from react_agent.validation.clause_pair_audit_v1 import audit_join, audit_task
from react_agent.validation.context_stress_audit_v1 import equal
from react_agent.validation.exit_pair_audit_v1 import checked_runtime


def audit_checkpoint(root: Path, identity: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    if identity.get("protocol") != "clause_dev32_v1" or task not in identity["tasks"]:
        raise ValueError("candidate task and identity required")
    equal(identity["expected_tasks"], 32, "candidate task count")
    runtime = checked_runtime(identity["exit_observer"]["runtime"])

    def guard(execution: Path, sidecar: Path) -> dict[str, Any]:
        return audit_join(execution, sidecar, root / "witness.jsonl", expected_runtime=runtime)

    return cast(
        dict[str, Any],
        bind(baseline.audit_checkpoint, audit_task=audit_task, audit_guard=guard)(
            root, identity, task
        ),
    )


def audit_prefix(output: Path, identity: dict[str, Any], shard: int) -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        bind(baseline.audit_prefix, audit_checkpoint=audit_checkpoint)(
            output,
            identity,
            shard,
        ),
    )
