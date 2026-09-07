"""Immutable control/context records, independent of artifact content."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from react_agent.foundation.artifacts import Immutable


class ControlState(Immutable):
    run_id: str
    task_id: str
    step: int = Field(default=0, ge=0)
    status: Literal["running", "completed", "parse_failure", "max_steps", "model_error"] = "running"
    model_turn_count: int = Field(default=0, ge=0)
    tool_call_count: int = Field(default=0, ge=0)
    format_retry_count: int = Field(default=0, ge=0)
    parse_error_count: int = Field(default=0, ge=0)
    proposed_tool: str | None = None
    active_call_id: str | None = None
    called_tools: tuple[str, ...] = ()
    terminal_reason: str | None = None


class ContextMessage(Immutable):
    role: Literal["system", "user", "assistant"]
    content: str
    artifact_id: str


class ContextBundle(Immutable):
    run_id: str
    step: int = Field(ge=1)
    model_turn: int = Field(ge=1)
    messages: tuple[ContextMessage, ...]

    @property
    def artifact_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(message.artifact_id for message in self.messages))

    def model_messages(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.messages]


class Decision(Immutable):
    effect: Literal["ALLOW", "DENY", "TRANSFORM"] = "ALLOW"
    policy: str = "A0_PASS_THROUGH"
    reason_code: str = "METADATA_ONLY"


class FoundationEvent(Immutable):
    schema_version: Literal["foundation_trace_v2"] = "foundation_trace_v2"
    run_id: str
    task_id: str
    sequence: int = Field(ge=1)
    step: int = Field(ge=0)
    event: Literal["context", "artifact", "control", "policy_decision", "normalization"]
    data_json: str
