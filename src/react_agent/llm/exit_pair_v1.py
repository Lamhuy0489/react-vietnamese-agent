"""Explicit diagnostic pair over inherited sibling-worker and witness semantics."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from react_agent.llm.base import LLMBackend
from react_agent.llm.guard_diagnostic_backend_v2 import RecordSink
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.model_pair_v1 import Role
from react_agent.llm.model_pair_v2 import ShutdownPair, ShutdownPairConfig
from react_agent.security_v1.exit_milestones_v1 import MilestoneBackend, MilestoneConfig
from react_agent.security_v1.guard_bare_json_v1 import bind


@dataclass(frozen=True)
class ExitPairConfig(ShutdownPairConfig):
    exit_observer: str = "exit_milestones_v1"

    def __post_init__(self) -> None:
        if self.exit_observer != "exit_milestones_v1":
            raise ValueError("explicit exit observer identity required")
        super().__post_init__()

    def execution(self, role: Role, *, cold: bool) -> MilestoneConfig:
        old = super().execution(role, cold=cold)
        return MilestoneConfig(
            old.model_id,
            old.model_revision,
            old.timeout_seconds,
            old.terminate_grace_seconds,
            old.kill_grace_seconds,
            graceful_shutdown_seconds=old.graceful_shutdown_seconds,
        )


def observer_config(config: ShutdownPairConfig) -> ExitPairConfig:
    if type(config) is ExitPairConfig:
        return config
    if type(config) is not ShutdownPairConfig:
        raise TypeError("exact shutdown or exit pair config required")
    return ExitPairConfig(**vars(config))


class ExitPair(DiagnosticPair):
    config: ExitPairConfig

    def __init__(
        self,
        agent_factory: Callable[[], LLMBackend],
        guard_factory: Callable[[], LLMBackend],
        config: ShutdownPairConfig,
        witness: Path,
    ) -> None:
        # Same witness ownership as DiagnosticPair; never replace live workers.
        self.witness = RecordSink(witness)
        self._observer_lock = threading.Lock()
        bind(ShutdownPair.__init__, ShutdownBackend=MilestoneBackend)(
            self, agent_factory, guard_factory, observer_config(config)
        )

    def exit_snapshot(self) -> dict[str, Any]:
        self._enter()
        try:
            if self.state not in {"CLOSED", "FAILED"}:
                raise RuntimeError("exit snapshot requires terminal pair")
            return {
                role: {
                    "status": "unreaped" if worker._process is not None else "reaped",
                    "milestones": None
                    if worker._process is not None
                    else cast(MilestoneBackend, worker).exit_milestones(),
                }
                for role, worker in self._workers.items()
            }
        finally:
            self._lock.release()
