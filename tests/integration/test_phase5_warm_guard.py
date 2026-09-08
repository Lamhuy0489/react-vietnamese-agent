from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.llm.base import GenerationConfig
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.a2_qa import MODEL, REVISION
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.guard import GuardInput
from react_agent.security_v1.runtime_v5 import SecurityRuntime
from react_agent.security_v1.warm_guard import (
    MAX_REQUEST_BYTES,
    WarmGuardBackend,
    WarmGuardConfig,
    WarmModelGuard,
)
from react_agent.security_v1.warm_guard_qa import LifecycleFactory, parity_case
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic lifecycle QA cannot use network")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def worker(mode="safe", timeout=10):
    return WarmGuardBackend(
        LifecycleFactory(mode),
        WarmGuardConfig(MODEL, REVISION, timeout, terminate_grace_seconds=0.2),
    )


def request(content="public"):
    return GuardInput(user_instruction="Chỉ đọc", source_type="document", candidate_content=content)


def test_one_load_three_distinct_requests():
    with worker("counter") as backend:
        outputs = [
            json.loads(
                backend.generate([{"role": "user", "content": str(i)}], GenerationConfig()).text
            )
            for i in range(3)
        ]
        assert [r["calls"] for r in outputs] == [1, 2, 3]
        assert len({r["pid"] for r in outputs}) == 1
        assert [a["cold_start"] for a in backend.attempts] == [True, False, False]
        assert [a["load_seconds"] for a in backend.attempts[1:]] == [0, 0]
    assert backend.closed and backend.lifecycle_events[-1]["reaped"]
    assert backend.lifecycle_events[-1]["method"] == "GRACEFUL"


def test_cache_and_closed_guard_cannot_return_safe():
    backend = worker()
    guard = WarmModelGuard(backend)
    with backend:
        assert guard.classify(request()).status == "OK"
        assert guard.classify(request()).cache_hit
        assert len(backend.attempts) == 1
    assert guard.classify(request()).status == "ERROR"
    assert guard._cache == {}


@pytest.mark.parametrize(
    "mode,status",
    [
        ("load_error", "BACKEND_FAILURE"),
        ("initial_identity", "IDENTITY_CHANGED"),
        ("response_identity", "IDENTITY_CHANGED"),
        ("oversized", "RESPONSE_TOO_LARGE"),
    ],
)
def test_initial_failure_retires(mode, status):
    with worker(mode) as backend:
        assert WarmModelGuard(backend).classify(request()).status == "ERROR"
        assert backend.retired
        assert backend.attempts[0]["status"] == status
        assert backend.attempts[0]["reaped"]


@pytest.mark.parametrize(
    "mode,status",
    [
        ("crash_second", "WORKER_CRASH"),
        ("identity_second", "IDENTITY_CHANGED"),
        ("invalid_second", "OK"),
    ],
)
def test_warm_failure_clears_prior_safe_cache(mode, status):
    with worker(mode) as backend:
        guard = WarmModelGuard(backend)
        assert guard.classify(request()).status == "OK"
        assert guard.classify(request("different")).status == "ERROR"
        assert backend.retired and guard._cache == {}
        assert backend.attempts[1]["status"] == status
        assert guard.classify(request()).status == "ERROR"
        assert sum(a["cold_start"] for a in backend.attempts) == 1
    assert all(e["reaped"] for e in backend.lifecycle_events)


@pytest.mark.parametrize("mode", ["hang_second", "kill_second"])
def test_warm_deadline_cancels_and_reaps(mode):
    with worker(mode, 2) as backend:
        guard = WarmModelGuard(backend)
        assert guard.classify(request()).status == "OK"
        assert guard.classify(request("second")).status == "ERROR"
        attempt = backend.attempts[-1]
        assert attempt["status"] == "TIMEOUT" and attempt["reaped"]
        assert not attempt["cold_start"]
        assert 2 <= attempt["elapsed_seconds"] < 5
        if mode == "kill_second":
            assert backend.lifecycle_events[-1]["method"] == "KILL"


def test_cold_deadline_includes_load():
    with worker("load_hang", 0.5) as backend:
        assert WarmModelGuard(backend).classify(request()).status == "ERROR"
        assert backend.attempts[0]["status"] == "TIMEOUT"
        assert backend.attempts[0]["cold_start"] and backend.attempts[0]["reaped"]


def test_idle_death_invalidates_cache():
    with worker() as backend:
        guard = WarmModelGuard(backend)
        assert guard.classify(request()).status == "OK"
        backend._process.kill()
        backend._process.join(2)
        assert guard.classify(request()).status == "ERROR"
        assert backend.retired and guard._cache == {}


def test_input_limit_before_spawn():
    with worker() as backend:
        with pytest.raises(ValueError, match="byte limit"):
            backend.generate(
                [{"role": "user", "content": "x" * MAX_REQUEST_BYTES}], GenerationConfig()
            )
        assert backend._process is None and backend.retired


