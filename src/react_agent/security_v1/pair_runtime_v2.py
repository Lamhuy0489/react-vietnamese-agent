"""Versioned pair/runtime failure evidence over the unchanged v7 security loop.

The parent calls role adapters directly; adapters never spawn a nested pair.
The outer task owns startup, cancellation and a durable cleanup receipt.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any, cast

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.model_pair_v1 import (
    READY_ACK,
    READY_COMMAND,
    ModelPair,
    ReadyFactory,
    Role,
)
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import SecurityConfig
from react_agent.security_v1.final_entitlements_v2 import extract_final_entitlement
from react_agent.security_v1.processing_scope_v2 import ProcessingScope
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v7 import SecurityRuntime
from react_agent.security_v1.warm_guard import WarmGuardBackend, WarmGuardConfig
from react_agent.tools.registry import ToolRegistry

PROFILE = "model_pair_security_runtime_v2"


class PairRoleBackend:
    """Host role view; transport/lifecycle stays with the original pair."""

    def __init__(self, pair: ModelPair, role: Role) -> None:
        if role not in {"agent", "guard"}:
            raise ValueError("unknown model role")
        self.pair, self.role = pair, role
        identity = pair.config.agent if role == "agent" else pair.config.guard
        self.model_id, self.model_revision = identity.model_id, identity.model_revision
        self.config = pair.config.execution(role, cold=False)
        self.host_attempts: list[dict[str, Any]] = []

    @property
    def attempts(self) -> list[dict[str, Any]]:
        # Startup readiness is recorded in the outer receipt, not as an LLM call.
        return cast(
            list[dict[str, Any]], self.pair.snapshot()["workers"][self.role]["attempts"][1:]
        )

    @property
    def lifecycle_events(self) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], self.pair.snapshot()["workers"][self.role]["lifecycle"])

    @property
    def closed(self) -> bool:
        return bool(self.pair.snapshot()["workers"][self.role]["closed"])

    @property
    def retired(self) -> bool:
        return self.pair.state != "READY" or self.closed

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        before = len(self.attempts)
        events_before = len(self.pair.snapshot()["events"])
        status = "ERROR"
        error_class: str | None = None
        try:
            response = self.pair.generate(self.role, messages, config)
            status = "OK"
            return response
        except BaseException as exc:
            error_class = type(exc).__name__
            raise
        finally:
            self.host_attempts.append(
                {
                    "sequence": len(self.host_attempts) + 1,
                    "role": self.role,
                    "status": status,
                    "error_class": error_class,
                    "request_sha256": text_hash(canonical_json(messages)),
                    "generation_sha256": text_hash(canonical_json(config.model_dump())),
                    "worker_attempts_before": before,
                    "worker_attempts_after": len(self.attempts),
                    "pair_events_before": events_before,
                    "pair_events_after": len(self.pair.snapshot()["events"]),
                }
            )

    def close(self) -> None:
        self.pair.close()

    def retire(self) -> None:
        self.close()


def run_pair_task(
    task: RuntimeTask,
    *,
    output: Path,
    registry_factory: Callable[[], ToolRegistry],
    security: SecurityConfig,
    runtime_config: RuntimeConfig,
    generation: GenerationConfig,
    source_catalog: SourceCatalog,
    pair: ModelPair | None = None,
    agent_factory: Callable[[], LLMBackend] | None = None,
    agent_execution: WarmGuardConfig | None = None,
) -> SecurityRun:
    """Run once into a fresh root, retaining lifecycle evidence on every exit.

    A0/A1 require agent-only inputs. A2–A6 require a NEW pair owned by the host.
    Output and caller inputs are validated before any worker starts.
    """
    if runtime_config.config_id != "A0":
        raise ValueError("baseline runtime mechanics must be A0")
    if security.llm_guard:
        if pair is None or agent_factory is not None or agent_execution is not None:
            raise ValueError("A2–A6 require only a task-owned pair")
        initial = pair.snapshot()  # Also validates parent process ownership.
        if initial["state"] != "NEW":
            raise ValueError("fresh NEW pair required")
    elif pair is not None or agent_factory is None or agent_execution is None:
        raise ValueError("A0/A1 require only an agent worker, no guard/pair")
    if security.level == "A6":
        extract_final_entitlement(task.instruction)
    if security.session_trust:
        ProcessingScope(task.instruction)
    root = output.resolve()
    frozen = Path(__file__).resolve().parents[3] / "data"
    if root.exists() or root.is_relative_to(frozen) or frozen.is_relative_to(root):
        raise ValueError("fresh output outside data required")
    root.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    worker: WarmGuardBackend | None = None
    agent_role: PairRoleBackend | None = None
    guard: PairRoleBackend | None = None
    result: SecurityRun | None = None
    error_class: str | None = None
    cleanup_error: str | None = None
    startup_seconds = 0.0
    startup_completed = False
    run_seconds = 0.0
    try:
        startup_started = perf_counter()
        try:
            if pair is not None:
                pair.start()
                backend: LLMBackend = PairRoleBackend(pair, "agent")
                agent_role = cast(PairRoleBackend, backend)
                guard = PairRoleBackend(pair, "guard")
            else:
                if agent_factory is None or agent_execution is None:
                    raise ValueError("agent-only inputs missing")
                worker = WarmGuardBackend(ReadyFactory(agent_factory), agent_execution)
                ready = worker.generate(
                    [{"role": "user", "content": READY_COMMAND}], GenerationConfig()
                )
                if ready.text != READY_ACK:
                    raise ValueError("agent readiness failed")
                backend, guard = worker, None
            startup_completed = True
        finally:
            startup_seconds = perf_counter() - startup_started
        runtime = SecurityRuntime(
            backend, registry_factory(), runtime_config=runtime_config, generation_config=generation
        )
        run_started = perf_counter()
        try:
            result = runtime._run_task(
                task,
                output=root / "runtime",
                source_catalog=source_catalog,
                security_config=security,
                guard_factory=(lambda: guard) if guard is not None else None,
                guard_execution=guard.config if guard is not None else None,
                _worker=guard,
            )
        finally:
            run_seconds = perf_counter() - run_started
        metadata_path = root / "runtime/run_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["pair_runtime_profile"] = PROFILE
        if guard is not None:
            # Pair readiness is a transport request but not a classification.
            # Preserve actual worker sequence/cold flags and name a new schema.
            metadata["guard_trace_schema"] = "guard_trace_pair_v1"
            trace_path = root / "runtime/trace_guard.jsonl"
            rows = [json.loads(line) for line in trace_path.read_text().splitlines()]
            for row in rows:
                row["schema_version"] = "guard_trace_pair_v1"
            trace_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return result
    except BaseException as exc:
        error_class = type(exc).__name__
        raise
    finally:
        cleanup_started = perf_counter()
        try:
            if pair is not None:
                pair.close()
            elif worker is not None:
                worker.close()
        except BaseException as exc:
            cleanup_error = type(exc).__name__
            raise
        finally:
            snapshot = (
                pair.snapshot()
                if pair is not None
                else {
                    "workers": {
                        "agent": {
                            "attempts": worker.attempts if worker else [],
                            "lifecycle": worker.lifecycle_events if worker else [],
                            "closed": worker.closed if worker else True,
                            "handle_pending": worker._process is not None if worker else False,
                        }
                    }
                }
            )
            receipt = {
                "profile": PROFILE,
                "owner_pid": os.getpid(),
                "task_id": task.task_id,
                "task_sha256": text_hash(task.instruction),
                "security": security.model_dump(mode="json"),
                "runtime_config": runtime_config.model_dump(mode="json"),
                "generation": generation.model_dump(mode="json"),
                "source_catalog_sha256": text_hash(source_catalog.model_dump_json()),
                "pair_config": asdict(pair.config) if pair else None,
                "agent_execution": asdict(agent_execution) if agent_execution else None,
                "snapshot": snapshot,
                "host_role_attempts": {
                    "agent": agent_role.host_attempts if agent_role else [],
                    "guard": guard.host_attempts if guard else [],
                }
                if pair is not None
                else None,
                "startup_seconds": startup_seconds,
                "startup_completed": startup_completed,
                "runtime_seconds_including_inner_cleanup": run_seconds,
                "outer_cleanup_seconds": perf_counter() - cleanup_started,
                "total_seconds": perf_counter() - started,
                "error_class": error_class,
                "cleanup_error_class": cleanup_error,
                "terminal": result.result.status if result else None,
                "phase5_accepted": False,
            }
            with (root / "pair_runtime.json").open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
