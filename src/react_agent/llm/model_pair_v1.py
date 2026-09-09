"""Task-owned sibling model workers using the immutable bounded warm transport."""

from __future__ import annotations

import json
import math
import os
import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_hf_v1 import AgentHFBackend
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.security_v1.warm_guard import WarmGuardBackend, WarmGuardConfig

Role = Literal["agent", "guard"]
READY_COMMAND = "__HOST_MODEL_PAIR_READY_V1__"
READY_ACK = "MODEL_PAIR_RESIDENT_ACK_V1"


@dataclass(frozen=True)
class ModelIdentity:
    model_id: str
    model_revision: str

    def __post_init__(self) -> None:
        if any(
            not isinstance(v, str) or not v.strip() for v in (self.model_id, self.model_revision)
        ):
            raise ValueError("explicit model identity required")


@dataclass(frozen=True)
class PairConfig:
    agent: ModelIdentity
    guard: ModelIdentity
    agent_start_seconds: float = 1200.0
    guard_start_seconds: float = 120.0
    agent_call_seconds: float = 180.0
    guard_call_seconds: float = 120.0
    terminate_grace_seconds: float = 0.5
    kill_grace_seconds: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.agent, ModelIdentity) or not isinstance(self.guard, ModelIdentity):
            raise ValueError("typed identities required")
        for value in (
            self.agent_start_seconds,
            self.guard_start_seconds,
            self.agent_call_seconds,
            self.guard_call_seconds,
            self.terminate_grace_seconds,
            self.kill_grace_seconds,
        ):
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("finite positive nonboolean deadline required")

    @property
    def sha256(self) -> str:
        return text_hash(canonical_json({"protocol": "model_pair_v1", **asdict(self)}))

    def execution(self, role: Role, *, cold: bool) -> WarmGuardConfig:
        identity = self.agent if role == "agent" else self.guard
        timeout = (
            (self.agent_start_seconds if cold else self.agent_call_seconds)
            if role == "agent"
            else (self.guard_start_seconds if cold else self.guard_call_seconds)
        )
        return WarmGuardConfig(
            identity.model_id,
            identity.model_revision,
            timeout,
            self.terminate_grace_seconds,
            self.kill_grace_seconds,
        )


class ReadyBackend:
    """Host command adapter; ACK bypasses model inference, never model authentication."""

    def __init__(self, backend: LLMBackend) -> None:
        self.backend = backend
        self.model_id = backend.model_id
        self.model_revision = backend.model_revision

    def check_identity(self) -> None:
        if (self.backend.model_id, self.backend.model_revision) != (
            self.model_id,
            self.model_revision,
        ):
            raise RuntimeError("resident backend identity drift")

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        self.check_identity()
        if messages == [{"role": "user", "content": READY_COMMAND}]:
            if config != GenerationConfig():
                raise ValueError("invalid readiness decoding")
            return ModelResponse(
                text=READY_ACK, model_id=self.model_id, model_revision=self.model_revision
            )
        response = self.backend.generate(messages, config)
        self.check_identity()
        return response


@dataclass(frozen=True)
class ReadyFactory:
    factory: Callable[[], LLMBackend]

    def __call__(self) -> LLMBackend:
        return ReadyBackend(self.factory())


@dataclass(frozen=True)
class AgentHFFactory:
    model_path: Path
    inventory_path: Path
    metrics_path: Path

    def __call__(self) -> LLMBackend:
        return AgentHFBackend(self.model_path, self.inventory_path, self.metrics_path)


