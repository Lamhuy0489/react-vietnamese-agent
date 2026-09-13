"""Real-spawn, synthetic stop/teardown evidence; no model, network or Test data."""

from __future__ import annotations

import ast
import inspect
import json
import multiprocessing as mp
import os
import signal
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.security_v1.warm_guard import WarmGuardBackend, WarmGuardConfig
from react_agent.security_v1.worker_shutdown_v2 import ShutdownBackend, ShutdownConfig


class SyntheticBackend:
    model_id = "synthetic-shutdown"
    model_revision = "v2"

    def __init__(self, mode: str) -> None:
        self.mode = mode
        if mode == "ignore_term":
            signal.signal(signal.SIGTERM, signal.SIG_IGN)

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if self.mode == "generation_error":
            raise ValueError("synthetic private exception must not escape")
        if self.mode == "busy":
            time.sleep(5)
        return ModelResponse(
            text="public", model_id=self.model_id, model_revision=self.model_revision
        )

    def __del__(self) -> None:
        if self.mode == "slow":
            time.sleep(0.4)
        elif self.mode in {"hang", "ignore_term"}:
            time.sleep(5)
        elif self.mode in {"exit_error", "exit_zero"}:
            os._exit(9 if self.mode == "exit_error" else 0)


@dataclass(frozen=True)
class Factory:
    mode: str = "fast"

    def __call__(self) -> SyntheticBackend:
        return SyntheticBackend(self.mode)


def worker(mode: str = "fast", grace: float = 2.0) -> ShutdownBackend:
    return ShutdownBackend(
        Factory(mode),
        ShutdownConfig(
            "synthetic-shutdown",
            "v2",
            timeout_seconds=10,
            graceful_shutdown_seconds=grace,
            terminate_grace_seconds=0.2,
            kill_grace_seconds=1,
        ),
    )


def save(root: Path, backend: WarmGuardBackend) -> dict:
    assert backend.closed
    assert backend._process is None
    value = {
        "schema_version": "synthetic_worker_shutdown_case_v2",
        "native_model": False,
        "attempts": backend.attempts,
        "lifecycle": backend.lifecycle_events,
    }
    assert all(e["reaped"] for e in backend.lifecycle_events)
    pids = {e["pid"] for e in backend.lifecycle_events}
    assert not pids.intersection(p.pid for p in mp.active_children())
    (root / "shutdown_case.json").write_text(json.dumps(value, indent=2) + "\n")
    return backend.lifecycle_events[-1]


@pytest.mark.parametrize("mode", ["fast", "slow"])
def test_acknowledged_natural_exit_keeps_observable_responses(tmp_path: Path, mode: str) -> None:
    backend = worker(mode)
    with backend:
        assert backend.generate([], GenerationConfig()).text == "public"
        assert backend.generate([], GenerationConfig()).text == "public"
        assert backend.attempts[0]["pid"] == backend.attempts[1]["pid"]
    row = save(tmp_path, backend)
    assert row["method"] == "GRACEFUL" and row["exitcode"] == 0
    assert row["stop_received"] and row["serve_returned"]
    assert 0 <= row["stop_received_seconds"] <= row["serve_returned_after_stop_seconds"]
    assert row["serve_returned_after_stop_seconds"] <= row["elapsed_seconds"]
    if mode == "slow":
        assert row["serve_returned_after_stop_seconds"] >= 0.4
    before = json.dumps(backend.lifecycle_events)
    backend.close()
    assert json.dumps(backend.lifecycle_events) == before
    with pytest.raises(RuntimeError, match="retired"):
        backend.generate([], GenerationConfig())


def test_old_small_budget_control_is_preserved(tmp_path: Path) -> None:
    backend = WarmGuardBackend(
        Factory("slow"),
        WarmGuardConfig(
            "synthetic-shutdown",
            "v2",
            timeout_seconds=10,
            terminate_grace_seconds=0.05,
        ),
    )
    with backend:
        assert backend.generate([], GenerationConfig()).text == "public"
    row = save(tmp_path, backend)
    assert row["method"] in {"TERMINATE", "KILL"}


