"""Source-admitted Dev32 dispatch, separate from the frozen CPU-only runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from react_agent.llm import grouped_dev_runner_v2 as baseline
from react_agent.llm.clause_dev_identity_v1 import identity as cpu_identity
from react_agent.llm.clause_dev_identity_v1 import pair_config
from react_agent.llm.clause_dev_runner_v1 import native_pair, synthetic_pair, synthetic_runtime
from react_agent.llm.exit_pair_v1 import observer_config
from react_agent.llm.native_shutdown_v2 import native_config
from react_agent.security_v1.clause_pair_runtime_v1 import run_pair_task
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation.clause_dev_checkpoint_v1 import audit_checkpoint, audit_prefix
from react_agent.validation.clause_dev_release_v1 import admit
from react_agent.validation.context_stress_audit_v1 import equal


def release_identity(*args: Any, release: dict[str, Any], **kwargs: Any) -> Any:
    manifest, rows = cpu_identity(*args, **kwargs)
    manifest.update(
        release_binding=release,
        source_admission_protocol="clause_dev32_source_v1",
        native_release_authenticated=False,  # Remote admission is a separate host audit.
        native_dispatch_allowed=release["source_mode"] == "committed",
    )
    return manifest, rows


def native_runtime(task: Any, **kwargs: Any) -> Any:
    return run_pair_task(task, constrained=kwargs["output"].parent / "constraints", **kwargs)


def run(
    output: Path,
    release: Path,
    environment: Path,
    *,
    project: Path,
    source_manifest: Path,
    source_sha256: str,
    **kwargs: Any,
) -> dict[str, Any]:
    backend = kwargs.get("backend", "stub")
    if backend not in {"stub", "hf"}:
        raise ValueError("explicit known backend required")
    admitted = admit(
        project, source_manifest, source_sha256, kwargs["commit"], native=backend == "hf"
    )
    for protected in (project, source_manifest):
        if output.resolve().is_relative_to(
            protected.resolve()
        ) or protected.resolve().is_relative_to(output.resolve()):
            raise ValueError("output overlaps admitted source")

    def identity(*args: Any, **options: Any) -> Any:
        return release_identity(*args, release=admitted, **options)

    result = bind(
        baseline.run,
        identity=identity,
        pair_config=pair_config,
        native_config=lambda: observer_config(native_config()),
        ShutdownPair=synthetic_pair,
        native_pair=native_pair,
        run_pair_task=native_runtime if backend == "hf" else synthetic_runtime,
        audit_checkpoint=audit_checkpoint,
        audit_prefix=audit_prefix,
    )(output, release, environment, **kwargs)
    equal(
        admit(project, source_manifest, source_sha256, kwargs["commit"], native=backend == "hf"),
        admitted,
        "source unchanged after execution",
    )
    return cast(dict[str, Any], {**result, "expected": 4, "remaining": 4 - result["completed"]})
