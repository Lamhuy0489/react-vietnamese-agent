"""Load checked-in YAML configuration into typed contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from react_agent.agent.state import RuntimeConfig
from react_agent.llm.base import GenerationConfig


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"configuration must be a mapping: {path}")
    return payload


def load_runtime_config(path: Path) -> RuntimeConfig:
    payload = load_yaml(path)
    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        raise ValueError("runtime configuration is missing")
    return RuntimeConfig(config_id=str(payload.get("id", "A0")), **runtime)


def load_generation_config(path: Path) -> GenerationConfig:
    return GenerationConfig.model_validate(load_yaml(path))
