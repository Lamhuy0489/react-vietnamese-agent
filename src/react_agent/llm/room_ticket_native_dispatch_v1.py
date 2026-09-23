"""Source-admitted, one-task native room-ticket dispatch with fail-closed resume.

This module does not certify model publisher or remote notebook identity. Those
are independent release-audit inputs, never inferred from a local manifest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.native_exit_pair_v1 import native_pair as build_pair
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.room_ticket_pair_runtime_v1 import run_pair_task
from react_agent.validation import clause_dev_release_v1 as source
from react_agent.validation.context_stress_audit_v1 import equal, inventory
from react_agent.validation.host_inventory_schema_v1 import InventoryPin
from react_agent.validation.room_inventory_review_v1 import (
    RoomInventoryReview,
    pinned_room_catalog,
)
from react_agent.validation.room_ticket_native_release_v1 import (
    RUN_PROTOCOL,
    admit_source,
    audit,
)
from react_agent.validation.room_ticket_pair_audit_v1 import audit_join


def _document_ids(environment: Path) -> tuple[str, ...]:
    # Use the runtime's actual document inventory, not the manifest's claim.
    from react_agent.security_v1.room_ticket_pair_runtime_v1 import _document_ids as actual

    return actual(environment)


def _identity(
    task: RuntimeTask,
    environment: Path,
    review: RoomInventoryReview,
    draft_bytes: bytes,
    pin: InventoryPin,
    *,
    expected_pin_sha256: str,
    run_manifest_sha256: str,
    source_sha256: str,
    source_commit: str,
    model_inventory: Path,
    snapshot: GuardSnapshot,
    runtime_config: RuntimeConfig,
    generation: GenerationConfig,
) -> dict[str, Any]:
    pinned_room_catalog(
        review,
        draft_bytes,
        pin,
        expected_pin_sha256=expected_pin_sha256,
        source_commit=source_commit,
        document_ids=_document_ids(environment),
    )
    return {
        "protocol": RUN_PROTOCOL,
        "task_id": task.task_id,
        "task_sha256": text_hash(
            canonical_json({"task_id": task.task_id, "instruction": task.instruction})
        ),
        "environment_sha256": text_hash(canonical_json(inventory(environment))),
        "draft_sha256": review.draft_sha256,
        "pin_sha256": expected_pin_sha256,
        "run_manifest_sha256": run_manifest_sha256,
        "source_manifest_sha256": source_sha256,
        "source_commit": source_commit,
        "model_inventory_sha256": source.digest(model_inventory),
        "guard_snapshot_sha256": snapshot.sha256,
        "runtime_config_sha256": text_hash(canonical_json(runtime_config.model_dump(mode="json"))),
        "generation_sha256": text_hash(canonical_json(generation.model_dump(mode="json"))),
        "backend": "hf",
        "native_model_authenticated": False,
        "phase5_accepted": False,
    }


def run(
    task: RuntimeTask,
    *,
    output: Path,
    project: Path,
    source_manifest: Path,
    expected_source_sha256: str,
    source_commit: str,
    environment: Path,
    review: RoomInventoryReview,
    draft_bytes: bytes,
    pin: InventoryPin,
    expected_pin_sha256: str,
    run_manifest_sha256: str,
    agent: Path,
    model_inventory: Path,
    guard: Path,
    snapshot: GuardSnapshot,
    runtime_config: RuntimeConfig,
    generation: GenerationConfig,
    resume: bool = False,
) -> dict[str, Any]:
    """Dispatch once; resume accepts only a complete, audited checkpoint."""
    for path in (
        output,
        project,
        source_manifest,
        environment,
        agent,
        model_inventory,
        guard,
    ):
        no_links(path)
    target = output.resolve()
    for protected in (project, source_manifest, environment, agent, model_inventory, guard):
        root = protected.resolve()
        if target.is_relative_to(root) or root.is_relative_to(target):
            raise ValueError("room-ticket output overlaps a frozen input")
    admitted = admit_source(project, source_manifest, expected_source_sha256, source_commit)
    identity = _identity(
        task,
        environment,
        review,
        draft_bytes,
        pin,
        expected_pin_sha256=expected_pin_sha256,
        run_manifest_sha256=run_manifest_sha256,
        source_sha256=expected_source_sha256,
        source_commit=source_commit,
        model_inventory=model_inventory,
        snapshot=snapshot,
        runtime_config=runtime_config,
        generation=generation,
    )
    if output.exists():
        if not resume:
            raise ValueError("fresh room-ticket output required")
        return audit(
            output, project, source_manifest, expected_source_sha256, source_commit, identity
        )
    if resume:
        raise ValueError("cannot resume a missing room-ticket task")
    output.mkdir(parents=True)
    write_receipt(output / "identity.json", identity)
    pair = build_pair(
        agent,
        model_inventory,
        guard,
        snapshot,
        output / "native",
        output / "attention",
        output / "policy",
        witness=output / "witness.jsonl",
        constrained=output / "constraints",
    )
    try:
        result = run_pair_task(
            task,
            pair=pair,
            environment=environment,
            output=output / "execution",
            security=configuration("A6"),
            runtime_config=runtime_config,
            generation=generation,
            review=review,
            draft_bytes=draft_bytes,
            pin=pin,
            expected_pin_sha256=expected_pin_sha256,
            source_commit=source_commit,
        )
    finally:
        pair.close()
    # Audit before sealing a checkpoint; failures retain raw bytes for diagnosis.
    joined = audit_join(
        output / "execution",
        output / "native/guard_response_diagnostics.jsonl",
        output / "witness.jsonl",
        expected_pin_sha256=expected_pin_sha256,
    )
    equal(joined["valid"], True, "room-ticket pair join before checkpoint")
    equal(
        admit_source(project, source_manifest, expected_source_sha256, source_commit),
        admitted,
        "room-ticket source stable",
    )
    write_receipt(
        output / "checkpoint.json",
        {
            "protocol": RUN_PROTOCOL,
            "identity_sha256": text_hash(canonical_json(identity)),
            "terminal": result.result.status,
            "raw_sha256": inventory(output),
        },
    )
    return audit(output, project, source_manifest, expected_source_sha256, source_commit, identity)
