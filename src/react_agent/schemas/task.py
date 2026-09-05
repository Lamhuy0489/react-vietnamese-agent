"""Schema for the non-benchmark Phase 1 smoke tasks."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class RuntimeTask(Protocol):
    """Minimal public task view accepted by the model-facing runtime."""

    task_id: str
    instruction: str


class ExpectedBehavior(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acceptable_tool_sequences: list[list[str]]
    required_answer_facts: list[str] = Field(default_factory=list)


class SmokeTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(pattern=r"^smoke_[0-9]{3}$")
    instruction: str = Field(min_length=1)
    category: str = Field(min_length=1)
    expected: ExpectedBehavior
    fixture_version: str = "phase1_v1"
    author: str = Field(pattern=r"^(huy|minh)$")
