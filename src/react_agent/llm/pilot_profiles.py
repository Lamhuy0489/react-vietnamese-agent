"""Predeclared Dev pilot conditions; no dependency on evaluator labels."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PilotProfile:
    source: str
    chat_adapter: str = "native"

    @property
    def model_id(self) -> str:
        return "/".join(self.source.split("/")[:2])

    @property
    def revision(self) -> str:
        return "/".join(self.source.split("/")[2:])


PROFILES = {
    "qwen": PilotProfile("qwen-lm/qwen2.5/transformers/3b-instruct/1"),
    "gemma": PilotProfile("google/gemma-2/transformers/gemma-2-2b-it/2", "gemma_system_to_user_v1"),
    "llama": PilotProfile("metaresearch/llama-3.2/transformers/3b-instruct/1"),
    "qwen7b": PilotProfile("qwen-lm/qwen2.5/transformers/7b-instruct/1"),
    "gemma4": PilotProfile("google/gemma-4/transformers/gemma-4-e4b-it/1"),
}


def adapt_messages(messages: list[dict[str, str]], adapter: str) -> list[dict[str, str]]:
    """Preserve text/order while satisfying Gemma's user/assistant-only template."""
    if adapter == "native":
        return [dict(message) for message in messages]
    if adapter != "gemma_system_to_user_v1":
        raise ValueError(f"unknown chat adapter: {adapter}")
    result: list[dict[str, str]] = []
    for index, message in enumerate(messages):
        role = message["role"]
        if role == "system":
            if index != 0:
                raise ValueError("system message must be first")
            role = "user"
        if role not in {"user", "assistant"}:
            raise ValueError(f"unsupported role: {role}")
        if result and result[-1]["role"] == role:
            result[-1]["content"] += "\n\n" + message["content"]
        else:
            result.append({"role": role, "content": message["content"]})
    if not result or result[0]["role"] != "user" or result[-1]["role"] != "user":
        raise ValueError("generation requires a user-first, user-last conversation")
    return result


def find_pilot_model(root: Path, profile: PilotProfile) -> Path:
    """Resolve the pinned Kaggle mount, rejecting missing or ambiguous models."""
    suffix = tuple(profile.source.split("/")[1:])
    candidates = [
        path.parent
        for path in root.rglob("config.json")
        if tuple(part.casefold() for part in path.parent.parts[-4:]) == suffix
    ]
    if len(candidates) != 1:
        raise ValueError(f"expected one pinned model mount for {profile.source}")
    path = candidates[0]
    required = ["config.json", "tokenizer_config.json", "tokenizer.json"]
    if any(not (path / name).is_file() for name in required):
        raise ValueError("missing model/tokenizer metadata")
    if (
        not (path / "model.safetensors").is_file()
        and not (path / "model.safetensors.index.json").is_file()
    ):
        raise ValueError("missing safetensors weights/index")
    return path
