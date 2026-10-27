"""Read-only complete checkpoint audit with externally admitted run inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.doc_read_native_admission_v1 import RUN_PROTOCOL, AdmittedRun
from react_agent.validation.doc_read_pair_audit_v1 import audit_join


def identity(admitted: AdmittedRun, run_sha256: str) -> dict[str, Any]:
    return dict(protocol=RUN_PROTOCOL, run_manifest_sha256=run_sha256,
                manifest=admitted.manifest.model_dump(mode="json"))


def audit_execution(output: Path, admitted: AdmittedRun) -> dict[str, Any]:
    """Join actual runtime identities before allowing a durable checkpoint."""
    joined = audit_join(
        output / "execution", output / "native/guard_response_diagnostics.jsonl",
        output / "witness.jsonl", approval=admitted.approval,
        expected_approval_sha256=admitted.manifest.approval_sha256,
    )
    meta = read_record(output / "execution/runtime/run_metadata.json")
    equal(meta["task_hash"], text_hash(admitted.task.instruction), "actual raw task")
    equal(meta["task_id"], admitted.task.task_id, "actual task ID")
    equal(meta["source_catalog"], admitted.catalog.model_dump(mode="json"), "actual source catalog")
    equal(meta["runtime_config"], admitted.runtime.model_dump(mode="json"), "actual runtime config")
    equal(meta["generation_config"], admitted.generation.model_dump(mode="json"),
          "actual generation")
    equal([meta["model_id"], meta["model_revision"]],
          [admitted.manifest.agent_model_id, admitted.manifest.agent_runtime_revision],
          "actual agent identity")
    equal([meta["guard_execution"]["model_id"], meta["guard_execution"]["model_revision"]],
          [admitted.snapshot.model_id, admitted.manifest.guard_revision], "actual guard identity")
    return joined


def audit(output: Path, admitted: AdmittedRun, run_sha256: str) -> dict[str, Any]:
    before = inventory(output)
    expected = identity(admitted, run_sha256)
    equal(read_record(output / "identity.json"), expected, "native task identity")
    if not (output / "checkpoint.json").is_file():
        raise ValueError("partial doc_read task requires manual triage; no semantic retry")
    checkpoint = read_record(output / "checkpoint.json")
    equal(checkpoint["protocol"], RUN_PROTOCOL, "doc_read checkpoint protocol")
    equal(checkpoint["identity_sha256"], text_hash(canonical_json(expected)), "checkpoint identity")
    raw = {name: sha for name, sha in before.items() if name != "checkpoint.json"}
    equal(checkpoint["raw_sha256"], raw, "immutable complete raw checkpoint")
    joined = audit_execution(output, admitted)
    meta = read_record(output / "execution/runtime/run_metadata.json")
    equal(meta["result"]["status"], checkpoint["terminal"], "checkpoint terminal")
    equal(inventory(output), before, "native checkpoint audit read-only")
    return dict(protocol=RUN_PROTOCOL, valid=True, terminal=checkpoint["terminal"],
                joined=joined, native_model_authenticated=False, phase5_accepted=False)
