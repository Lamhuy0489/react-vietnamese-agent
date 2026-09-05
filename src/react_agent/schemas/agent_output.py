"""Strict observable model-output schemas; no hidden-reasoning fields."""

from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    arguments: dict[str, object]


class ActionTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Action


class FinalAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)


class FinalTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    final_answer: FinalAnswer


AgentTurn: TypeAlias = ActionTurn | FinalTurn