def test_context_exception_closes_worker():
    backend = worker()
    with pytest.raises(ValueError, match="host abort"), backend:
        backend.generate([], GenerationConfig())
        raise ValueError("host abort")
    assert backend.closed and backend._process is None


def test_owner_interrupt_cancels(monkeypatch):
    with worker() as backend:
        backend.generate([], GenerationConfig())

        def interrupted(*args, **kwargs):
            raise KeyboardInterrupt

        monkeypatch.setattr(backend._complete, "wait", interrupted)
        with pytest.raises(KeyboardInterrupt):
            backend.generate([], GenerationConfig())
        assert backend.attempts[-1]["status"] == "INTERRUPTED"
        assert backend.attempts[-1]["reaped"] and backend.retired


def test_concurrent_calls_rejected_not_queued():
    with worker() as backend:
        backend._lock.acquire()
        try:
            with pytest.raises(RuntimeError, match="concurrent"):
                backend.generate([], GenerationConfig())
            with pytest.raises(RuntimeError, match="in-flight"):
                backend.close()
        finally:
            backend._lock.release()
        assert backend.attempts == []
        guard = WarmModelGuard(backend)
        guard._classification_lock.acquire()
        try:
            with pytest.raises(RuntimeError, match="concurrent guard classifications"):
                guard.classify(request())
        finally:
            guard._classification_lock.release()


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A3", "A4", "A5", "A6"])
@pytest.mark.parametrize("error", [False, True])
def test_cold_warm_runtime_parity(level, error, tmp_path):
    assert parity_case(ROOT, tmp_path, level, error=error)["valid"]


@pytest.mark.parametrize("level", ["A5", "A6"])
@pytest.mark.parametrize("external", ["mail", "webhook"])
@pytest.mark.parametrize("error", [False, True])
def test_critical_sink_parity(level, external, error, tmp_path):
    assert parity_case(ROOT, tmp_path, level, error=error, external=external)["valid"]


@pytest.mark.parametrize("terminal", ["completed", "parse_failure", "model_error", "max_steps"])
def test_every_terminal_closes_worker(terminal, tmp_path):
    read = action_response(Action(name="calculator", arguments={"expression": "1+1"}))
    responses = [read] + {
        "completed": [final_response()],
        "parse_failure": ["invalid"],
        "model_error": [],
        "max_steps": [],
    }[terminal]
    runtime = SecurityRuntime(
        RecordingBackend(responses),
        build_smoke_registry(ROOT / "data/smoke"),
        runtime_config=RuntimeConfig(
            max_steps=1 if terminal == "max_steps" else 2, max_format_retries_per_step=0
        ),
    )
    result = runtime.run_instrumented(
        PublicWorkbenchTask(task_id="awb_terminal", instruction="Chỉ tính toán."),
        output=tmp_path / "run",
        security_config=configuration("A6"),
        guard_factory=LifecycleFactory(),
        guard_execution=WarmGuardConfig(MODEL, REVISION, 10),
    )
    assert result.result.status == terminal
    metadata = json.loads((tmp_path / "run/run_metadata.json").read_text())
    assert metadata["guard_closed"]
    assert len(metadata["guard_lifecycle_events"]) == 1
    assert metadata["guard_lifecycle_events"][0]["reaped"]


def test_unexpected_host_exception_closes_worker(monkeypatch, tmp_path):
    captured = []

    def fail(self, task, **kwargs):
        backend = kwargs["_worker"]
        captured.append(backend)
        backend.generate([], GenerationConfig())
        raise ValueError("host integration fault")

    monkeypatch.setattr(SecurityRuntime, "_run_task", fail)
    runtime = SecurityRuntime(RecordingBackend([]), build_smoke_registry(ROOT / "data/smoke"))
    with pytest.raises(ValueError, match="host integration"):
        runtime.run_instrumented(
            PublicWorkbenchTask(task_id="awb_fault", instruction="Chỉ đọc."),
            output=tmp_path / "run",
            security_config=configuration("A6"),
            guard_factory=LifecycleFactory(),
            guard_execution=WarmGuardConfig(MODEL, REVISION, 10),
        )
    assert captured[0].closed and captured[0]._process is None


def test_separate_workers_reset_backend_state():
    values = []
    for _ in range(2):
        with worker("counter") as backend:
            values.append(json.loads(backend.generate([], GenerationConfig()).text)["calls"])
    assert values == [1, 1]


def test_failed_cleanup_never_claims_reaped():
    class Unreapable:
        pid = 12345
        exitcode = None

        def is_alive(self):
            return True

        def join(self, timeout):
            pass

        def terminate(self):
            pass

        def kill(self):
            pass

    backend = worker()
    fake = Unreapable()
    backend._process, backend._started = fake, True
    try:
        with pytest.raises(RuntimeError, match="cancellation failed"):
            backend.close()
        assert backend._process is fake
        assert not backend.lifecycle_events[-1]["reaped"]
    finally:
        backend._process = None  # Fake handle only; no real process was spawned.
        backend.close()
