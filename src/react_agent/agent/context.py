"""Build model-neutral context in one deterministic order."""

from __future__ import annotations

import json

from react_agent.prompts import A0_SYSTEM_PROMPT
from react_agent.schemas.task import RuntimeTask


class ContextBuilder:
    def __init__(self, tool_definitions: list[dict[str, object]]) -> None:
        self._tool_definitions = tool_definitions

    def build(
        self,
        task: RuntimeTask,
        history: list[tuple[str, str]],
        correction: str | None = None,
    ) -> list[dict[str, str]]:
        tools = json.dumps(self._tool_definitions, ensure_ascii=False, sort_keys=True)
        messages = [
            {"role": "system", "content": f"{A0_SYSTEM_PROMPT}\nCông cụ:\n{tools}"},
            {"role": "user", "content": task.instruction},
        ]
        for action, observation in history:
            messages.append({"role": "assistant", "content": action})
            messages.append({"role": "user", "content": f"OBSERVATION: {observation}"})
        if correction is not None:
            messages.append({"role": "user", "content": correction})
        return messages
