"""Unsplit authoring metadata and private scope oracle, separate from runtime task."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, model_validator

from react_agent.schemas.adversarial_workbench import (
    PrivateWorkbenchOracle,
    SinkGrant,
    StrictRecord,
)


class ArtifactSinkGrant(SinkGrant):
    artifact_ids: list[str] = Field(min_length=1)


class DataScope(StrictRecord):
    document_ids: list[str] = Field(default_factory=list)
    cached_page_ids: list[str] = Field(default_factory=list)
    sql_columns: dict[str, list[str]] = Field(default_factory=dict)
    sink_artifacts: list[ArtifactSinkGrant] = Field(default_factory=list)
    final_artifacts: list[str] = Field(default_factory=list)


class ScopedOracle(PrivateWorkbenchOracle):
    scope: DataScope

    @model_validator(mode="after")
    def check_artifact_references(self) -> Self:
        identities = {a.artifact_id for a in self.sensitive_artifacts}
        if len(identities) != len(self.sensitive_artifacts):
            raise ValueError("duplicate sensitive artifact ID")
        references = set(self.scope.final_artifacts)
        for grant in self.scope.sink_artifacts:
            references.update(grant.artifact_ids)
            if not any(
                g.tool == grant.tool and g.destination == grant.destination
                for g in self.sink_grants
            ):
                raise ValueError("artifact grant requires a matching destination grant")
        if not references <= identities:
            raise ValueError("scope refers to unknown sensitive artifact")
        for table, columns in self.scope.sql_columns.items():
            if not table or not columns or len(columns) != len(set(columns)):
                raise ValueError("SQL scope requires nonempty unique columns per table")
        return self


class CandidateMetadata(StrictRecord):
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    family_id: str = Field(pattern=r"^CAND_[A-Z]+$")
    semantic_group: str = Field(min_length=1)
    template_group: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    mechanism: str = Field(min_length=20)
    lineage: Literal["adapted_workbench_v2", "new_authored_candidate"]
    split: Literal["unassigned"] = "unassigned"
    review_status: Literal["pending"] = "pending"
    authoring_method: Literal["assistant_authored_owner_workflow"] = (
        "assistant_authored_owner_workflow"
    )
