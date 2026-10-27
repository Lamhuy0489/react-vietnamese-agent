"""Pinned single-task native dispatcher; only audited complete resume is allowed."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import write_receipt
from react_agent.llm.native_exit_pair_v1 import native_pair as build_pair
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.doc_read_pair_runtime_v1 import run_pair_task
from react_agent.tools.factory import build_smoke_registry
from react_agent.validation.context_stress_audit_v1 import equal, inventory
from react_agent.validation.doc_read_native_admission_v1 import RUN_PROTOCOL, admit_run
from react_agent.validation.doc_read_native_release_v1 import audit, audit_execution, identity
from react_agent.validation.room_ticket_run_manifest_v1 import admit_output


def execution_source(project: Path) -> None:
    """Admitted bytes must be the imported code, not an unused shadow source tree."""
    root = (project / "src").resolve()
    for name, module in tuple(sys.modules.items()):
        if name == "react_agent" or name.startswith("react_agent."):
            origin = getattr(module, "__file__", None)
            # Public worker deliberately omits validation/__init__.py: it imports host QA.
            # Admit only its single pinned namespace path, never a search path outside source.
            if name == "react_agent.validation" and origin is None:
                paths = list(getattr(module, "__path__", ()))
                spec = getattr(module, "__spec__", None)
                if (len(paths) == 1 and Path(paths[0]).resolve() == root / "react_agent/validation"
                        and spec is not None and spec.origin is None):
                    continue
            if not origin or not Path(origin).resolve().is_relative_to(root):
                raise ValueError("imported runtime is outside admitted project")


def run(
    *, manifest_path: Path, expected_manifest_sha256: str, project: Path,
    source_manifest: Path, inputs: Path, agent: Path, guard: Path, output: Path,
    resume: bool = False,
) -> dict[str, Any]:
    admit_output(output, (manifest_path, project, source_manifest, inputs, agent, guard))
    admitted = admit_run(manifest_path, expected_manifest_sha256, project=project,
                         source_manifest=source_manifest, inputs=inputs)
    execution_source(project)
    if output.exists():
        if not resume:
            raise ValueError("fresh doc_read native output required")
        return audit(output, admitted, expected_manifest_sha256)
    if resume:
        raise ValueError("cannot resume missing doc_read task")
    before = inventory(inputs)
    record = identity(admitted, expected_manifest_sha256)
    output.mkdir(parents=True)
    write_receipt(output / "identity.json", record)
    pair = build_pair(
        agent, inputs / "agent_inventory.json", guard, admitted.snapshot,
        output / "native", output / "attention", output / "policy",
        witness=output / "witness.jsonl", constrained=output / "constraints",
    )
    try:
        result = run_pair_task(
            admitted.task, pair=pair, output=output / "execution",
            registry_factory=lambda: build_smoke_registry(inputs / "environment"),
            source_catalog=admitted.catalog, security=configuration("A6"),
            runtime_config=admitted.runtime, generation=admitted.generation,
            approval=admitted.approval,
            expected_approval_sha256=admitted.manifest.approval_sha256,
        )
    finally:
        pair.close()
    audit_execution(output, admitted)
    equal(inventory(inputs), before, "native inputs stable")
    readmitted = admit_run(manifest_path, expected_manifest_sha256, project=project,
                           source_manifest=source_manifest, inputs=inputs)
    equal(readmitted.manifest.model_dump(mode="json"), admitted.manifest.model_dump(mode="json"),
          "native source/run re-admission")
    write_receipt(output / "checkpoint.json", dict(
        protocol=RUN_PROTOCOL, identity_sha256=text_hash(canonical_json(record)),
        terminal=result.result.status, raw_sha256=inventory(output),
    ))
    return audit(output, admitted, expected_manifest_sha256)
