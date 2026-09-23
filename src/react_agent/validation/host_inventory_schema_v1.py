"""Content-free host annotation and run-pin schemas shared by pilot and Dev tools.

This module has no benchmark fixture, authoring, evaluator or model imports so
the inference worker can validate a pin without packaging those components.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.schemas.adversarial_workbench import StrictRecord


class AuxiliaryAnnotation(StrictRecord):
    source_type: Literal[SourceType.DOCUMENT, SourceType.CACHED_PAGE]
    source_id: str = Field(pattern=r"^AUX_[A-Z]+$")
    sensitivity: Sensitivity
    trust: Literal[Trust.UNTRUSTED] = Trust.UNTRUSTED
    basis: Literal["pre_ingestion_host_inventory"] = "pre_ingestion_host_inventory"


class PairAnnotations(StrictRecord):
    version: Literal["pair_host_annotations_v1"] = "pair_host_annotations_v1"
    pair_id: str = Field(min_length=1)
    entries: tuple[AuxiliaryAnnotation, ...]

    @model_validator(mode="after")
    def canonical_entries(self) -> Self:
        keys = [(entry.source_type, entry.source_id) for entry in self.entries]
        if not keys or keys != sorted(set(keys)):
            raise ValueError("nonempty, sorted, unique host annotation entries required")
        return self

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))


class InventoryPin(StrictRecord):
    """Declared inventory identity; human review and declaration timing are external facts."""

    version: Literal["host_inventory_pin_v1"] = "host_inventory_pin_v1"
    annotations: PairAnnotations
    owner_ref: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_./-]+$")
    review_ref: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_./-]+$")
    declared_at_utc: datetime
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")

    @field_validator("declared_at_utc")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("inventory declaration requires an explicit UTC timestamp")
        return value

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))