@pytest.mark.parametrize("mode,method", [("hang", "TERMINATE"), ("ignore_term", "KILL")])
def test_ack_is_not_process_exit_and_fallback_stays_bounded(
    tmp_path: Path,
    mode: str,
    method: str,
) -> None:
    backend = worker(mode, grace=0.5)
    with backend:
        backend.generate([], GenerationConfig())
    row = save(tmp_path, backend)
    assert row["method"] == method
    assert row["stop_received"] and not row["serve_returned"]
    assert row["serve_returned_after_stop_seconds"] is None
    assert row["elapsed_seconds"] < 3


@pytest.mark.parametrize("mode,code", [("exit_error", 9), ("exit_zero", 0)])
def test_error_exit_after_ack_is_not_graceful(tmp_path: Path, mode: str, code: int) -> None:
    backend = worker(mode)
    with backend:
        backend.generate([], GenerationConfig())
    row = save(tmp_path, backend)
    assert row["method"] == "EXITED" and row["exitcode"] == code
    assert row["stop_received"] and not row["serve_returned"]


def test_generation_failure_does_not_request_normal_shutdown(tmp_path: Path) -> None:
    backend = worker("generation_error")
    with backend, pytest.raises(RuntimeError, match="backend failed"):
        backend.generate([], GenerationConfig())
    row = save(tmp_path, backend)
    assert not row["graceful_requested"] and not row["stop_received"]
    assert backend.attempts[0]["status"] == "BACKEND_FAILURE"
    assert "synthetic private exception" not in json.dumps(backend.attempts)


def test_timeout_cancels_without_graceful_wait(tmp_path: Path) -> None:
    backend = ShutdownBackend(
        Factory("busy"),
        ShutdownConfig(
            "synthetic-shutdown",
            "v2",
            timeout_seconds=0.5,
            graceful_shutdown_seconds=10,
            terminate_grace_seconds=0.2,
        ),
    )
    with backend, pytest.raises(TimeoutError):
        backend.generate([], GenerationConfig())
    row = save(tmp_path, backend)
    assert not row["graceful_requested"] and not row["stop_received"]
    assert row["elapsed_seconds"] < 3
    assert backend.attempts[0]["status"] == "TIMEOUT"


def test_never_started_close_has_no_fake_ack() -> None:
    backend = worker()
    backend.close()
    assert backend.lifecycle_events == []


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf"), True])
def test_grace_budget_validation(value: float) -> None:
    with pytest.raises(ValueError, match="graceful"):
        ShutdownConfig("synthetic", "v2", graceful_shutdown_seconds=value)


def test_budget_changes_execution_identity() -> None:
    one = ShutdownConfig("synthetic", "v2", graceful_shutdown_seconds=1)
    two = ShutdownConfig("synthetic", "v2", graceful_shutdown_seconds=2)
    assert one.identity != two.identity
    assert one.lifecycle == "task_local_observed_shutdown_v2"


def test_close_still_requires_idle_owner() -> None:
    backend = worker()
    backend._lock.acquire()
    try:
        with pytest.raises(RuntimeError, match="in-flight"):
            backend.close()
    finally:
        backend._lock.release()
    owner = backend._owner_pid
    backend._owner_pid = -1
    try:
        with pytest.raises(RuntimeError, match="owning"):
            backend.close()
    finally:
        backend._owner_pid = owner
        backend.close()


def test_transport_method_is_frozen_except_observer_entry() -> None:
    original = ast.parse(textwrap.dedent(inspect.getsource(WarmGuardBackend.generate)))
    candidate = ast.parse(textwrap.dedent(inspect.getsource(ShutdownBackend.generate)))
    for node in ast.walk(candidate):
        if isinstance(node, ast.Name) and node.id == "_observed_serve":
            node.id = "_serve"
        if isinstance(node, ast.keyword) and node.arg == "args":
            assert isinstance(node.value, ast.Tuple)
            assert [x.attr for x in node.value.elts[-2:] if isinstance(x, ast.Attribute)] == [
                "_stop_received",
                "_serve_returned",
            ]
            node.value.elts = node.value.elts[:-2]
    assert ast.dump(candidate) == ast.dump(original)
