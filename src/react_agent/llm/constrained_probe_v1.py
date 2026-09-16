"""Versioned constrained probe/checkpoints over the fixed public observer schedule."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.normalization import text_hash
from react_agent.llm import guard_observer_probe_v2 as baseline
from react_agent.llm.constrained_probe_stub_v1 import SyntheticConstraintFactory
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticFactory
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.native_constrained_pair_v1 import native_pair as constrained_pair
from react_agent.security_v1.constrained_runtime_v1 import (
    RUNTIME_VERSION,
    run_pair_task,
    run_synthetic_pair_task,
)
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, PROMPT_VERSION, bind
from react_agent.validation.constrained_runtime_audit_v1 import audit_join as constraint_join
from react_agent.validation.constrained_worker_audit_v1 import IDENTITY, LANGUAGE, POLICY

PROFILE = "constrained_guard_probe_v1"
SCHEDULE = baseline.SCHEDULE


def execution_sources() -> dict[str, str]:
    source = Path(__file__).resolve().parents[1]
    names = (
        "llm/constrained_probe_v1.py",
        "llm/constrained_probe_stub_v1.py",
        "llm/native_constrained_pair_v1.py",
        "llm/constrained_policy_v1.py",
        "llm/constrained_guard_v1.py",
        "llm/guard_token_language_v1.py",
        "security_v1/constrained_host_v1.py",
        "security_v1/constrained_runtime_v1.py",
        "security_v1/constrained_classifier_v1.py",
        "security_v1/guard_bare_json_v1.py",
        "validation/constrained_worker_audit_v1.py",
        "validation/constrained_runtime_audit_v1.py",
        "validation/constrained_native_audit_v1.py",
    )
    return {
        **baseline.execution_sources(),
        **{name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in names},
    }


def fixed_identity(backend: str, condition: str) -> dict[str, Any]:
    if condition not in {"valid", "backend_failure"} or (backend == "hf" and condition != "valid"):
        raise ValueError("unknown condition or forbidden native injection")
    identity = baseline.fixed_identity(backend, "valid")
    identity.update(
        protocol=PROFILE,
        condition=condition,
        security_runtime_version=RUNTIME_VERSION,
        guard_prompt=dict(version=PROMPT_VERSION, sha256=text_hash(PROMPT)),
        constrained_execution=dict(identity=IDENTITY, language=LANGUAGE, policy=POLICY),
        synthetic_constraint_receipts=backend == "stub",
    )
    return identity


def audit_join(execution: Path, sidecar: Path, witness: Path) -> dict[str, Any]:
    return constraint_join(execution, sidecar, witness, execution.parent / "constraints")


def native_pair(*args: Any, **kwargs: Any) -> DiagnosticPair:
    witness: Path = kwargs["witness"]
    return constrained_pair(*args, **kwargs, constrained=witness.parent / "constraints")


def synthetic_pair(
    agent: Any, guard: DiagnosticFactory, config: Any, witness: Path
) -> DiagnosticPair:
    fixture = guard.backend_factory
    if type(fixture) is not baseline.StubFactory or fixture.role != "guard":
        raise ValueError("explicit synthetic guard factory required")
    return DiagnosticPair(
        agent,
        cast(
            Any,
            DiagnosticFactory(
                SyntheticConstraintFactory(witness.parent / "constraints", fixture.condition),
                guard.output,
            ),
        ),
        config,
        witness,
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
        checkpoint=checkpoint,
        audit_join=audit_join,
        native_pair=native_pair,
        DiagnosticPair=synthetic_pair,
        run_pair_task=run_pair_task if backend == "hf" else synthetic_runtime,
    )


def checkpoint(root: Path) -> dict[str, Any]:
    # Backend only selects a runtime entry; checkpoint never invokes it.
    return cast(dict[str, Any], bind(baseline.checkpoint, **dependencies("stub"))(root))


def run(output: Path, environment: Path, **kwargs: Any) -> dict[str, Any]:
    backend = kwargs["backend"]
    fixed_identity(backend, kwargs.get("condition", "valid"))
    return cast(
        dict[str, Any], bind(baseline.run, **dependencies(backend))(output, environment, **kwargs)
    )
