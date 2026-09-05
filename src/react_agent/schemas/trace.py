"""Observable JSONL trace event contract."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

EventName = Literal[
    "run_start",
    "model_output",
    "parse_error",
    "tool_call_proposed",
    "tool_call_executed",
    "tool_result",
    "final_answer",
    "run_end",
]


class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    task_id: str
    step: int = Field(ge=0)
    event: EventName
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    call_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
