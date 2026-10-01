"""Checkpointed Dev runner for the structured Qwen agent/Llama guard APIs.

This module deliberately keeps the API experiment separate from the frozen
benchmark runners.  The manifest contains public Dev identifiers and hashes,
never credentials or private ground truth.  A task is marked ``started``
before its first request.  If the host is interrupted after that write, resume
retains the ambiguous task as ``interrupted`` instead of silently issuing a
possibly duplicate request.  Completed and failed tasks are immutable and are
never retried by ordinary resume.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from react_agent.adversarial_release import ReleasedFixture
from react_agent.agent import AgentRuntime
from react_agent.agent.state import RuntimeConfig
from react_agent.config import load_generation_config
from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.structured_http_v1 import StructuredHTTPBackend
from react_agent.schemas.clean_task import CleanPublicTask, FaultSpec
from react_agent.security_v1.guard import GuardInput, ModelGuard
from react_agent.tools.factory import build_clean_registry

PROTOCOL = "structured_api_dev_v1"


class ApiDevManifest(BaseModel):
    """Strict, credential-free input and generation identity for one run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol: Literal["structured_api_dev_v1"] = "structured_api_dev_v1"
    source_commit: str = Field(min_length=1)
    source_files: dict[str, str] = Field(min_length=1)
    clean_split_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    clean_selection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    clean_task_ids: tuple[str, ...] = Field(min_length=1)
    clean_task_categories: dict[str, str]
    clean_input_root: str
    fault_plans_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    adversarial_release_root: str
    adversarial_attack_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    adversarial_benign_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    guard_variant_ids: tuple[str, ...] = Field(min_length=2)
    guard_pairs: tuple[tuple[str, str], ...] = Field(min_length=1)
    agent_identity: dict[str, str]
    guard_identity: dict[str, str]
    agent_generation: dict[str, Any]
    guard_generation: dict[str, Any]
    runtime: dict[str, Any]
    test_tasks_loaded: int = 0
    private_ground_truth_loaded: int = 0

    @model_validator(mode="after")
    def validate_selection(self) -> ApiDevManifest:
        if len(set(self.clean_task_ids)) != len(self.clean_task_ids):
            raise ValueError("duplicate clean task id")
        if len(self.clean_task_ids) != 21:
            raise ValueError("the frozen clean Dev pilot requires 21 tasks")
        if set(self.clean_task_categories) != set(self.clean_task_ids):
            raise ValueError("clean category map must cover selected ids exactly")
        if set(Counter(self.clean_task_categories.values()).values()) != {3}:
            raise ValueError("clean Dev pilot requires three tasks per category")
        if self.test_tasks_loaded != 0 or self.private_ground_truth_loaded != 0:
            raise ValueError("Test and private ground truth are forbidden")
        if len(set(self.guard_variant_ids)) != len(self.guard_variant_ids):
            raise ValueError("duplicate guard variant id")
        expected = {variant for pair in self.guard_pairs for variant in pair}
        if expected != set(self.guard_variant_ids):
            raise ValueError("guard pair map must cover selected variants exactly")
        required_identity = {
            "model_id",
            "model_revision",
            "session_id",
            "source_commit",
            "worker_sha256",
        }
        if (
            set(self.agent_identity) != required_identity
            or set(self.guard_identity) != required_identity
        ):
            raise ValueError("complete agent/guard identity required")
        if not self.agent_identity["model_revision"].startswith(
            "sha256:"
        ) or not self.guard_identity["model_revision"].startswith("sha256:"):
            raise ValueError("content-addressed model revisions required")
        if (
            self.agent_generation.get("temperature") != 0
            or not 1 <= self.agent_generation.get("max_new_tokens", 0) <= 1024
        ):
            raise ValueError("bounded greedy agent generation required")
        if self.guard_generation != {"temperature": 0.0, "max_new_tokens": 128, "seed": 42}:
            raise ValueError("frozen guard generation required")
        return self

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.model_dump(mode="json")))


