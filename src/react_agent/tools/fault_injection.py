"""Deterministic tool-fault adapter for benchmark recovery scenarios."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from react_agent.schemas.clean_task import FaultSpec
from react_agent.schemas.tool import ToolError, ToolResult
from react_agent.tools.base import BaseTool


class FaultInjectingTool(BaseTool[BaseModel]):
    """Wrap a tool and inject only the private, occurrence-indexed fault plan."""

    input_model = BaseModel

    def __init__(self, wrapped: BaseTool[Any], faults: list[FaultSpec]) -> None:
        self._wrapped = wrapped
        self._faults = {fault.occurrence: fault for fault in faults}
        self._occurrence = 0
        self.name = wrapped.name
        self.description = wrapped.description

    @property
    def input_schema(self) -> dict[str, Any]:
        return self._wrapped.input_schema

    def execute(self, call_id: str, arguments: dict[str, object]) -> ToolResult:
        self._occurrence += 1
        fault = self._faults.get(self._occurrence)
        if fault is not None:
            return ToolResult(
                call_id=call_id,
                tool_name=self.name,
                ok=False,
                error=ToolError(
                    code=fault.error_code,
                    message=f"Deterministic benchmark fault at occurrence {self._occurrence}.",
                    retryable=fault.retryable,
                ),
                metadata={"injected": True, "occurrence": self._occurrence},
            )
        return self._wrapped.execute(call_id, arguments)

    def _run(self, arguments: BaseModel) -> object:
        raise RuntimeError("FaultInjectingTool delegates through execute()")
