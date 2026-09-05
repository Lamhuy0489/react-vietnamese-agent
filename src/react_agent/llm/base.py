"""Backend-independent generation contracts."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class GenerationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(default=0.0, ge=0.0)
    max_new_tokens: int = Field(default=512, ge=1)
    seed: int = 42


class ModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    model_id: str
    model_revision: str


class LLMBackend(Protocol):
    model_id: str
    model_revision: str

    def generate(
        self, messages: list[dict[str, str]], config: GenerationConfig
    ) -> ModelResponse: ...
