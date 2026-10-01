"""Compose the native engine and lifecycle API without starting a tunnel or server."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from react_agent.serving.quiescent_engine_v3 import load_hf_engine
from react_agent.serving.request_http_v3 import IDENTITY_KEYS, QuiescentHTTP


def load_worker(cfg: dict[str, Any], *, api_key: str, state_root: Path) -> QuiescentHTTP:
    """Explicit model load; HF warmup and both device synchronizations precede READY."""
    engine, metadata = load_hf_engine(cfg)
    return QuiescentHTTP(api_key=api_key,
        identity={key: str(metadata[key]) for key in IDENTITY_KEYS},
        role=cfg["role"], model=cfg["model"], root=state_root, engine=engine)
