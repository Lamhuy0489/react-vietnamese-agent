"""Externally pinned one-task native inputs; no dataset condition/oracle fields."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.agent_mount_v1 import no_links, validate_inventory
from react_agent.llm.base import GenerationConfig
from react_agent.llm.efficient_requests_v1 import GUARD_REVISION
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask, StrictRecord
from react_agent.security_v1.doc_read_final_proof_v1 import DocReadApproval, validate_catalog
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.validation import clause_dev_release_v1 as source
from react_agent.validation.context_stress_audit_v1 import equal, inventory

SOURCE_PROTOCOL = "phase5_doc_read_native_source_v1"
RUN_PROTOCOL = "phase5_doc_read_native_task_v1"
INPUT_FILES = ("task.json", "catalog.json", "approval.json", "runtime.json", "generation.json",
               "agent_inventory.json", "guard_snapshot.json")
ENVIRONMENT_FILES = {
    "documents/documents.json", "cached_pages/pages.json", "database/university.db",
}
REQUIRED = {
    "src/react_agent/security_v1/doc_read_final_proof_v1.py",
    "src/react_agent/security_v1/doc_read_final_runtime_v1.py",
    "src/react_agent/security_v1/doc_read_pair_runtime_v1.py",
    "src/react_agent/validation/doc_read_pair_audit_v1.py",
    "src/react_agent/validation/doc_read_native_admission_v1.py",
    "src/react_agent/validation/doc_read_native_release_v1.py",
    "src/react_agent/llm/doc_read_native_dispatch_v1.py",
    "scripts/run_phase5_doc_read_native_v1.py",
}


class DocReadRunManifest(StrictRecord):
    protocol: Literal["phase5_doc_read_native_run_v1"]
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    expected_task_count: Literal[1]
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    files: dict[str, str]
    environment_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    approval_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    agent_model_id: Literal["Qwen/Qwen2.5-7B-Instruct"]
    agent_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    agent_runtime_revision: str = Field(min_length=1)
    guard_revision: str = Field(min_length=1)
    guard_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    seed: int = Field(ge=0)
    evaluator_version: str = Field(min_length=1)
    native_model_authenticated: Literal[False]
    phase5_accepted: Literal[False]

    @model_validator(mode="after")
    def exact_input_fields(self) -> DocReadRunManifest:
        import re
        if set(self.files) != set(INPUT_FILES) or any(
            re.fullmatch(r"[0-9a-f]{64}", sha) is None for sha in self.files.values()
        ):
            raise ValueError("exact public input file pins required")
        return self


@dataclass(frozen=True)
class AdmittedRun:
    manifest: DocReadRunManifest
    task: PublicWorkbenchTask
    catalog: SourceCatalog
    approval: DocReadApproval
    runtime: RuntimeConfig
    generation: GenerationConfig
    snapshot: GuardSnapshot


def admit_source(project: Path, manifest: Path, expected: str, commit: str) -> dict[str, Any]:
    admitted = dict(bind(source.admit, PROTOCOL=SOURCE_PROTOCOL)(
        project, manifest, expected, commit, native=True,
    ))
    files = admitted["source_sha256"]
    if not REQUIRED <= files.keys() or any(
        name.startswith("src/react_agent/authoring/")
        or "doc_read_final_controls" in name
        or name.startswith("data/dev/") or name.startswith("data/prospective/")
        for name in files
    ):
        raise ValueError("doc_read public worker closure incomplete or contains host QA")
    return admitted


def admit_run(
    manifest_path: Path, expected_manifest_sha256: str, *, project: Path,
    source_manifest: Path, inputs: Path,
) -> AdmittedRun:
    for path in (manifest_path, project, source_manifest, inputs):
        no_links(path)
    equal(source.digest(manifest_path), expected_manifest_sha256, "external native run pin")
    manifest = DocReadRunManifest.model_validate_json(manifest_path.read_bytes())
    admit_source(project, source_manifest, manifest.source_manifest_sha256, manifest.source_commit)
    for name, sha in manifest.files.items():
        equal(source.digest(inputs / name), sha, "native input " + name)
    actual_files = inventory(inputs)
    allowed = set(INPUT_FILES) | {"environment/" + name for name in ENVIRONMENT_FILES}
    equal(sorted(actual_files), sorted(allowed), "only declared public inputs")
    equal(text_hash(canonical_json(inventory(inputs / "environment"))),
          manifest.environment_sha256, "synthetic environment hash")
    task = PublicWorkbenchTask.model_validate_json((inputs / "task.json").read_bytes())
    catalog = SourceCatalog.model_validate_json((inputs / "catalog.json").read_bytes())
    approval = DocReadApproval.model_validate_json((inputs / "approval.json").read_bytes())
    runtime = RuntimeConfig.model_validate_json((inputs / "runtime.json").read_bytes())
    generation = GenerationConfig.model_validate_json((inputs / "generation.json").read_bytes())
    snapshot = GuardSnapshot.model_validate_json((inputs / "guard_snapshot.json").read_bytes())
    model = json.loads((inputs / "agent_inventory.json").read_text())
    validate_inventory(model)
    equal(task.task_id, manifest.task_id, "native task identity")
    equal([model["model_id"], model["upstream_revision"]],
          [manifest.agent_model_id, manifest.agent_revision], "agent immutable revision")
    equal(snapshot.model_revision, manifest.guard_revision, "guard revision")
    equal(manifest.guard_revision, GUARD_REVISION, "supported native guard revision")
    equal(manifest.agent_runtime_revision, AGENT_REVISION, "supported agent runtime revision")
    equal(snapshot.sha256, manifest.guard_snapshot_sha256, "guard snapshot identity")
    equal(generation.seed, manifest.seed, "native seed")
    validate_catalog(approval, manifest.approval_sha256, catalog)
    return AdmittedRun(manifest, task, catalog, approval, runtime, generation, snapshot)
