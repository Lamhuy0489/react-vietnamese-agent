"""Explicit candidate runtime bindings; never alter frozen runtime module globals."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.base import GenerationConfig
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.model_pair_v1 import Role
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.constrained_classifier_v1 import ConstrainedClassifier
from react_agent.security_v1.constrained_host_v1 import ConstrainedRoleBackend, native_root
from react_agent.security_v1.guard import GuardInput, GuardOutcome
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, bind
from react_agent.security_v1.pair_runtime_v3 import PairRoleBackend
from react_agent.security_v1.pair_runtime_v3 import run_pair_task as original_pair
from react_agent.security_v1.processing_scope_v3 import PROFILE, ProcessingScope, describe_action
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v7 import SecurityRuntime as V7Runtime
from react_agent.validation.constrained_worker_audit_v1 import IDENTITY

RUNTIME_VERSION = "security_runtime_v8_constrained_v1"


class HostClassifier(ConstrainedClassifier):
    generation = GenerationConfig(max_new_tokens=128)

    def __init__(self, backend: ConstrainedRoleBackend) -> None:
        super().__init__(backend)
        self.role = backend
        self._host_lock = threading.Lock()

    def classify(self, request: GuardInput) -> GuardOutcome:
        if not self._host_lock.acquire(blocking=False):
            raise RuntimeError("single host classifier owner required")
        try:
            return self._classify(request)
        finally:
            self._host_lock.release()

    def _classify(self, request: GuardInput) -> GuardOutcome:
        before = len(self.role.host_attempts)
        outcome = super().classify(request)
        if outcome.status == "ERROR" and len(self.role.host_attempts) == before:
            # An actual local admission rejection, not a dispatched worker call.
            # Capture after retirement: closing the pair is not a generate event.
            events = len(self.role.pair.snapshot()["events"])
            attempts = len(self.role.attempts)
            messages = [
                dict(role="system", content=PROMPT),
                dict(role="user", content=canonical_json(request.model_dump(mode="json"))),
            ]
            self.role.host_attempts.append(
                dict(
                    sequence=before + 1,
                    role="guard",
                    status="ERROR",
                    error_class="ConstrainedHostAdmissionError",
                    request_sha256=text_hash(canonical_json(messages)),
                    generation_sha256=text_hash(canonical_json(self.generation.model_dump())),
                    worker_attempts_before=attempts,
                    worker_attempts_after=attempts,
                    pair_events_before=events,
                    pair_events_after=events,
                )
            )
        return outcome


class SecurityRuntime(V7Runtime):
    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        if not isinstance(kwargs.get("_worker"), ConstrainedRoleBackend):
            raise ValueError("constrained task-owned role required")
        inner = bind(V5Runtime._run_task, WarmModelGuard=HostClassifier, PROMPT=PROMPT)
        body = bind(
            V7Runtime._run_task,
            _V5_RUN_TASK=inner,
            ProcessingScope=ProcessingScope,
            describe_action=describe_action,
            SCOPE_PROFILE=PROFILE,
            RUNTIME_VERSION=RUNTIME_VERSION,
        )
        result = cast(SecurityRun, body(self, task, **kwargs))
        path = Path(kwargs["output"]) / "run_metadata.json"
        metadata = json.loads(path.read_text())
        metadata["constrained_execution_identity"] = IDENTITY
        metadata["guard_cache_protocol"] = "constrained_classifier_v1"
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
        return result


def _run(
    task: RuntimeTask, *, pair: DiagnosticPair, constrained: Path, **kwargs: Any
) -> SecurityRun:
    no_links(constrained)
    if constrained.exists() or constrained.is_symlink():
        raise ValueError("fresh constraint evidence root required")
    output = Path(kwargs["output"]).resolve()
    if constrained.resolve().is_relative_to(output) or output.is_relative_to(constrained.resolve()):
        raise ValueError("constraint evidence must be separate from runtime output")

    def role_backend(owner: DiagnosticPair, role: Role) -> PairRoleBackend:
        return (
            ConstrainedRoleBackend(owner, constrained)
            if role == "guard"
            else PairRoleBackend(owner, role)
        )

    body = bind(
        original_pair,
        PairRoleBackend=role_backend,
        ProcessingScope=ProcessingScope,
        SecurityRuntime=SecurityRuntime,
    )
    return cast(SecurityRun, body(task, pair=pair, **kwargs))


def run_pair_task(task: RuntimeTask, *, pair: DiagnosticPair, **kwargs: Any) -> SecurityRun:
    root = native_root(pair)  # Topology admission before pair.start/model load.
    return _run(task, pair=pair, constrained=root, **kwargs)


def run_synthetic_pair_task(
    task: RuntimeTask, *, pair: DiagnosticPair, constrained: Path, **kwargs: Any
) -> SecurityRun:
    """Explicit test harness, never an automatic fallback for native admission."""
    if type(pair) is not DiagnosticPair or any(
        not identity.model_id.startswith("synthetic-")
        for identity in (pair.config.agent, pair.config.guard)
    ):
        raise ValueError("explicit synthetic identities required")
    return _run(task, pair=pair, constrained=constrained, **kwargs)
