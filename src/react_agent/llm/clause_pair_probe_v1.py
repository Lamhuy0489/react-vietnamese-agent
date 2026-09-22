"""Candidate-specific host probe identity/checkpoints over unchanged paired workers."""

from __future__ import annotations

import hashlib
from functools import partial
from pathlib import Path
from typing import Any, cast

from react_agent.llm import exit_pair_probe_v1 as previous
from react_agent.llm import guard_observer_probe_v2 as baseline
from react_agent.llm.agent_mount_v1 import no_links
from react_agent.security_v1.authorization_anchors_v3 import PROFILE as ANCHORS
from react_agent.security_v1.clause_pair_runtime_v1 import (
    RUNTIME_VERSION,
    run_pair_task,
    run_synthetic_pair_task,
)
from react_agent.security_v1.exit_milestones_v1 import runtime_identity
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.processing_scope_v5 import PROFILE as SCOPE
from react_agent.security_v1.value_origin_v3 import PROFILE as ORIGIN
from react_agent.validation.clause_pair_audit_v1 import audit_join
from react_agent.validation.context_stress_audit_v1 import inventory
from react_agent.validation.exit_pair_audit_v1 import checked_runtime

PROFILE = "clause_constrained_exit_probe_v1"
SCHEDULE = previous.SCHEDULE


def execution_sources() -> dict[str, str]:
    source = Path(__file__).resolve().parents[1]
    names = (
        "llm/clause_pair_probe_v1.py",
        "security_v1/clause_pair_runtime_v1.py",
        "validation/clause_pair_audit_v1.py",
        "security_v1/runtime_v12.py",
        "security_v1/authorization_anchors_v3.py",
        "security_v1/value_origin_v3.py",
        "security_v1/processing_scope_v5.py",
        "security_v1/resource_bindings_v1.py",
        "security_v1/sql_rows_v1.py",
        "security_v1/runtime_v10.py",
    )
    return {
        **previous.execution_sources(),
        **{p: hashlib.sha256((source / p).read_bytes()).hexdigest() for p in names},
    }


def fixed_identity(backend: str, condition: str) -> dict[str, Any]:
    value = bind(previous.fixed_identity, runtime_identity=runtime_identity)(backend, condition)
    return {
        **value,
        "protocol": PROFILE,
        "security_runtime_version": RUNTIME_VERSION,
        "clause_pair_profiles": dict(anchors=ANCHORS, scope=SCOPE, origin=ORIGIN),
    }


def synthetic_runtime(task: Any, **kwargs: Any) -> Any:
    return run_synthetic_pair_task(
        task, constrained=kwargs["output"].parent / "constraints", **kwargs
    )


def dependencies(backend: str) -> dict[str, Any]:
    return {
        **previous.dependencies(backend),
        "PROFILE": PROFILE,
        "fixed_identity": fixed_identity,
        "execution_sources": execution_sources,
        "checkpoint": checkpoint,
        "audit_join": audit_join,
        "run_pair_task": run_pair_task if backend == "hf" else synthetic_runtime,
    }


def checkpoint(root: Path, *, expected_runtime: dict[str, str] | None = None) -> dict[str, Any]:
    no_links(root.parent.parent / "identity.json")
    bindings = dependencies("stub")
    if expected_runtime is not None:
        runtime = checked_runtime(expected_runtime)
        bindings.update(
            fixed_identity=bind(fixed_identity, runtime_identity=lambda: runtime),
            audit_join=partial(audit_join, expected_runtime=runtime),
        )
    return cast(dict[str, Any], bind(baseline.checkpoint, **bindings)(root))


def run(output: Path, environment: Path, **kwargs: Any) -> dict[str, Any]:
    if output.exists():
        inventory(output)
    backend = kwargs["backend"]
    fixed_identity(backend, kwargs.get("condition", "valid"))
    return cast(
        dict[str, Any],
        bind(baseline.run, **dependencies(backend))(
            output,
            environment,
            **kwargs,
        ),
    )
