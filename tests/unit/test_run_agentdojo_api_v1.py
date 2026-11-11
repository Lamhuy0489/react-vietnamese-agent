"""AgentDojo runner helpers that work without the agentdojo venv."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "run_agentdojo_api_v1", ROOT / "scripts/run_agentdojo_api_v1.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extra_body_is_added_and_merged() -> None:
    seen: list[dict[str, Any]] = []
    inner = SimpleNamespace(create=lambda **kw: seen.append(kw) or "ok")
    raw = SimpleNamespace(chat=SimpleNamespace(completions=inner), models="m")
    mod = _load()
    client = mod.ClientWithExtras(raw, {"chat_template_kwargs": {"enable_thinking": False}})
    assert client.chat.completions.create(model="x", extra_body={"top_k": 1}) == "ok"
    assert seen[0]["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False},
                                     "top_k": 1}
    assert client.models == "m"
    plain = mod.ClientWithExtras(raw, {})
    plain.chat.completions.create(model="x")
    assert "extra_body" not in seen[1]


def test_model_spec_resolves_v2_entries() -> None:
    mod = _load()
    spec = mod.model_spec(ROOT / "configs/models/backbones_v3.yaml", "qwen3_8b")
    assert spec["repo"] == "Qwen/Qwen3-8B"
    assert spec["chat_template_kwargs"] == {"enable_thinking": False}


def test_served_model_matches_repo() -> None:
    mod = _load()
    client = SimpleNamespace(models=SimpleNamespace(list=lambda: SimpleNamespace(
        data=[SimpleNamespace(id="Qwen/Qwen3-8B@abc")])))
    assert mod.served_model(client, "Qwen/Qwen3-8B") == "Qwen/Qwen3-8B@abc"
