"""Task-local host role admission over the unchanged observed sibling transport."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.constrained_policy_v1 import ConstrainedPolicyFactory
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticFactory
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.model_pair_v1 import ReadyFactory
from react_agent.security_v1.pair_runtime_v3 import PairRoleBackend
from react_agent.validation.constrained_worker_audit_v1 import IDENTITY, complete
from react_agent.validation.context_stress_audit_v1 import equal, inventory


def native_root(pair: DiagnosticPair) -> Path:
    """Fail before startup if the guard factory is not the constrained native path."""
    if type(pair) is not DiagnosticPair:
        raise TypeError("exact diagnostic pair required")
    ready: Any = pair._workers["guard"].factory
    if type(ready) is not ReadyFactory:
        raise ValueError("exact readiness/observer topology required")
    observer: Any = ready.factory
    if type(observer) is not DiagnosticFactory:
        raise ValueError("exact readiness/observer topology required")
    factory: Any = observer.backend_factory
    if type(factory) is not ConstrainedPolicyFactory:
        raise ValueError("native constrained guard factory required")
    if (factory.snapshot.model_id, factory.snapshot.model_revision) != (
        pair.config.guard.model_id,
        pair.config.guard.model_revision,
    ):
        raise ValueError("guard snapshot identity mismatch")
    return factory.output


class ConstrainedRoleBackend(PairRoleBackend):
    """Receipt-bound host view, not remote live-configuration introspection."""

    def __init__(self, pair: DiagnosticPair, root: Path) -> None:
        super().__init__(pair, "guard")
        self.root = root
        self.constraint_identity = IDENTITY
        self._owner = os.getpid()
        self._pair_identity = pair.config.sha256
        self._factories = tuple(pair._workers[r].factory for r in ("agent", "guard"))
        self._hashes: dict[str, str] = {}
        self._validated = 0
        self._pid: int | None = None

    def verify_identity(self) -> None:
        if os.getpid() != self._owner or self.retired:
            raise RuntimeError("owning live pair required")
        if self.pair._workers["guard"].retired:
            raise RuntimeError("resident guard unavailable")
        if self.pair.config.sha256 != self._pair_identity or self.constraint_identity != IDENTITY:
            raise ValueError("host execution identity changed")
        if self.config != self.pair.config.execution("guard", cold=False):
            raise ValueError("host deadline/config identity changed")
        if (self.model_id, self.model_revision) != (
            self.pair.config.guard.model_id,
            self.pair.config.guard.model_revision,
        ) or any(
            self.pair._workers[r].factory is not f
            for r, f in zip(("agent", "guard"), self._factories, strict=True)
        ):
            raise ValueError("host model/factory changed")
        if len(self.attempts) != self._validated:
            raise ValueError("unwitnessed guard request history")
        actual = inventory(self.root) if self.root.exists() else {}
        equal(actual, self._hashes, "validated receipt history")
        if self._validated:
            equal(
                sorted(p.name for p in self.root.iterdir()),
                [f"request_{i:06d}" for i in range(1, self._validated + 1)],
                "exact constrained request roots",
            )

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        self.verify_identity()
        if config != GenerationConfig(max_new_tokens=128):
            raise ValueError("frozen host guard generation required")
        response = super().generate(messages, config)
        attempt = self.attempts[-1]
        index = self._validated + 1
        if len(self.attempts) != index or attempt["status"] != "OK":
            raise ValueError("one successful transport attempt required")
        if self._pid is not None and attempt["pid"] != self._pid:
            raise ValueError("worker replacement forbidden")
        binding: dict[str, Any] = dict(
            pid=attempt["pid"],
            model_id=self.model_id,
            model_revision=self.model_revision,
            request_index=index,
            request_sha256=text_hash(canonical_json(messages)),
            generation_sha256=text_hash(canonical_json(config.model_dump())),
        )
        for key in ("request_sha256", "generation_sha256"):
            equal(attempt[key], binding[key], "host transport " + key)
        verified = complete(self.root / f"request_{index:06d}", binding, text_hash(response.text))
        self._hashes.update(
            {f"request_{index:06d}/" + p: sha for p, sha in verified["raw_sha256"].items()}
        )
        self._validated, self._pid = index, attempt["pid"]
        self.verify_identity()
        return response