class ModelPair:
    def __init__(
        self,
        agent_factory: Callable[[], LLMBackend],
        guard_factory: Callable[[], LLMBackend],
        config: PairConfig,
    ) -> None:
        self.config = config
        self._config_sha256 = config.sha256
        self._owner = os.getpid()
        self._lock = threading.Lock()
        self.state = "NEW"
        self.events: list[dict[str, Any]] = []
        self._workers = {
            "agent": WarmGuardBackend(
                ReadyFactory(agent_factory), config.execution("agent", cold=True)
            ),
            "guard": WarmGuardBackend(
                ReadyFactory(guard_factory), config.execution("guard", cold=True)
            ),
        }

    def _enter(self) -> None:
        if os.getpid() != self._owner:
            raise RuntimeError("model pair belongs to another process")
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("model pair operation already in flight")

    def _event(self, stage: str, **values: Any) -> None:
        self.events.append({"sequence": len(self.events) + 1, "stage": stage, **values})

    def _identity(self) -> None:
        if self.config.sha256 != self._config_sha256:
            raise RuntimeError("pair configuration changed")

    def _alive(self) -> None:
        if any(worker.retired for worker in self._workers.values()):
            raise RuntimeError("model pair lost a worker")

    def _cleanup(self) -> None:
        failed = False
        for role in ("guard", "agent"):
            worker = self._workers[role]
            try:
                worker.close()
                if worker._process is not None:
                    raise RuntimeError("worker handle still pending")
                self._event("cleanup", role=role, reaped=True)
            except BaseException as exc:  # Attempt sibling cleanup even on interruption.
                failed = True
                self._event("cleanup", role=role, reaped=False, error_class=type(exc).__name__)
        if failed:
            raise RuntimeError("pair cleanup incomplete; owner must retry cleanup")

    def start(self) -> None:
        self._enter()
        try:
            if self.state != "NEW":
                raise RuntimeError("model pair can start exactly once")
            self.state = "STARTING"
            try:
                self._identity()
                for role in ("agent", "guard"):
                    worker = self._workers[role]
                    if role == "guard" and self._workers["agent"].retired:
                        raise RuntimeError("agent died before guard startup")
                    response = worker.generate(
                        [{"role": "user", "content": READY_COMMAND}], GenerationConfig()
                    )
                    if response.text != READY_ACK or worker.retired:
                        raise RuntimeError("readiness acknowledgement failed")
                    self._event(
                        "ready",
                        role=role,
                        pid=worker.attempts[-1]["pid"],
                        cold_execution_sha256=worker.config.identity,
                    )
                    worker.config = self.config.execution(role, cold=False)
                    self._event("warm_deadline", role=role, execution_sha256=worker.config.identity)
                self._alive()
                self.state = "READY"
            except BaseException:
                self.state = "FAILED"
                self._cleanup()
                raise
        finally:
            self._lock.release()

    def generate(
        self, role: Role, messages: list[dict[str, str]], config: GenerationConfig
    ) -> ModelResponse:
        self._enter()
        try:
            if self.state != "READY":
                raise RuntimeError("model pair not ready")
            try:
                self._identity()
                self._alive()
                if role not in ("agent", "guard"):
                    raise ValueError("unknown model role")
                if any(READY_COMMAND in m.get("content", "") for m in messages):
                    raise ValueError("reserved host command cannot be a model prompt")
                worker = self._workers[role]
                if worker.config != self.config.execution(role, cold=False):
                    raise ValueError("worker execution configuration changed")
                response = worker.generate(messages, config)
                self._alive()
                self._event("generate", role=role, status="OK")
                return response
            except BaseException as exc:
                self.state = "FAILED"
                self._event(
                    "generate",
                    role=role if role in ("agent", "guard") else "INVALID",
                    status="ERROR",
                    error_class=type(exc).__name__,
                )
                self._cleanup()
                raise
        finally:
            self._lock.release()

    def close(self) -> None:
        self._enter()
        try:
            if self.state != "FAILED":
                self.state = "CLOSED"
            try:
                self._cleanup()
            except BaseException:
                self.state = "FAILED"
                raise
        finally:
            self._lock.release()

    def snapshot(self) -> dict[str, Any]:
        self._enter()
        try:
            # JSON roundtrip ensures a detached observation, not shared mutable lists.
            result: dict[str, Any] = json.loads(
                canonical_json(
                    {
                        "protocol": "model_pair_v1",
                        "state": self.state,
                        "config_sha256": self._config_sha256,
                        "owner_pid": self._owner,
                        "events": self.events,
                        "workers": {
                            role: {
                                "attempts": w.attempts,
                                "lifecycle": w.lifecycle_events,
                                "closed": w.closed,
                                "handle_pending": w._process is not None,
                            }
                            for role, w in self._workers.items()
                        },
                        "phase5_accepted": False,
                    }
                )
            )
            return result
        finally:
            self._lock.release()

    def __enter__(self) -> ModelPair:
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
