"""Host metadata and pass-through hook extension points; no security enforcement."""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import model_validator

from react_agent.foundation.artifacts import (
    Artifact,
    ArtifactStore,
    ArtifactType,
    Immutable,
    ParentLink,
    Relation,
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
    join_sensitivity,
    join_trust,
)
from react_agent.foundation.runtime_contracts import ControlState, Decision
from react_agent.schemas.agent_output import Action
from react_agent.schemas.tool import ToolResult


class SourceLabel(Immutable):
    source_type: SourceType
    source_id: str
    sensitivity: Sensitivity
    trust: Trust
    legacy_trust: str | None = None


class SourceBinding(Immutable):
    tool: str
    arguments_json: str
    label: SourceLabel

    @model_validator(mode="after")
    def canonical_arguments(self) -> SourceBinding:
        data = json.loads(self.arguments_json)
        if not isinstance(data, dict) or canonical_json(data) != self.arguments_json:
            raise ValueError("host source binding requires canonical argument object")
        return self


class SourceCatalog(Immutable):
    version: str = "host_source_catalog_v1"
    bindings: tuple[SourceBinding, ...] = ()

    @model_validator(mode="after")
    def unique_binding(self) -> SourceCatalog:
        if len({(b.tool, b.arguments_json) for b in self.bindings}) != len(self.bindings):
            raise ValueError("ambiguous host source metadata")
        return self

    def resolve(self, action: Action) -> SourceLabel:
        arguments = canonical_json(action.arguments)
        for binding in self.bindings:
            if binding.tool == action.name and binding.arguments_json == arguments:
                return binding.label
        if action.name == "db_query":
            return SourceLabel(
                source_type=SourceType.DATABASE,
                source_id="database:unknown_scope",
                sensitivity=Sensitivity.CONFIDENTIAL,
                trust=Trust.TRUSTED,
            )
        if action.name in {"calculator", "send_email_mock", "post_webhook_mock"}:
            return SourceLabel(
                source_type=SourceType.CALCULATOR
                if action.name == "calculator"
                else SourceType.TOOL,
                source_id=action.name,
                sensitivity=Sensitivity.PUBLIC,
                trust=Trust.TRUSTED,
            )
        return SourceLabel(
            source_type=SourceType.TOOL,
            source_id=action.name + ":unknown_scope",
            sensitivity=Sensitivity.CONFIDENTIAL,
            trust=Trust.UNTRUSTED,
        )


def derive(
    store: ArtifactStore,
    content: object,
    *,
    kind: ArtifactType,
    parents: tuple[str, ...],
    step: int,
    relation: Relation = Relation.DERIVED_FROM,
    source_type: SourceType = SourceType.MODEL,
    producer: str = "runtime_v1",
    sensitivity: Sensitivity = Sensitivity.PUBLIC,
    trust: Trust = Trust.TRUSTED,
) -> Artifact:
    originals = tuple(store.get(identity) for identity in dict.fromkeys(parents))
    return store.create(
        content,
        artifact_type=kind,
        source_type=source_type,
        source_id=None,
        producer=producer,
        created_step=step,
        sensitivity=join_sensitivity(sensitivity, *(a.sensitivity for a in originals)),
        trust=join_trust(trust, *(a.trust for a in originals)),
        parents=tuple(ParentLink(parent_id=a.artifact_id, relation=relation) for a in originals),
    )


class PostResult(Immutable):
    result_json: str
    source_artifact_id: str
    result_artifact_id: str


class PreExecutionHook(Protocol):
    def evaluate(
        self, state: ControlState, action: Action, artifacts: tuple[Artifact, ...]
    ) -> Decision: ...


class PostExecutionHook(Protocol):
    def process(
        self,
        state: ControlState,
        action: Action,
        result: ToolResult,
        store: ArtifactStore,
        action_id: str,
        catalog: SourceCatalog,
    ) -> PostResult: ...


class FinalResponseHook(Protocol):
    def evaluate(self, state: ControlState, final: Artifact) -> Decision: ...


class AllowAllPreHook:
    def evaluate(
        self, state: ControlState, action: Action, artifacts: tuple[Artifact, ...]
    ) -> Decision:
        return Decision()


class AllowAllFinalHook:
    def evaluate(self, state: ControlState, final: Artifact) -> Decision:
        return Decision()


class RecordOnlyPostHook:
    def process(
        self,
        state: ControlState,
        action: Action,
        result: ToolResult,
        store: ArtifactStore,
        action_id: str,
        catalog: SourceCatalog,
    ) -> PostResult:
        label = catalog.resolve(action)
        kind = {
            SourceType.DOCUMENT: ArtifactType.DOCUMENT_CONTENT,
            SourceType.CACHED_PAGE: ArtifactType.CACHED_PAGE,
            SourceType.DATABASE: ArtifactType.DB_RESULT,
            SourceType.CALCULATOR: ArtifactType.CALCULATION_RESULT,
        }.get(label.source_type, ArtifactType.TOOL_RESULT)
        source = store.create(
            result.content if result.ok else result.model_dump(mode="json"),
            artifact_type=kind,
            source_type=label.source_type,
            source_id=label.source_id,
            producer="tool_source_snapshot",
            created_step=state.step,
            sensitivity=label.sensitivity,
            trust=label.trust,
            metadata={
                "call_id": result.call_id,
                "tool": action.name,
                "legacy_trust": label.legacy_trust,
                "label_origin": "host_catalog",
                "snapshot_root": True,
                "ok": result.ok,
            },
        )
        serialized = result.model_dump_json()
        observation = derive(
            store,
            serialized,
            kind=ArtifactType.TOOL_RESULT,
            parents=(source.artifact_id, action_id),
            step=state.step,
            source_type=SourceType.TOOL,
            producer="record_only_post",
        )
        return PostResult(
            result_json=serialized,
            source_artifact_id=source.artifact_id,
            result_artifact_id=observation.artifact_id,
        )