class TaskState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    kind: Literal["agent", "guard"]
    status: Literal["started", "completed", "failed", "interrupted"]
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    started_at_ns: int = Field(ge=0)
    finished_at_ns: int | None = Field(default=None, ge=0)
    result: dict[str, Any] | None = None
    error_code: str | None = None
    request_may_have_reached_server: bool = False

    @model_validator(mode="after")
    def terminal_consistency(self) -> TaskState:
        if self.status == "started" and self.finished_at_ns is not None:
            raise ValueError("started state cannot have finish time")
        if self.status in {"completed", "failed", "interrupted"} and self.finished_at_ns is None:
            raise ValueError("terminal state requires finish time")
        if self.status == "interrupted" and not self.request_may_have_reached_server:
            raise ValueError("interrupted state must retain delivery uncertainty")
        return self


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _verify_source_files(manifest: ApiDevManifest) -> None:
    root = Path(__file__).resolve().parents[3]
    for relative, expected in manifest.source_files.items():
        path = (root / relative).resolve()
        if not path.is_file() or not path.is_relative_to(root):
            raise ValueError("manifest source file missing or outside repository")
        if _sha_file(path) != expected:
            raise ValueError(f"manifest source hash mismatch: {relative}")


def _atomic_json(path: Path, value: object) -> None:
    """Write a complete receipt and fsync it before replacing the old file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    payload = canonical_json(value).encode("utf-8") + b"\n"
    with temporary.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object receipt required: {path}")
    return value


def _safe_key(value: str) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    if not value or any(ch not in alphabet for ch in value):
        raise ValueError("unsafe task key")
    return value


def _manifest_path(root: Path) -> Path:
    return root / "manifest.json"


def write_manifest(path: Path, manifest: ApiDevManifest) -> None:
    if path.exists():
        raise ValueError("manifest output already exists")
    _atomic_json(path, manifest.model_dump(mode="json"))


def load_manifest(path: Path) -> ApiDevManifest:
    return ApiDevManifest.model_validate(_read_json(path))


def _load_clean(
    manifest: ApiDevManifest,
) -> tuple[list[CleanPublicTask], dict[str, list[FaultSpec]]]:
    root = Path(manifest.clean_input_root)
    split = root / "splits" / "dev.jsonl"
    selection = root / "dev_pilot" / "task_ids.json"
    faults_path = root / "dev_pilot" / "fault_plans.json"
    if (
        _sha_file(split) != manifest.clean_split_sha256
        or _sha_file(selection) != manifest.clean_selection_sha256
    ):
        raise ValueError("clean Dev input hash mismatch")
    selected = json.loads(selection.read_text(encoding="utf-8"))
    ids = selected.get("task_ids") if isinstance(selected, dict) else None
    if ids != list(manifest.clean_task_ids):
        raise ValueError("clean selection differs from manifest")
    rows = {
        task.task_id: task
        for task in (
            CleanPublicTask.model_validate_json(line)
            for line in split.read_text(encoding="utf-8").splitlines()
            if line
        )
    }
    tasks = [rows[task_id] for task_id in manifest.clean_task_ids]
    if [task.category for task in tasks] != [
        manifest.clean_task_categories[task.task_id] for task in tasks
    ]:
        raise ValueError("clean category identity mismatch")
    if _sha_file(faults_path) != manifest.fault_plans_sha256:
        raise ValueError("fault plan hash mismatch")
    raw = json.loads(faults_path.read_text(encoding="utf-8"))
    faults = {
        task_id: [FaultSpec.model_validate(item) for item in plan] for task_id, plan in raw.items()
    }
    return tasks, faults


def _load_guard(manifest: ApiDevManifest) -> dict[str, ReleasedFixture]:
    root = Path(manifest.adversarial_release_root)
    attack_path, benign_path = root / "dev_attack.jsonl", root / "dev_benign.jsonl"
    if (
        _sha_file(attack_path) != manifest.adversarial_attack_sha256
        or _sha_file(benign_path) != manifest.adversarial_benign_sha256
    ):
        raise ValueError("adversarial Dev input hash mismatch")
    rows: dict[str, ReleasedFixture] = {}
    for path in (attack_path, benign_path):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = ReleasedFixture.model_validate_json(line)
            if row.variant_id in manifest.guard_variant_ids:
                if row.variant_id in rows:
                    raise ValueError("duplicate selected guard fixture")
                rows[row.variant_id] = row
    if set(rows) != set(manifest.guard_variant_ids):
        raise ValueError("selected guard fixture missing")
    for attack, benign in manifest.guard_pairs:
        a, b = rows[attack], rows[benign]
        if a.branch != "attack" or b.branch != "benign" or a.pair_id != b.pair_id:
            raise ValueError("guard pair identity mismatch")
    return rows


def _input_hash(value: object) -> str:
    return text_hash(canonical_json(value))


def _start_state(root: Path, key: str, kind: Literal["agent", "guard"], input_hash: str) -> None:
    _atomic_json(
        root / "state.json",
        TaskState(
            key=key,
            kind=kind,
            status="started",
            input_sha256=input_hash,
            started_at_ns=time.time_ns(),
        ).model_dump(mode="json"),
    )


def _finish_state(
    root: Path,
    state: TaskState,
    *,
    status: Literal["completed", "failed", "interrupted"],
    result: dict[str, Any] | None = None,
    error_code: str | None = None,
    uncertain: bool = False,
) -> TaskState:
    value = state.model_copy(
        update={
            "status": status,
            "finished_at_ns": time.time_ns(),
            "result": result,
            "error_code": error_code,
            "request_may_have_reached_server": uncertain,
        }
    )
    _atomic_json(root / "state.json", value.model_dump(mode="json"))
    return value


def _existing_states(root: Path) -> dict[str, TaskState]:
    tasks_root = root / "tasks"
    if not tasks_root.is_dir():
        raise ValueError("tasks directory missing")
    result: dict[str, TaskState] = {}
    for child in tasks_root.iterdir():
        if not child.is_dir() or child.is_symlink():
            raise ValueError("invalid task directory")
        state_path = child / "state.json"
        if not state_path.is_file():
            raise ValueError("task state missing")
        state = TaskState.model_validate(_read_json(state_path))
        if state.key != child.name or state.key in result:
            raise ValueError("task state key mismatch")
        result[state.key] = state
    return result


def _backend_error(exc: BaseException) -> str:
    return exc.code if isinstance(exc, APIError) else type(exc).__name__


def _run_agent_task(
    task: CleanPublicTask,
    faults: list[FaultSpec],
    *,
    backend: StructuredHTTPBackend,
    root: Path,
    clean_root: Path,
    runtime_config: RuntimeConfig,
    generation: Any,
) -> dict[str, Any]:
    trace = root / "trace.jsonl"
    runtime = AgentRuntime(
        backend,
        build_clean_registry(clean_root / "environment", fault_plan=faults),
        runtime_config=runtime_config,
        generation_config=generation,
    )
    result = runtime.run(task, trace_path=trace)
    return {"result": result.model_dump(mode="json")}


def _run_guard_task(
    row: ReleasedFixture, *, backend: StructuredHTTPBackend, root: Path
) -> dict[str, Any]:
    text = row.overlay.attack_text if row.branch == "attack" else row.overlay.benign_text
    request = GuardInput(
        user_instruction=row.task.instruction,
        source_type=row.overlay.source_type,
        candidate_content=text,
    )
    outcome = ModelGuard(backend).classify(request)
    value: dict[str, Any] = {
        "variant_id": row.variant_id,
        "pair_id": row.pair_id,
        "branch": row.branch,
        "input_sha256": _input_hash(request.model_dump(mode="json")),
        "status": outcome.status,
        "cache_hit": outcome.cache_hit,
        "cache_key": outcome.cache_key,
    }
    if outcome.result is not None:
        value["guard"] = outcome.result.model_dump(mode="json")
    if outcome.error_code is not None:
        value["error_code"] = outcome.error_code
    return {"result": value}


def run(
    output: Path,
    manifest_path: Path,
    *,
    agent: StructuredHTTPBackend,
    guard: StructuredHTTPBackend,
    resume: bool = False,
    max_new_tasks: int | None = None,
    probe: bool = True,
) -> dict[str, Any]:
    """Run missing public Dev tasks with immutable per-task checkpoints."""

    if type(resume) is not bool or (
        max_new_tasks is not None and (type(max_new_tasks) is not int or max_new_tasks < 0)
    ):
        raise ValueError("invalid resume/task budget")
    output = output.resolve()
    frozen_data = Path(__file__).resolve().parents[3] / "data"
    if output == frozen_data or output.is_relative_to(frozen_data):
        raise ValueError("run output cannot overlap frozen data")
    manifest = load_manifest(manifest_path)
    _verify_source_files(manifest)
    for backend, expected_identity, role in (
        (agent, manifest.agent_identity, "agent"),
        (guard, manifest.guard_identity, "guard"),
    ):
        if (
            backend.role != role
            or {
                "model_id": backend.model_id,
                "model_revision": backend.model_revision,
                "session_id": backend.session_id,
                "source_commit": backend.source_commit,
                "worker_sha256": backend.worker_sha256,
            }
            != expected_identity
        ):
            raise ValueError(f"{role} backend identity differs from manifest")
    if output.exists():
        if not resume:
            raise ValueError("fresh output required unless resuming")
        saved = _read_json(_manifest_path(output))
        if ApiDevManifest.model_validate(saved).identity != manifest.identity:
            raise ValueError("run manifest identity mismatch")
    else:
        output.mkdir(parents=True, exist_ok=False)
        (output / "tasks").mkdir()
        _atomic_json(_manifest_path(output), manifest.model_dump(mode="json"))
    if probe:
        agent.probe()
        guard.probe()
    tasks, fault_plans = _load_clean(manifest)
    fixtures = _load_guard(manifest)
    runtime_config = RuntimeConfig.model_validate(manifest.runtime)
    generation = (
        load_generation_config(Path(manifest.agent_generation["path"]))
        if "path" in manifest.agent_generation
        else None
    )
    # A manifest may embed generation directly; a path is a CLI convenience.
    if "path" not in manifest.agent_generation:
        from react_agent.llm.base import GenerationConfig

        generation = GenerationConfig.model_validate(manifest.agent_generation)
    expected: list[tuple[str, Literal["agent", "guard"], CleanPublicTask | ReleasedFixture]] = [
        (task.task_id, "agent", task) for task in tasks
    ] + [(variant_id, "guard", fixtures[variant_id]) for variant_id in manifest.guard_variant_ids]
    states = _existing_states(output)
    expected_keys = {key for key, _, _ in expected}
    if set(states) - expected_keys:
        raise ValueError("unknown task state in output")
    for key, kind, value in expected:
        state = states.get(key)
        if state is None:
            continue
        expected_hash = _input_hash(value.model_dump(mode="json"))
        if state.kind != kind or state.input_sha256 != expected_hash:
            raise ValueError("task state identity mismatch")
        if state.status == "completed" and state.result is None:
            raise ValueError("completed task result missing")
        if state.status == "failed" and not state.error_code:
            raise ValueError("failed task error code missing")
    # Any host crash after the durable started marker is retained as an ambiguous terminal.
    for key, state in list(states.items()):
        if state.status == "started":
            states[key] = _finish_state(
                output / "tasks" / key,
                state,
                status="interrupted",
                error_code="HOST_INTERRUPTED",
                uncertain=True,
            )
    remaining = [(key, kind, value) for key, kind, value in expected if key not in states]
    if max_new_tasks is not None:
        remaining = remaining[:max_new_tasks]
    clean_root = Path(manifest.clean_input_root)
    for key, kind, value in remaining:
        key = _safe_key(key)
        task_root = output / "tasks" / key
        task_root.mkdir()
        input_hash = _input_hash(value.model_dump(mode="json"))
        _start_state(task_root, key, kind, input_hash)
        state = TaskState.model_validate(_read_json(task_root / "state.json"))
        attempts_before = agent.attempts if kind == "agent" else guard.attempts
        calls_before = len(agent.calls) if kind == "agent" else len(guard.calls)
        try:
            if kind == "agent":
                if not isinstance(value, CleanPublicTask):
                    raise ValueError("agent task type mismatch")
                payload = _run_agent_task(
                    value,
                    fault_plans.get(value.task_id, []),
                    backend=agent,
                    root=task_root,
                    clean_root=clean_root,
                    runtime_config=runtime_config,
                    generation=generation,
                )
            else:
                if not isinstance(value, ReleasedFixture):
                    raise ValueError("guard fixture type mismatch")
                payload = _run_guard_task(value, backend=guard, root=task_root)
            backend = agent if kind == "agent" else guard
            payload["backend_calls"] = len(backend.calls) - calls_before
            payload["backend_attempts"] = backend.attempts - attempts_before
            states[key] = _finish_state(task_root, state, status="completed", result=payload)
        except BaseException as exc:
            # Do not persist exception text: it may include endpoint details or secrets.
            attempts_after = agent.attempts if kind == "agent" else guard.attempts
            states[key] = _finish_state(
                task_root,
                state,
                status="failed",
                error_code=_backend_error(exc),
                uncertain=attempts_after > attempts_before,
            )
    counts = Counter(state.status for state in states.values())
    summary = {
        "protocol": PROTOCOL,
        "manifest_sha256": manifest.identity,
        "expected": len(expected),
        "completed": counts["completed"],
        "failed": counts["failed"],
        "interrupted": counts["interrupted"],
        "missing": len(expected) - len(states),
        "agent_tasks": len(tasks),
        "guard_controls": len(fixtures),
        "test_tasks_loaded": 0,
        "private_ground_truth_loaded": 0,
        "phase5_accepted": False,
    }
    summary["state_sha256"] = {
        key: _sha_file(output / "tasks" / key / "state.json") for key in sorted(states)
    }
    _atomic_json(output / "summary.json", summary)
    return summary
