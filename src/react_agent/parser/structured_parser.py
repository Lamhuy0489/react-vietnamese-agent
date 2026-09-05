"""Parse exactly one action or final-answer JSON object."""

from __future__ import annotations

import json
from dataclasses import dataclass

from pydantic import TypeAdapter, ValidationError

from react_agent.schemas.agent_output import ActionTurn, AgentTurn, FinalTurn
from react_agent.tools.registry import ToolRegistry


@dataclass(frozen=True)
class ParseError(Exception):
    code: str
    message: str
    retryable: bool = True

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class StructuredParser:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry
        self._adapter: TypeAdapter[AgentTurn] = TypeAdapter(ActionTurn | FinalTurn)

    def parse(self, raw_output: str) -> AgentTurn:
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ParseError("INVALID_JSON", "Output must be exactly one JSON object.") from exc

        try:
            turn = self._adapter.validate_python(payload)
        except ValidationError as exc:
            raise ParseError("INVALID_SCHEMA", "Output does not match AgentOutput schema.") from exc

        if isinstance(turn, ActionTurn):
            tool = self._registry.get(turn.action.name)
            if tool is None:
                raise ParseError("UNKNOWN_TOOL", f"Unknown tool: {turn.action.name}")
            try:
                tool.validate_arguments(turn.action.arguments)
            except ValidationError as exc:
                raise ParseError(
                    "INVALID_ARGUMENTS",
                    f"Invalid arguments for tool: {turn.action.name}",
                ) from exc
        return turn
