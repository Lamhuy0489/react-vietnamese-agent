"""Separate four-task observed-exit diagnostic with hash-bound missing-only resume."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from functools import partial
from pathlib import Path
from typing import Any, cast

from react_agent.llm import constrained_probe_v1 as constrained
from react_agent.llm import guard_observer_probe_v2 as baseline
from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.exit_pair_v1 import ExitPair, ExitPairConfig, observer_config
from react_agent.llm.native_exit_pair_v1 import native_pair as build_native
from react_agent.security_v1.exit_milestones_v1 import runtime_identity
from react_agent.security_v1.exit_pair_runtime_v1 import run_pair_task, run_synthetic_pair_task
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation.context_stress_audit_v1 import inventory
from react_agent.validation.exit_pair_audit_v1 import audit_join, checked_runtime

PROFILE = "constrained_exit_pair_probe_v1"
SCHEDULE = baseline.SCHEDULE


def config(backend: str) -> ExitPairConfig:
    return observer_config(baseline.config(backend))


def execution_sources() -> dict[str, str]:
    source = Path(__file__).resolve().parents[1]
    names = (
        "llm/exit_pair_probe_v1.py",
        "llm/exit_pair_v1.py",
        "llm/native_exit_pair_v1.py",
        "security_v1/exit_pair_runtime_v1.py",
        "validation/exit_pair_audit_v1.py",
        "validation/exit_native_audit_v1.py",
        "security_v1/exit_milestones_v1.py",
        "validation/exit_milestones_v1.py",
        "llm/model_pair_v1.py",
        "llm/model_pair_v2.py",
        "security_v1/worker_shutdown_v2.py",
        "security_v1/warm_guard.py",
    )
    return {
        **constrained.execution_sources(),
        **{name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in names},
    }


def fixed_identity(backend: str, condition: str) -> dict[str, Any]:
    identity = constrained.fixed_identity(backend, condition)
    identity.update(
        protocol=PROFILE,
        pair_config=asdict(config(backend)),
        exit_observer=dict(protocol="exit_milestones_v1", runtime=runtime_identity()),
    )
    return identity


def native_pair(*args: Any, **kwargs: Any) -> ExitPair:
    witness: Path = kwargs["witness"]
    return build_native(*args, **kwargs, constrained=witness.parent / "constraints")


def synthetic_pair(*args: Any, **kwargs: Any) -> ExitPair:
    return cast(
        ExitPair, bind(constrained.synthetic_pair, DiagnosticPair=ExitPair)(*args, **kwargs)
    )


def synthetic_runtime(task: Any, **kwargs: Any) -> Any:
    return run_synthetic_pair_task(
        task, constrained=kwargs["output"].parent / "constraints", **kwargs
    )


def dependencies(backend: str) -> dict[str, Any]:
    return dict(
        PROFILE=PROFILE,
        fixed_identity=fixed_identity,
        execution_sources=execution_sources,
        config=config,
        checkpoint=checkpoint,
        audit_join=audit_join,
        native_pair=native_pair,
        DiagnosticPair=synthetic_pair,
        run_pair_task=run_pair_task if backend == "hf" else synthetic_runtime,
    )


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
        inventory(output)  # Reject symlinks before the frozen resume body reads identity.
    backend = kwargs["backend"]
    fixed_identity(backend, kwargs.get("condition", "valid"))
    return cast(
        dict[str, Any], bind(baseline.run, **dependencies(backend))(output, environment, **kwargs)
    )
