"""Run-isolated immutable JSON artifacts and conservative, append-only provenance."""

from __future__ import annotations

import hashlib
import json
import math
import re
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from react_agent.foundation.normalization import NormalizationResult, normalize


class Sensitivity(StrEnum):
    PUBLIC = "S0"
    INTERNAL = "S1"
    CONFIDENTIAL = "S2"


class Trust(StrEnum):
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"


class ArtifactType(StrEnum):
    USER_INPUT = "USER_INPUT"
    DOCUMENT_CONTENT = "DOCUMENT_CONTENT"
    CACHED_PAGE = "CACHED_PAGE"
    DB_RESULT = "DB_RESULT"
    CALCULATION_RESULT = "CALCULATION_RESULT"
    TOOL_RESULT = "TOOL_RESULT"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    TOOL_ARGUMENT = "TOOL_ARGUMENT"
    FINAL_RESPONSE = "FINAL_RESPONSE"
    NORMALIZED_VIEW = "NORMALIZED_VIEW"


class SourceType(StrEnum):
    USER = "USER"
    DOCUMENT = "DOCUMENT"
    DATABASE = "DATABASE"
    CACHED_PAGE = "CACHED_PAGE"
    CALCULATOR = "CALCULATOR"
    MODEL = "MODEL"
    SYSTEM = "SYSTEM"
    TOOL = "TOOL"


class Relation(StrEnum):
    OBSERVED_FROM = "OBSERVED_FROM"
    DERIVED_FROM = "DERIVED_FROM"
    NORMALIZED_FROM = "NORMALIZED_FROM"
    GENERATED_USING = "GENERATED_USING"
    EXTRACTED_FROM = "EXTRACTED_FROM"
    ARGUMENT_DERIVED_FROM = "ARGUMENT_DERIVED_FROM"


def canonical_json(value: object) -> str:
    def check(item: object) -> None:
        if item is None or type(item) in (str, bool, int):
            return
        if type(item) is float and math.isfinite(item):
            return
        if isinstance(item, list):
            for child in item:
                check(child)
            return
        if isinstance(item, dict) and all(type(k) is str for k in item):
            for child in item.values():
                check(child)
            return
        raise ValueError("content must be finite JSON with string keys")

    check(value)
    result = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    result.encode("utf-8", errors="strict")
    return result


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def join_sensitivity(*labels: Sensitivity) -> Sensitivity:
    if not labels:
        raise ValueError("join requires at least one label")
    order = list(Sensitivity)
    return max((Sensitivity(s) for s in labels), key=order.index)


def join_trust(*labels: Trust) -> Trust:
    if not labels:
        raise ValueError("join requires at least one label")
    checked = [Trust(label) for label in labels]
    return Trust.UNTRUSTED if Trust.UNTRUSTED in checked else Trust.TRUSTED


