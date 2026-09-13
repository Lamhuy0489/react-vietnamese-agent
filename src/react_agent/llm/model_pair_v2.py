"""Opt-in observed-shutdown pair; inherit frozen ownership and transport semantics."""

from __future__ import annotations

import math
import os
import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import LLMBackend
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig, ReadyFactory, Role
from react_agent.security_v1.worker_shutdown_v2 import ShutdownBackend, ShutdownConfig


@dataclass(frozen=True)
class AgentWorkerConfig:
    model_id: str
    model_revision: str
    start_seconds: float = 1200.0
    call_seconds: float = 180.0
    terminate_grace_seconds: float = 0.5
    kill_grace_seconds: float = 1.0
    graceful_shutdown_seconds: float = 2.0

    def __post_init__(self) -> None:
        ModelIdentity(self.model_id, self.model_revision)
        for value in (
            self.start_seconds,
            self.call_seconds,
            self.terminate_grace_seconds,
            self.kill_grace_seconds,
            self.graceful_shutdown_seconds,
        ):
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("finite positive nonboolean deadline required")
        self.execution(cold=True)
        self.execution(cold=False)

    def execution(self, *, cold: bool) -> ShutdownConfig:
        return ShutdownConfig(
            self.model_id,
            self.model_revision,
            self.start_seconds if cold else self.call_seconds,
            self.terminate_grace_seconds,
            self.kill_grace_seconds,
            graceful_shutdown_seconds=self.graceful_shutdown_seconds,
        )


@dataclass(frozen=True)
class ShutdownPairConfig(PairConfig):
    graceful_shutdown_seconds: float = 2.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.execution("agent", cold=True)

    @property
    def sha256(self) -> str:
        return text_hash(canonical_json({"protocol": "model_pair_shutdown_v2", **asdict(self)}))

    def execution(self, role: Role, *, cold: bool) -> ShutdownConfig:
        if role not in {"agent", "guard"}:
            raise ValueError("known model role required")
        old = super().execution(role, cold=cold)
        return ShutdownConfig(
            old.model_id,
            old.model_revision,
            old.timeout_seconds,
            old.terminate_grace_seconds,
            old.kill_grace_seconds,
            graceful_shutdown_seconds=self.graceful_shutdown_seconds,
        )


class ShutdownPair(ModelPair):
    config: ShutdownPairConfig

    def __init__(
        self,
        agent_factory: Callable[[], LLMBackend],
        guard_factory: Callable[[], LLMBackend],
        config: ShutdownPairConfig,
    ) -> None:
        if not isinstance(config, ShutdownPairConfig):
            raise TypeError("versioned pair shutdown config required")
        # Do not construct legacy workers and silently replace their buffers.
        self.config = config
        self._config_sha256 = config.sha256
        self._owner = os.getpid()
        self._lock = threading.Lock()
        self.state = "NEW"
        self.events: list[dict[str, Any]] = []
        self._workers = {
            "agent": ShutdownBackend(
                ReadyFactory(agent_factory), config.execution("agent", cold=True)
            ),
            "guard": ShutdownBackend(
                ReadyFactory(guard_factory), config.execution("guard", cold=True)
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        result = super().snapshot()
        result["protocol"] = "model_pair_shutdown_v2"
        return result
