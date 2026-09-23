"""Content-free, unreviewed source plan for the synthetic CPU room pilot only."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, model_validator

from react_agent.environment.documents import Document
from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.schemas.adversarial_workbench import StrictRecord


class SyntheticRoomSource(StrictRecord):
    source_id: str = Field(pattern=r"^AUX_[A-Z]+$")
    source_type: Literal[SourceType.DOCUMENT] = SourceType.DOCUMENT
    sensitivity: Sensitivity
    trust: Literal[Trust.UNTRUSTED] = Trust.UNTRUSTED


class SyntheticRoomInventory(StrictRecord):
    version: Literal["phase5_room_synthetic_inventory_v1"] = (
        "phase5_room_synthetic_inventory_v1"
    )
    pair_id: Literal["SYN_ROOM_002"] = "SYN_ROOM_002"
    status: Literal["assistant_draft_unreviewed"] = "assistant_draft_unreviewed"
    entries: tuple[SyntheticRoomSource, ...]

    @model_validator(mode="after")
    def exact_sorted_sources(self) -> Self:
        ids = [entry.source_id for entry in self.entries]
        if ids != ["AUX_NEWPRIVATE", "AUX_NEWROOM"]:
            raise ValueError("room pilot requires exact sorted synthetic source IDs")
        return self

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))

    def catalog_for_documents(self, documents: list[dict[str, object]]) -> SourceCatalog:
        """Bind exact auxiliary IDs; text cannot influence host labels."""
        inventory = SyntheticRoomInventory.model_validate(self.model_dump(mode="json"))
        parsed = [Document.model_validate(item) for item in documents]
        ids = [document.doc_id for document in parsed]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate document ID in synthetic environment")
        auxiliary = {identity for identity in ids if identity.startswith("AUX_")}
        if auxiliary != {entry.source_id for entry in inventory.entries}:
            raise ValueError("synthetic auxiliary documents differ from predeclared inventory")
        return SourceCatalog(
            version="host_source_catalog_v2_annotations",
            bindings=tuple(
                SourceBinding(
                    tool="doc_read",
                    arguments_json=canonical_json({"doc_id": entry.source_id}),
                    label=SourceLabel(
                        source_type=entry.source_type,
                        source_id=entry.source_id,
                        sensitivity=entry.sensitivity,
                        trust=entry.trust,
                    ),
                )
                for entry in inventory.entries
            ),
        )
