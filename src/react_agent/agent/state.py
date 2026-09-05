"""Runtime configuration and terminal result contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TerminalStatus = Literal["completed", "parse_failure", "max_steps", "model_error"]


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config_id: str = "A0"
    max_steps: int = Field(default=8, ge=1, le=32)
    max_format_retries_per_step: int = Field(default=2, ge=0, le=5)
    tool_timeout_seconds: float = Field(default=5.0, gt=0, le=60)


class RunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    task_id: str
    status: TerminalStatus
    steps: int = Field(ge=0)
    final_answer: str | None = None
    tool_sequence: list[str]
    parse_errors: int = Field(ge=0)
