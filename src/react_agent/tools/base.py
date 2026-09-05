"""Shared typed mock-tool interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from react_agent.schemas.tool import ToolError, ToolResult

InputT = TypeVar("InputT", bound=BaseModel)


class ToolExecutionError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


class BaseTool(ABC, Generic[InputT]):
    name: str
    description: str
    input_model: type[InputT]

    @property
    def input_schema(self) -> dict[str, Any]:
        return self.input_model.model_json_schema()

    def validate_arguments(self, arguments: dict[str, object]) -> InputT:
        return self.input_model.model_validate(arguments)

    def execute(self, call_id: str, arguments: dict[str, object]) -> ToolResult:
        try:
            validated = self.validate_arguments(arguments)
        except ValidationError as exc:
            return ToolResult(
                call_id=call_id,
                tool_name=self.name,
                ok=False,
                error=ToolError(
                    code="INVALID_ARGUMENTS",
                    message=str(exc),
                    retryable=True,
                ),
            )
        try:
            content = self._run(validated)
        except ToolExecutionError as exc:
            return ToolResult(
                call_id=call_id,
                tool_name=self.name,
                ok=False,
                error=ToolError(
                    code=exc.code,
                    message=exc.message,
                    retryable=exc.retryable,
                ),
            )
        return ToolResult(call_id=call_id, tool_name=self.name, ok=True, content=content)

    @abstractmethod
    def _run(self, arguments: InputT) -> object: ...
