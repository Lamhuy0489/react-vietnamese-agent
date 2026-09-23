"""External, content-pinned admission for one prospective native ticket task."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.base import GenerationConfig
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask, StrictRecord
from react_agent.validation import clause_dev_release_v1 as source
from react_agent.validation.context_stress_audit_v1 import equal, inventory
from react_agent.validation.host_inventory_schema_v1 import InventoryPin
from react_agent.validation.room_inventory_review_v1 import (
    RoomInventoryReview,
    pinned_room_catalog,
)
from react_agent.validation.room_ticket_native_release_v1 import admit_source


class RoomTicketRunManifest(StrictRecord):
    """Single ticket-arm specimen; other declared arms need separate launchers."""

    protocol: Literal["phase5_room_ticket_run_manifest_v1"]
    arm: Literal["ticket"]
    condition: Literal[
        "clean_public_room",
        "poisoned_public_room",
        "s2_collision",
        "wrong_destination",
        "final_leak",
    ]
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    expected_task_count: Literal[1]
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    draft_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    inventory_pin_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    inventory_pin_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    task_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    environment_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    agent_model_id: str = Field(min_length=1)
    agent_model_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    guard_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    guard_snapshot_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    guard_model_revision: str = Field(min_length=1)
    runtime_config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    generation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    seed: int = Field(ge=0)
    evaluator_version: str = Field(min_length=1)
    source_authenticated_by_remote_audit: Literal[False]
    phase5_accepted: Literal[False]

    @model_validator(mode="after")
    def exact_model_roles(self) -> Self:
        if self.agent_model_id != "Qwen/Qwen2.5-7B-Instruct":
            raise ValueError("fixed prospective agent model required")
        return self


def admit_output(output: Path, inputs: tuple[Path, ...]) -> None:
    """No frozen input may be inside the output tree or contain that tree."""
    no_links(output)
    target = output.resolve()
    for path in inputs:
        no_links(path)
        frozen = path.resolve()
        if target.is_relative_to(frozen) or frozen.is_relative_to(target):
            raise ValueError("prospective output overlaps frozen input")


def admit_run(
    manifest_path: Path,
    expected_manifest_sha256: str,
    *,
    project: Path,
    source_manifest: Path,
    review_path: Path,
    draft_path: Path,
    pin_path: Path,
    task_path: Path,
    environment: Path,
    model_inventory: Path,
    snapshot_path: Path,
    runtime_config_path: Path,
    generation_path: Path,
) -> tuple[
    RoomTicketRunManifest,
    PublicWorkbenchTask,
    RoomInventoryReview,
    bytes,
    InventoryPin,
    GuardSnapshot,
    RuntimeConfig,
    GenerationConfig,
]:
    """Compare all observed bytes to an independent run-manifest SHA before worker startup."""
    for path in (
        manifest_path,
        source_manifest,
        review_path,
        draft_path,
        pin_path,
        task_path,
        environment,
        model_inventory,
        snapshot_path,
        runtime_config_path,
        generation_path,
    ):
        no_links(path)
    equal(source.digest(manifest_path), expected_manifest_sha256, "external prospective run pin")
    manifest = RoomTicketRunManifest.model_validate_json(manifest_path.read_bytes())
    admit_source(
        project,
        source_manifest,
        manifest.source_manifest_sha256,
        manifest.source_commit,
    )
    for path, expected, label in (
        (review_path, manifest.review_sha256, "owner review"),
        (draft_path, manifest.draft_sha256, "reviewed draft"),
        (pin_path, manifest.inventory_pin_file_sha256, "inventory pin file"),
        (task_path, manifest.task_sha256, "prospective task"),
        (model_inventory, manifest.model_inventory_sha256, "agent model inventory"),
        (snapshot_path, manifest.guard_snapshot_file_sha256, "guard snapshot file"),
        (runtime_config_path, manifest.runtime_config_sha256, "runtime config file"),
        (generation_path, manifest.generation_sha256, "generation config file"),
    ):
        # The snapshot's content identity is separately checked below; the
        # manifest binds its exact JSON bytes as well.
        equal(source.digest(path), expected, label)
    task = PublicWorkbenchTask.model_validate_json(task_path.read_bytes())
    review = RoomInventoryReview.model_validate_json(review_path.read_bytes())
    draft = draft_path.read_bytes()
    pin = InventoryPin.model_validate_json(pin_path.read_bytes())
    snapshot = GuardSnapshot.model_validate_json(snapshot_path.read_bytes())
    runtime = RuntimeConfig.model_validate_json(runtime_config_path.read_bytes())
    generation = GenerationConfig.model_validate_json(generation_path.read_bytes())
    model = json.loads(model_inventory.read_text(encoding="utf-8"))
    equal(task.task_id, manifest.task_id, "prospective task ID")
    equal(pin.identity, manifest.inventory_pin_sha256, "canonical inventory pin")
    equal(snapshot.sha256, manifest.guard_snapshot_sha256, "canonical guard snapshot")
    equal(snapshot.model_revision, manifest.guard_model_revision, "guard revision")
    equal(generation.seed, manifest.seed, "generation seed")
    equal(
        [model["model_id"], model["upstream_revision"]],
        [manifest.agent_model_id, manifest.agent_model_revision],
        "agent immutable revision",
    )
    equal(
        text_hash(canonical_json(inventory(environment))),
        manifest.environment_sha256,
        "prospective environment",
    )
    documents = json.loads((environment / "documents/documents.json").read_text(encoding="utf-8"))
    pinned_room_catalog(
        review,
        draft,
        pin,
        expected_pin_sha256=manifest.inventory_pin_sha256,
        source_commit=manifest.source_commit,
        document_ids=tuple(row["doc_id"] for row in documents),
    )
    return manifest, task, review, draft, pin, snapshot, runtime, generation
