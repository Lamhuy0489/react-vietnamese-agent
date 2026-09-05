"""Registry avoids tool-name conditionals in runtime and broker."""

from __future__ import annotations

from typing import Any

from react_agent.tools.base import BaseTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool[Any]] = {}

    def register(self, tool: BaseTool[Any]) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool registration: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool[Any] | None:
        return self._tools.get(name)

    def definitions(self) -> list[dict[str, object]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for _, tool in sorted(self._tools.items())
        ]

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))