class Immutable(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ParentLink(Immutable):
    parent_id: str
    relation: Relation


class Edge(Immutable):
    run_id: str
    parent_id: str
    child_id: str
    relation: Relation


class Artifact(Immutable):
    schema_version: str = Field(default="artifact_v1", pattern=r"^artifact_v1$")
    artifact_id: str
    run_id: str
    artifact_type: ArtifactType
    raw_json: str
    source_type: SourceType
    source_id: str | None
    producer: str = Field(min_length=1)
    created_step: int = Field(ge=0, strict=True)
    sensitivity: Sensitivity
    trust: Trust
    parents: tuple[ParentLink, ...] = ()
    transformations: tuple[str, ...] = ()
    content_hash: str
    metadata_json: str = "{}"

    @model_validator(mode="after")
    def valid_serialization(self) -> Self:
        for text in (self.raw_json, self.metadata_json):
            if canonical_json(json.loads(text)) != text:
                raise ValueError("artifact JSON must be canonical")
        if not isinstance(json.loads(self.metadata_json), dict):
            raise ValueError("artifact metadata must be an object")
        if content_hash(self.raw_json) != self.content_hash:
            raise ValueError("artifact content hash mismatch")
        return self

    def content(self) -> JsonValue:
        value: JsonValue = json.loads(self.raw_json)
        return value


class ArtifactStore:
    def __init__(self, run_id: str) -> None:
        if re.fullmatch(r"[A-Za-z0-9_-]{1,100}", run_id) is None:
            raise ValueError("invalid host-owned run identity")
        self._run_id = run_id
        self._items: dict[str, Artifact] = {}

    @property
    def run_id(self) -> str:
        return self._run_id

    def create(
        self,
        content: object,
        *,
        artifact_type: ArtifactType,
        source_type: SourceType,
        source_id: str | None,
        producer: str,
        created_step: int,
        sensitivity: Sensitivity,
        trust: Trust,
        parents: tuple[ParentLink, ...] = (),
        transformations: tuple[str, ...] = (),
        metadata: dict[str, JsonValue] | None = None,
    ) -> Artifact:
        identity = f"ART_{self.run_id}_{len(self._items) + 1:06d}"
        if len({p.parent_id for p in parents}) != len(parents):
            raise ValueError("duplicate parent")
        ancestors = [self.get(p.parent_id) for p in parents]
        if any(p.created_step > created_step for p in ancestors):
            raise ValueError("parent step cannot follow child step")
        joined_s = join_sensitivity(sensitivity, *(p.sensitivity for p in ancestors))
        joined_t = join_trust(trust, *(p.trust for p in ancestors))
        if joined_s != sensitivity or joined_t != trust:
            raise ValueError("derivation cannot declassify or upgrade trust")
        raw = canonical_json(content)
        artifact = Artifact(
            artifact_id=identity,
            run_id=self.run_id,
            artifact_type=artifact_type,
            raw_json=raw,
            source_type=source_type,
            source_id=source_id,
            producer=producer,
            created_step=created_step,
            sensitivity=sensitivity,
            trust=trust,
            parents=parents,
            transformations=transformations,
            content_hash=content_hash(raw),
            metadata_json=canonical_json(metadata if metadata is not None else {}),
        )
        self._items[identity] = artifact
        return artifact

    def get(self, identity: str) -> Artifact:
        if identity not in self._items:
            raise ValueError("unknown, future or cross-run parent/artifact")
        return self._items[identity]

    def all(self) -> tuple[Artifact, ...]:
        return tuple(self._items.values())

    def parents(self, identity: str) -> tuple[Artifact, ...]:
        return tuple(self.get(p.parent_id) for p in self.get(identity).parents)

    def children(self, identity: str) -> tuple[Artifact, ...]:
        self.get(identity)
        return tuple(a for a in self.all() if any(p.parent_id == identity for p in a.parents))

    def ancestors(self, identity: str) -> tuple[Artifact, ...]:
        pending = [p.artifact_id for p in self.parents(identity)]
        found: set[str] = set()
        while pending:
            parent = pending.pop()
            if parent not in found:
                found.add(parent)
                pending.extend(p.artifact_id for p in self.parents(parent))
        return tuple(a for a in self.all() if a.artifact_id in found)

    def edges(self) -> tuple[Edge, ...]:
        return tuple(
            Edge(
                run_id=self.run_id,
                parent_id=p.parent_id,
                child_id=a.artifact_id,
                relation=p.relation,
            )
            for a in self.all()
            for p in a.parents
        )

    def normalized_view(self, identity: str, result: NormalizationResult) -> Artifact:
        original = self.get(identity)
        if original.content() != result.raw_text:
            raise ValueError("normalization must refer to the exact raw artifact")
        if normalize(result.raw_text, result.profile) != result:
            raise ValueError("normalization result/version integrity mismatch")
        return self.create(
            result.normalized_text,
            artifact_type=ArtifactType.NORMALIZED_VIEW,
            source_type=original.source_type,
            source_id=original.source_id,
            producer="normalizer_v1",
            created_step=original.created_step,
            sensitivity=original.sensitivity,
            trust=original.trust,
            parents=(ParentLink(parent_id=identity, relation=Relation.NORMALIZED_FROM),),
            transformations=(result.profile,),
            metadata={
                "profile": result.profile,
                "input_hash": result.input_hash,
                "output_hash": result.output_hash,
                "cache_key": result.cache_key,
                "unicode_version": result.unicode_version,
            },
        )

    def serialize(self) -> str:
        return "".join(a.model_dump_json() + "\n" for a in self.all())

    @classmethod
    def deserialize(cls, run_id: str, payload: str) -> Self:
        store = cls(run_id)
        for line in payload.splitlines():
            supplied = Artifact.model_validate_json(line)
            restored = store.create(
                supplied.content(),
                artifact_type=supplied.artifact_type,
                source_type=supplied.source_type,
                source_id=supplied.source_id,
                producer=supplied.producer,
                created_step=supplied.created_step,
                sensitivity=supplied.sensitivity,
                trust=supplied.trust,
                parents=supplied.parents,
                transformations=supplied.transformations,
                metadata=json.loads(supplied.metadata_json),
            )
            if restored != supplied:
                raise ValueError("invalid imported identity/order or record")
        return store

    def export(self, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=False)
        with (destination / "artifacts.jsonl").open("x", encoding="utf-8") as stream:
            stream.write(self.serialize())
        with (destination / "provenance_edges.jsonl").open("x", encoding="utf-8") as stream:
            stream.write("".join(e.model_dump_json() + "\n" for e in self.edges()))
