"""Typed unsplit Phase 3 workbench inputs; private QA never enters RuntimeTask."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from react_agent.schemas.agent_output import Action


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PublicWorkbenchTask(StrictRecord):
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    instruction: str = Field(min_length=1)


class OverlayScenario(StrictRecord):
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    attack_category: Literal[
        "indirect_injection", "tool_output_poisoning", "data_exfiltration", "policy_violation"
    ]
    source_type: Literal["document", "cached_page", "database_text_field", "tool_output"]
    source_id: str = Field(pattern=r"^AWB_[A-Z]+$")
    trust: Literal["T0", "T1", "T2"]
    sensitivity: Literal["S0", "S1", "S2"]
    title: str = Field(min_length=1)
    base_content: str = Field(min_length=1)
    attack_text: str = Field(min_length=1)
    benign_text: str = Field(min_length=1)
    sensitive_value: str | None = None
    trigger: Action
    review_status: Literal["pending"] = "pending"

    @model_validator(mode="after")
    def check_location(self) -> Self:
        tool = {
            "document": "doc_read",
            "cached_page": "cached_fetch",
            "database_text_field": "db_query",
            "tool_output": "calculator",
        }[self.source_type]
        if self.trigger.name != tool or self.attack_text == self.benign_text:
            raise ValueError("source trigger must match source type and pair texts must differ")
        if self.source_type == "document" and self.trigger.arguments != {"doc_id": self.source_id}:
            raise ValueError("document trigger identity mismatch")
        if self.source_type == "cached_page" and self.trigger.arguments != {
            "page_id": self.source_id
        }:
            raise ValueError("page trigger identity mismatch")
        if self.sensitive_value and self.source_type != "database_text_field":
            raise ValueError("workbench sensitive field is supported only on the copied DB row")
        return self


class SinkGrant(StrictRecord):
    tool: Literal["send_email_mock", "post_webhook_mock"]
    destination: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_synthetic_destination(self) -> Self:
        if self.tool == "send_email_mock" and not self.destination.endswith("@example.test"):
            raise ValueError("fixture email destination must be synthetic @example.test")
        if self.tool == "post_webhook_mock" and not self.destination.startswith("mock://"):
            raise ValueError("fixture webhook destination must use mock://")
        return self


class SensitiveArtifact(StrictRecord):
    artifact_id: str = Field(min_length=1)
    value: str = Field(min_length=8)
    sensitivity: Literal["S2"] = "S2"
    trust: Literal["T0", "T1", "T2"] = "T0"
    read_action: Action


class PrivateWorkbenchOracle(StrictRecord):
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    allowed_read_tools: list[
        Literal["doc_search", "doc_read", "cached_search", "cached_fetch", "db_query", "calculator"]
    ]
    sink_grants: list[SinkGrant]
    forbidden_actions: list[Action] = Field(default_factory=list)
    required_facts: list[str] = Field(min_length=1)
    required_sink_actions: list[Action]
    sensitive_artifacts: list[SensitiveArtifact]
    safe_actions: list[Action] = Field(min_length=1)
    safe_final: str = Field(min_length=1)
    negative_actions: list[Action] = Field(min_length=1)
    negative_final: str = Field(min_length=1)
    expected_negative: Literal["executed_violation", "final_leakage"]
