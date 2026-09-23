"""Opt-in dated-room A6 policy on the constrained ExitPair transport.

The prospective inventory is admitted before pair startup. This is a new
candidate route, not a mutation of v12 or the CPU-only v13/v14 runtimes.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from react_agent.agent.state import RuntimeConfig
from react_agent.environment.documents import Document
from react_agent.llm.base import GenerationConfig
from react_agent.llm.exit_pair_v1 import ExitPair
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1 import clause_pair_runtime_v1 as baseline
from react_agent.security_v1 import constrained_runtime_v1 as constrained
from react_agent.security_v1.authorization_anchors_v3 import PROFILE as ANCHORS
from react_agent.security_v1.constrained_host_v1 import ConstrainedRoleBackend
from react_agent.security_v1.contracts import SecurityConfig
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, bind
from react_agent.security_v1.processing_scope_v5 import PROFILE as SCOPE
from react_agent.security_v1.public_field_ticket_policy_v2 import DatedTicketA6Policy
from react_agent.security_v1.public_field_ticket_v2 import PROFILE as TICKET
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v12 import SecurityRuntime as V12Runtime
from react_agent.security_v1.value_origin_v3 import PROFILE as ORIGIN
from react_agent.tools.factory import build_smoke_registry
from react_agent.tools.registry import ToolRegistry
from react_agent.validation.constrained_worker_audit_v1 import IDENTITY
from react_agent.validation.host_inventory_schema_v1 import InventoryPin
from react_agent.validation.room_inventory_review_v1 import (
    RoomInventoryReview,
    pinned_room_catalog,
)

RUNTIME_VERSION = "security_runtime_v15_room_ticket_pair_candidate_v1"


class SecurityRuntime(V12Runtime):
    """Compose v12's cumulative loop, constrained classifier and dated ticket."""

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        if not isinstance(kwargs.get("_worker"), ConstrainedRoleBackend):
            raise ValueError("room ticket pair requires its task-owned constrained guard")
        loop = SimpleNamespace(
            _run_task=bind(
                V5Runtime._run_task,
                WarmModelGuard=constrained.HostClassifier,
                PROMPT=PROMPT,
            )
        )
        body = bind(
            V12Runtime._run_task,
            V5Runtime=loop,
            ClauseA6Policy=DatedTicketA6Policy,
            RUNTIME_VERSION=RUNTIME_VERSION,
        )
        result = cast(SecurityRun, body(self, task, **kwargs))
        path = Path(kwargs["output"]) / "run_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata.update(
            constrained_execution_identity=IDENTITY,
            guard_cache_protocol="constrained_classifier_v1",
            clause_pair_profiles=dict(anchors=ANCHORS, scope=SCOPE, origin=ORIGIN),
            room_ticket_candidate={
                "profile": TICKET,
                "anchors": ANCHORS,
                "host_inventory_attested": False,
                "scope": "prospective_candidate_not_phase5_accepted",
            },
        )
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result


def _document_ids(environment: Path) -> tuple[str, ...]:
    path = environment / "documents/documents.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("prospective document inventory must be a list")
    return tuple(Document.model_validate(item).doc_id for item in raw)


def _run(
    task: RuntimeTask,
    *,
    pair: ExitPair,
    synthetic: bool,
    environment: Path,
    output: Path,
    security: SecurityConfig,
    runtime_config: RuntimeConfig,
    generation: GenerationConfig,
    review: RoomInventoryReview,
    draft_bytes: bytes,
    pin: InventoryPin,
    expected_pin_sha256: str,
    source_commit: str,
    constrained_root: Path | None = None,
) -> SecurityRun:
    if security.level != "A6":
        raise ValueError("room ticket pair requires explicit A6")
    if not isinstance(pair, ExitPair):
        raise TypeError("room ticket route requires a task-owned ExitPair")
    catalog = pinned_room_catalog(
        review,
        draft_bytes,
        pin,
        expected_pin_sha256=expected_pin_sha256,
        source_commit=source_commit,
        document_ids=_document_ids(environment),
    )
    if synthetic and constrained_root is None:
        raise ValueError("synthetic pair requires a separate constraint root")
    if not synthetic and constrained_root is not None:
        raise ValueError("native constraint root is owned by the guard factory")
    def registry_factory() -> ToolRegistry:
        return build_smoke_registry(environment)
    kwargs: dict[str, Any] = {
        "output": output,
        "registry_factory": registry_factory,
        "security": security,
        "runtime_config": runtime_config,
        "generation": generation,
        "source_catalog": catalog,
    }
    if constrained_root is not None:
        kwargs["constrained"] = constrained_root
    body = bind(baseline._run, SecurityRuntime=SecurityRuntime)
    result = cast(SecurityRun, body(task, pair=pair, synthetic=synthetic, **kwargs))
    path = output / "runtime/run_metadata.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata["prospective_inventory"] = {
        "review_ref": review.review_ref,
        "draft_sha256": review.draft_sha256,
        "pin_sha256": expected_pin_sha256,
        "source_commit": source_commit,
        "source_authenticated_by_release_audit": False,
    }
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def run_pair_task(task: RuntimeTask, *, pair: ExitPair, **kwargs: Any) -> SecurityRun:
    """Native-capable route; actual model/package admission is external."""
    return _run(task, pair=pair, synthetic=False, **kwargs)


def run_synthetic_pair_task(task: RuntimeTask, *, pair: ExitPair, **kwargs: Any) -> SecurityRun:
    """Explicit paired-process CPU route; never an HF success substitute."""
    return _run(task, pair=pair, synthetic=True, **kwargs)
