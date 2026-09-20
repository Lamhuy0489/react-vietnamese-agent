"""Join exit roles to constrained native policy/timing without weakening native checks."""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, cast

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.exit_pair_probe_v1 import checkpoint, execution_sources, fixed_identity
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation import constrained_native_audit_v1 as baseline
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.exit_pair_audit_v1 import audit_exit, audit_join, checked_runtime


def constraint_join(
    execution: Path, sidecar: Path, witness: Path, *, expected_runtime: dict[str, str] | None = None
) -> dict[str, Any]:
    # The combined join validates both; the legacy native body consumes the
    # unchanged constrained subsection with completed/incomplete token evidence.
    return cast(
        dict[str, Any],
        audit_join(execution, sidecar, witness, expected_runtime=expected_runtime)["constrained"],
    )


def role_evidence(
    *args: Any, expected_runtime: dict[str, str] | None = None, **kwargs: Any
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        bind(
            baseline.role_evidence,
            audit_join=partial(constraint_join, expected_runtime=expected_runtime),
        )(*args, **kwargs),
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
    for path in (probe, tokenizers, publishers, model_inventory, environment):
        no_links(path)
    before = inventory(probe)
    identity = read_record(probe / "identity.json")
    observer = identity.get("exit_observer")
    runtime = checked_runtime(observer.get("runtime") if type(observer) is dict else None)
    result = cast(
        dict[str, Any],
        bind(
            baseline.audit,
            checkpoint=partial(checkpoint, expected_runtime=runtime),
            execution_sources=execution_sources,
            fixed_identity=bind(fixed_identity, runtime_identity=lambda: runtime),
            role_evidence=partial(role_evidence, expected_runtime=runtime),
            audit_join=partial(constraint_join, expected_runtime=runtime),
        )(probe, tokenizers, publishers, pin, commit, model_inventory, environment),
    )
    for task in result["tasks"]:
        task["exit_milestones"] = audit_exit(
            probe / "tasks" / task["key"] / "execution", expected_runtime=runtime
        )
    equal(inventory(probe), before, "native exit join is read-only")
    result.update(
        protocol="exit_constrained_native_audit_v1",
        native_cause_identified=False,
        interpreter_identity_source="recorded run identity; remote authentication is separate",
        phase5_accepted=False,
    )
    return result
