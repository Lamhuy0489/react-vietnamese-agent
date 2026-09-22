"""Dev32 bounded paired runner; keep raw errors and missing-only resume intact."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from react_agent.llm import grouped_dev_runner_v2 as baseline
from react_agent.llm.clause_dev_identity_v1 import identity, pair_config
from react_agent.llm.constrained_probe_stub_v1 import SyntheticConstraintFactory
from react_agent.llm.exit_pair_v1 import ExitPair
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticFactory
from react_agent.llm.native_exit_pair_v1 import native_pair as build_native
from react_agent.security_v1.clause_pair_runtime_v1 import run_synthetic_pair_task
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation.clause_dev_checkpoint_v1 import audit_checkpoint, audit_prefix


def synthetic_pair(agent: Any, guard: Any, config: Any) -> ExitPair:
    output = Path(guard.output)
    return ExitPair(
        agent,
        cast(
            Any,
            DiagnosticFactory(
                SyntheticConstraintFactory(output.parent / "constraints", "valid"),
                output,
            ),
        ),
        config,
        output.parent / "witness.jsonl",
    )


def native_pair(*args: Any, **kwargs: Any) -> ExitPair:
    root = Path(args[4]).parent
    return build_native(
        *args, **kwargs, witness=root / "witness.jsonl", constrained=root / "constraints"
    )


def synthetic_runtime(task: Any, **kwargs: Any) -> Any:
    return run_synthetic_pair_task(
        task, constrained=kwargs["output"].parent / "constraints", **kwargs
    )


def run(output: Path, release: Path, environment: Path, **kwargs: Any) -> dict[str, Any]:
    backend = kwargs.get("backend", "stub")
    # Native dispatch stays gated until a versioned release auditor and exact
    # package rehearsal exist. A caller cannot silently label CPU evidence HF.
    if backend != "stub":
        raise ValueError("Dev32 native release gate pending; explicit stub backend only")
    result = bind(
        baseline.run,
        identity=identity,
        pair_config=pair_config,
        ShutdownPair=synthetic_pair,
        native_pair=native_pair,
        run_pair_task=synthetic_runtime,
        audit_checkpoint=audit_checkpoint,
        audit_prefix=audit_prefix,
    )(output, release, environment, **kwargs)
    return cast(dict[str, Any], {**result, "expected": 4, "remaining": 4 - result["completed"]})
