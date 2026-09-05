"""Contracts shared by the parser, broker, and all mock tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_id: str = Field(pattern=r"^call_[0-9]{6}$")
    name: str = Field(min_length=1)
    arguments: dict[str, object]


class ToolError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    retryable: bool


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_id: str
    tool_name: str
    ok: bool
    content: Any | None = None
    error: ToolError | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.ok and self.error is not None:
            raise ValueError("successful ToolResult cannot contain an error")
        if not self.ok and self.error is None:
            raise ValueError("failed ToolResult must contain an error")
