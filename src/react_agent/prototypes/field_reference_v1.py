"""Host-rendered text references with explicit dataflow; not a full A6 runtime."""

from __future__ import annotations

import base64
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from react_agent.broker.tool_broker import ToolBroker
from react_agent.foundation.artifacts import (
    Artifact,
    ArtifactStore,
    ArtifactType,
    Immutable,
    ParentLink,
    Relation,
    Sensitivity,
    SourceType,
    canonical_json,
    join_sensitivity,
    join_trust,
)
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.schemas.agent_output import Action

HASH = r"^[0-9a-f]{64}$"
LIMIT = 65536


class Selector(Immutable):
    source_id: str = Field(min_length=1, max_length=128)
    path: Literal["/content", "/title"]


class Grant(Immutable):
    run_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    task_id: str = Field(min_length=1, max_length=128)
    user_sha256: str = Field(pattern=HASH)
    catalog_sha256: str = Field(pattern=HASH)
    readable: tuple[str, ...] = Field(min_length=1, max_length=16)
    outputs: tuple[Selector, ...] = Field(min_length=1, max_length=32)
    clearance: Literal["S0"] = "S0"

    @model_validator(mode="after")
    def unique_scopes(self) -> Grant:
        if len(set(self.readable)) != len(self.readable) or len({
            (s.source_id, s.path) for s in self.outputs
        }) != len(self.outputs) or any(s.source_id not in self.readable for s in self.outputs):
            raise ValueError("unique readable/output scope required")
        return self

    @property
    def sha256(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))


class Reference(Immutable):
    run_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    grant_sha256: str = Field(pattern=HASH)
    artifact_id: str = Field(min_length=1, max_length=256)
    source_sha256: str = Field(pattern=HASH)
    path: Literal["/content", "/title"]
    value_type: Literal["text"] = "text"


class Plan(Immutable):
    refs: tuple[Reference, ...] = Field(min_length=1, max_length=8)
    separator: Literal["", " ", "\n"] = ""
    transforms: tuple[Literal["base64", "hex"], ...] = Field(default=(), max_length=4)


class FinalDecision(Immutable):
    allowed: bool
    reason: str
    output: str | None = None
    rendered_artifact_id: str | None = None
    effective_sensitivity: Sensitivity | None = None


class ReferenceError(ValueError):
    """Closed reference/budget boundary; errors never echo source content."""


