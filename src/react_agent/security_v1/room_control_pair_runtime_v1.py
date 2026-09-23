"""Prospective v12 baseline/metadata controls on the unchanged ExitPair loop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from react_agent.agent.state import RuntimeConfig
from react_agent.environment.documents import Document
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.base import GenerationConfig
from react_agent.llm.exit_pair_v1 import ExitPair
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.clause_pair_runtime_v1 import (
    run_pair_task as baseline_native,
)
from react_agent.security_v1.clause_pair_runtime_v1 import (
    run_synthetic_pair_task as baseline_synthetic,
)
from react_agent.security_v1.contracts import SecurityConfig
from react_agent.security_v1.runtime import SecurityRun
from react_agent.tools.factory import build_smoke_registry
from react_agent.tools.registry import ToolRegistry
from react_agent.validation.host_inventory_schema_v1 import InventoryPin
from react_agent.validation.room_inventory_review_v1 import (
    RoomInventoryReview,
    pinned_room_catalog,
)

Arm = Literal["baseline", "metadata"]


def _document_ids(environment: Path) -> tuple[str, ...]:
    raw = json.loads((environment / "documents/documents.json").read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("prospective document inventory must be a list")
    return tuple(Document.model_validate(item).doc_id for item in raw)


def _run(
    task: RuntimeTask,
    *,
    arm: Arm,
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
    if arm not in {"baseline", "metadata"} or security.level != "A6":
        raise ValueError("explicit prospective v12 A6 control arm required")
    if not isinstance(pair, ExitPair):
        raise TypeError("prospective control requires a task-owned ExitPair")
    reviewed = pinned_room_catalog(
        review,
        draft_bytes,
        pin,
        expected_pin_sha256=expected_pin_sha256,
        source_commit=source_commit,
        document_ids=_document_ids(environment),
    )
    if synthetic and constrained_root is None:
        raise ValueError("synthetic control requires a separate constraint root")
    if not synthetic and constrained_root is not None:
        raise ValueError("native constraint root belongs to the guard factory")
    # Admission is shared, but baseline intentionally does not give the v12
    # runtime or model the new source metadata. Metadata gets the reviewed pair.
    catalog = SourceCatalog() if arm == "baseline" else reviewed

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
    route = baseline_synthetic if synthetic else baseline_native
    result = route(task, pair=pair, **kwargs)
    path = output / "runtime/run_metadata.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata["prospective_control"] = {
        "arm": arm,
        "review_ref": review.review_ref,
        "draft_sha256": review.draft_sha256,
        "pin_sha256": expected_pin_sha256,
        "source_commit": source_commit,
        "metadata_enabled": arm == "metadata",
        "host_inventory_attested": False,
        "source_authenticated_by_release_audit": False,
    }
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def run_pair_task(task: RuntimeTask, *, arm: Arm, pair: ExitPair, **kwargs: Any) -> SecurityRun:
    """Native-capable control; model/package admission is external."""
    return _run(task, arm=arm, pair=pair, synthetic=False, **kwargs)


def run_synthetic_pair_task(
    task: RuntimeTask, *, arm: Arm, pair: ExitPair, **kwargs: Any
) -> SecurityRun:
    """Paired CPU route, never a substitute for native model quality."""
    return _run(task, arm=arm, pair=pair, synthetic=True, **kwargs)
