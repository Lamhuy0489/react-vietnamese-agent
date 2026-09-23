"""Committed-source one-task v12 baseline/metadata native controls."""

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
from react_agent.llm.room_ticket_native_dispatch_v1 import _identity as ticket_identity
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.room_control_pair_runtime_v1 import Arm, run_pair_task
from react_agent.validation.context_stress_audit_v1 import equal, inventory
from react_agent.validation.host_inventory_schema_v1 import InventoryPin
from react_agent.validation.room_control_native_release_v1 import RUN_PROTOCOL, audit
from react_agent.validation.room_control_pair_audit_v1 import audit_join
from react_agent.validation.room_inventory_review_v1 import RoomInventoryReview
from react_agent.validation.room_ticket_native_release_v1 import admit_source


def run(
    task: RuntimeTask,
    *,
    arm: Arm,
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
    if arm not in {"baseline", "metadata"}:
        raise ValueError("v12 control requires baseline or metadata arm")
    for path in (output, project, source_manifest, environment, agent, model_inventory, guard):
        no_links(path)
    target = output.resolve()
    for protected in (project, source_manifest, environment, agent, model_inventory, guard):
        root = protected.resolve()
        if target.is_relative_to(root) or root.is_relative_to(target):
            raise ValueError("control output overlaps a frozen input")
    admitted = admit_source(project, source_manifest, expected_source_sha256, source_commit)
    identity = ticket_identity(
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
    identity.update(
        protocol=RUN_PROTOCOL,
        arm=arm,
        review_ref=review.review_ref,
        catalog_role="none" if arm == "baseline" else "reviewed_s0_s2",
    )
    if output.exists():
        if not resume:
            raise ValueError("fresh control output required")
        return audit(
            output, project, source_manifest, expected_source_sha256, source_commit, identity
        )
    if resume:
        raise ValueError("cannot resume a missing control task")
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
            arm=arm,
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
    joined = audit_join(
        output / "execution",
        output / "native/guard_response_diagnostics.jsonl",
        output / "witness.jsonl",
        expected_arm=arm,
        expected_review_ref=review.review_ref,
        expected_draft_sha256=review.draft_sha256,
        expected_pin_sha256=expected_pin_sha256,
        expected_source_commit=source_commit,
    )
    equal(joined["valid"], True, "control pair join before checkpoint")
    equal(
        admit_source(project, source_manifest, expected_source_sha256, source_commit),
        admitted,
        "control source stable",
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
