"""Replay captured observable outputs without a GPU."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from react_agent.llm.base import GenerationConfig, ModelResponse


class ReplayBackend:
    model_id = "replay"
    model_revision = "phase1_v1"

    def __init__(self, responses: Iterable[str]) -> None:
        self._responses = deque(responses)

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        del messages, config
        if not self._responses:
            raise RuntimeError("ReplayBackend has no response remaining")
        return ModelResponse(
            text=self._responses.popleft(),
            model_id=self.model_id,
            model_revision=self.model_revision,
        )
