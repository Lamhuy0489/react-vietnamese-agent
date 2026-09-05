"""Deterministic CPU-only backend for unit tests."""

from __future__ import annotations

import json

from react_agent.llm.base import GenerationConfig, ModelResponse


class DummyBackend:
    model_id = "dummy"
    model_revision = "phase1_v1"

    def __init__(self, answer: str = "Tác vụ smoke đã hoàn tất.") -> None:
        self.answer = answer

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        del messages, config
        text = json.dumps({"final_answer": {"answer": self.answer}}, ensure_ascii=False)
        return ModelResponse(
            text=text,
            model_id=self.model_id,
            model_revision=self.model_revision,
        )
