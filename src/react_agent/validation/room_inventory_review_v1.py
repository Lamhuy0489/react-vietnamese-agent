"""Content-free owner review for a new prospective room-source inventory.

The record binds the earlier draft bytes and exact source roles. A review
reference is an operator declaration, not a cryptographic human signature.
No document content or evaluator oracle is read here.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.schemas.adversarial_workbench import StrictRecord
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.validation.host_inventory_schema_v1 import InventoryPin, PairAnnotations

PAIR_ID: Literal["PILOT_ROOM_PROSPECTIVE_001"] = "PILOT_ROOM_PROSPECTIVE_001"
EXPECTED = (
    (SourceType.DOCUMENT, "AUX_FUTUREPRIVATE", Sensitivity.CONFIDENTIAL, Trust.UNTRUSTED),
    (SourceType.DOCUMENT, "AUX_FUTUREROOM", Sensitivity.PUBLIC, Trust.UNTRUSTED),
)


class RoomInventoryReview(StrictRecord):
    """Owner-declared review of a previously authored, content-free draft."""

    version: Literal["phase5_room_inventory_review_v1"] = "phase5_room_inventory_review_v1"
    status: Literal["owner_confirmed"] = "owner_confirmed"
    pair_id: Literal["PILOT_ROOM_PROSPECTIVE_001"] = PAIR_ID
    draft_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    owner_ref: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_./-]+$")
    review_ref: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_./-]+$")
    recorded_at_utc: datetime

    @field_validator("recorded_at_utc")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("review record requires an explicit UTC timestamp")
        return value

    @model_validator(mode="after")
    def nonempty_review_reference(self) -> Self:
        if self.review_ref == self.owner_ref:
            raise ValueError("review reference must identify the distinct decision record")
        return self

    def admit_draft(self, draft_bytes: bytes) -> PairAnnotations:
        """Require byte-identical approved labels; do not inspect source content."""
        review = RoomInventoryReview.model_validate(self.model_dump(mode="json"))
        if hashlib.sha256(draft_bytes).hexdigest() != review.draft_sha256:
            raise ValueError("inventory draft differs from owner-reviewed bytes")
        annotations = PairAnnotations.model_validate_json(draft_bytes)
        if annotations.pair_id != PAIR_ID:
            raise ValueError("reviewed inventory has the wrong pair")
        labels = tuple(
            (entry.source_type, entry.source_id, entry.sensitivity, entry.trust)
            for entry in annotations.entries
        )
        if labels != EXPECTED:
            raise ValueError("reviewed inventory differs from approved source roles")
        return annotations

    def prepare_pin(
        self, draft_bytes: bytes, *, source_commit: str, declared_at_utc: datetime
    ) -> InventoryPin:
        """Build a separate run pin only after an actual source commit exists."""
        review = RoomInventoryReview.model_validate(self.model_dump(mode="json"))
        pin = InventoryPin(
            annotations=review.admit_draft(draft_bytes),
            owner_ref=review.owner_ref,
            review_ref=review.review_ref,
            declared_at_utc=declared_at_utc,
            source_commit=source_commit,
        )
        if pin.declared_at_utc < review.recorded_at_utc:
            raise ValueError("run pin cannot predate the recorded review")
        return pin


def pinned_room_catalog(
    review: RoomInventoryReview,
    draft_bytes: bytes,
    pin: InventoryPin,
    *,
    expected_pin_sha256: str,
    source_commit: str,
    document_ids: tuple[str, ...],
) -> SourceCatalog:
    """Admit only the reviewed pair and an independently frozen run pin.

    ``expected_pin_sha256`` must come from a run manifest frozen before any
    document content or inference. This function cannot authenticate Git or
    prove when the human review occurred; those checks belong to release audit.
    """
    review = RoomInventoryReview.model_validate(review.model_dump(mode="json"))
    pin = InventoryPin.model_validate(pin.model_dump(mode="json"))
    annotations = review.admit_draft(draft_bytes)
    if pin.identity != expected_pin_sha256:
        raise ValueError("inventory pin differs from the frozen run identity")
    if pin.source_commit != source_commit:
        raise ValueError("inventory pin source commit differs from the run identity")
    if pin.annotations != annotations or (
        pin.owner_ref,
        pin.review_ref,
    ) != (review.owner_ref, review.review_ref):
        raise ValueError("inventory pin differs from the owner-reviewed source roles")
    if pin.declared_at_utc < review.recorded_at_utc:
        raise ValueError("inventory pin predates the owner review record")
    if len(document_ids) != len(set(document_ids)):
        raise ValueError("duplicate document ID in prospective environment")
    auxiliary = {identity for identity in document_ids if identity.startswith("AUX_")}
    if auxiliary != {entry.source_id for entry in annotations.entries}:
        raise ValueError("prospective environment differs from approved auxiliary inventory")
    catalog = SourceCatalog(
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
            for entry in annotations.entries
        ),
    )
    ResourceBindings.from_catalog(catalog)
    return catalog
