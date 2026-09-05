"""Thin optional Hugging Face pipeline adapter intended for Kaggle."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from react_agent.llm.base import GenerationConfig, ModelResponse


class HFBackend:
    """Adapt a preloaded text-generation callable without importing Transformers."""

    def __init__(
        self,
        generator: Callable[..., Any],
        *,
        model_id: str,
        model_revision: str,
    ) -> None:
        self._generator = generator
        self.model_id = model_id
        self.model_revision = model_revision

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        output = self._generator(
            messages,
            max_new_tokens=config.max_new_tokens,
            temperature=config.temperature,
            do_sample=config.temperature > 0,
        )
        text = self._extract_text(output)
        return ModelResponse(
            text=text,
            model_id=self.model_id,
            model_revision=self.model_revision,
        )

    @staticmethod
    def _extract_text(output: Any) -> str:
        if isinstance(output, str):
            return output
        if isinstance(output, list) and output and isinstance(output[0], dict):
            generated = output[0].get("generated_text")
            if isinstance(generated, str):
                return generated
            if isinstance(generated, list) and generated:
                content = generated[-1].get("content")
                if isinstance(content, str):
                    return content
        raise TypeError("unsupported Hugging Face pipeline output")