class Session:
    def __init__(self, broker: ToolBroker, catalog: SourceCatalog, raw_user: str,
                 grant: Grant, expected_grant_sha256: str) -> None:
        self.grant = Grant.model_validate(grant.model_dump(mode="json"))
        self.catalog = SourceCatalog.model_validate(catalog.model_dump(mode="json"))
        if (self.grant.sha256 != expected_grant_sha256
                or text_hash(raw_user) != self.grant.user_sha256
                or text_hash(canonical_json(self.catalog.model_dump(mode="json")))
                != self.grant.catalog_sha256):
            raise ReferenceError("host grant/user/catalog pin mismatch")
        self.broker = broker
        self.store = ArtifactStore(grant.run_id)
        self._admitted: dict[str, Artifact] = {}
        self._step = 0
        self._reads = 0
        self.decisions: list[FinalDecision] = []

    def read_document(self, source_id: str) -> Reference:
        if source_id not in self.grant.readable or self._reads >= 64:
            raise ReferenceError("read outside host scope/budget")
        action = Action(name="doc_read", arguments={"doc_id": source_id})
        label = self.catalog.resolve(action)
        if label.source_type != SourceType.DOCUMENT or label.source_id != source_id:
            raise ReferenceError("explicit document metadata required")
        self._reads += 1
        self._step += 1
        result = self.broker.execute("doc_read", {"doc_id": source_id},
                                     run_id=self.grant.run_id, task_id=self.grant.task_id,
                                     step=self._step)
        content = result.content
        if (not result.ok or result.tool_name != "doc_read" or not isinstance(content, dict)
                or set(content) != {"doc_id", "title", "content"}
                or not all(type(v) is str for v in content.values())
                or content["doc_id"] != source_id
                or len(canonical_json(content).encode()) > LIMIT):
            raise ReferenceError("successful bounded raw document required")
        artifact = self.store.create(
            content, artifact_type=ArtifactType.DOCUMENT_CONTENT, source_type=SourceType.DOCUMENT,
            source_id=source_id, producer="field_reference_broker_snapshot_v1",
            created_step=self._step, sensitivity=label.sensitivity, trust=label.trust,
            metadata={"tool": "doc_read", "call_id": result.call_id,
                      "grant_sha256": self.grant.sha256},
        )
        self._admitted[artifact.artifact_id] = artifact
        return Reference(run_id=self.grant.run_id, grant_sha256=self.grant.sha256,
                         artifact_id=artifact.artifact_id, source_sha256=artifact.content_hash,
                         path="/content")

    def _select(self, ref: Reference) -> tuple[Artifact, str]:
        if ref.run_id != self.grant.run_id or ref.grant_sha256 != self.grant.sha256:
            raise ReferenceError("reference ownership mismatch")
        source = self._admitted.get(ref.artifact_id)
        if source is None or source.content_hash != ref.source_sha256:
            raise ReferenceError("unknown or changed source")
        if not any(s.source_id == source.source_id and s.path == ref.path
                   for s in self.grant.outputs):
            raise ReferenceError("field outside output scope")
        value = source.content()
        if not isinstance(value, dict) or not isinstance(value.get(ref.path[1:]), str):
            raise ReferenceError("text field required")
        return source, str(value[ref.path[1:]])

    def finalize(self, proposal: object, *, arm: Literal["exposure", "selected"] = "selected",
                 upstream_allowed: bool = False) -> FinalDecision:
        """Parse untrusted plan; host-only policy/veto parameters are not model fields."""
        if arm not in {"exposure", "selected"}:
            raise ValueError("known component arm required")
        try:
            plan = Plan.model_validate(proposal)
            # Revalidate instances as well (model_copy can bypass pydantic validation).
            plan = Plan.model_validate(plan.model_dump(mode="json"))
            selected = [self._select(ref) for ref in plan.refs]
            text = plan.separator.join(value for _, value in selected)
            if len(text.encode()) > LIMIT:
                raise ReferenceError("output byte budget")
            for operation in plan.transforms:
                data = text.encode()
                if (4 * ((len(data) + 2) // 3) if operation == "base64" else 2 * len(data)) > LIMIT:
                    raise ReferenceError("transform byte budget")
                text = (base64.b64encode(data).decode() if operation == "base64" else data.hex())
            sources = {source.artifact_id: source for source, _ in selected}
            sensitivity = join_sensitivity(*(s.sensitivity for s in sources.values()))
            trust = join_trust(*(s.trust for s in sources.values()))
            self._step += 1
            rendered = self.store.create(
                text, artifact_type=ArtifactType.FINAL_RESPONSE, source_type=SourceType.SYSTEM,
                source_id=None, producer="host_field_renderer_v1", created_step=self._step,
                sensitivity=sensitivity, trust=trust,
                parents=tuple(ParentLink(parent_id=s, relation=Relation.EXTRACTED_FROM)
                              for s in sources), transformations=plan.transforms,
                metadata={"grant_sha256": self.grant.sha256,
                          "plan_sha256": text_hash(canonical_json(plan.model_dump(mode="json"))),
                          "exposure_ids": list(self._admitted)},
            )
            effective = (join_sensitivity(*(a.sensitivity for a in self._admitted.values()))
                         if arm == "exposure" else sensitivity)
            allowed = upstream_allowed is True and effective == Sensitivity.PUBLIC
            reason = "allow" if allowed else (
                "upstream_veto" if upstream_allowed is not True else "sensitivity")
            decision = FinalDecision(allowed=allowed, reason=reason,
                                     output=text if allowed else None,
                                     rendered_artifact_id=rendered.artifact_id,
                                     effective_sensitivity=effective)
        except (ValidationError, ReferenceError):
            decision = FinalDecision(allowed=False, reason="invalid_reference_plan")
        self.decisions.append(decision)
        return decision
