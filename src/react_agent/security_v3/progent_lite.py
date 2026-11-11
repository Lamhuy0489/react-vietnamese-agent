"""Baseline PRG: Progent-style privilege policy, deterministic ("lite"), Study 2 WP7.

Progent (Shi et al., 2025) restricts which tools an agent may call and with which
arguments, using a policy derived from the user's request before the agent runs. Plan
WP7 fixes a deterministic variant with no LLM in the loop:

- read tools (search, read, query, calculator) are always allowed;
- a sink call (``send_email_mock``, ``post_webhook_mock``) is allowed only when its
  destination occurs literally (case-insensitive) in the user's instruction;
- a denied call is not executed; the agent gets ``POLICY_DENIED`` and may continue.

The policy is built from the public task instruction only; it never sees oracles. It is
the tool-level part of D2 rule 2 without D2's data-flow rules, so the two are compared
on the same footing.
"""

from __future__ import annotations

from typing import Any, cast

from pydantic import BaseModel

from react_agent.schemas.tool import ToolError, ToolResult
from react_agent.tools.base import BaseTool
from react_agent.tools.registry import ToolRegistry

SINKS = {"send_email_mock": "to", "post_webhook_mock": "endpoint"}
DENIED = "Đích này không có trong yêu cầu của người dùng; lệnh không được thực hiện."


class PolicyTool(BaseTool[BaseModel]):
    """A sink tool that runs only for destinations the user's instruction names."""

    input_model = BaseModel

    def __init__(self, wrapped: BaseTool[Any], instruction: str) -> None:
        self._wrapped, self._instruction = wrapped, instruction.casefold()
        self.name, self.description = wrapped.name, wrapped.description
        self.input_model = wrapped.input_model
        self.denied = 0

    @property
    def input_schema(self) -> dict[str, Any]:
        return self._wrapped.input_schema

    def validate_arguments(self, arguments: dict[str, object]) -> BaseModel:
        return cast(BaseModel, self._wrapped.validate_arguments(arguments))

    def allowed(self, arguments: dict[str, object]) -> bool:
        destination = str(arguments.get(SINKS[self.name], "")).strip().casefold()
        return bool(destination) and destination in self._instruction

    def execute(self, call_id: str, arguments: dict[str, object]) -> ToolResult:
        if not self.allowed(arguments):
            self.denied += 1
            return ToolResult(call_id=call_id, tool_name=self.name, ok=False, error=ToolError(
                code="POLICY_DENIED", retryable=False,
                message=DENIED))
        return self._wrapped.execute(call_id, arguments)

    def _run(self, arguments: BaseModel) -> object:
        raise RuntimeError("policy tool delegates via execute")


def apply_progent_lite(registry: ToolRegistry, instruction: str) -> ToolRegistry:
    wrapped = ToolRegistry()
    for name in registry.names:
        tool = registry.get(name)
        if tool is None:
            raise RuntimeError("registry changed during construction")
        wrapped.register(PolicyTool(tool, instruction) if name in SINKS else tool)
    return wrapped
