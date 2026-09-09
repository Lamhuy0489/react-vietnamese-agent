"""Real spawn workers with tiny synthetic backends; no GPU/model weights."""

from __future__ import annotations

import json
import os
import signal
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.model_pair_v1 import (
    READY_ACK,
    READY_COMMAND,
    ModelIdentity,
    ModelPair,
    PairConfig,
    ReadyBackend,
)


@dataclass(frozen=True)
class Factory:
    role: str
    root: Path
    behavior: str = ""

    def __call__(self) -> LLMBackend:
        if self.role == "guard" and not (self.root / "agent_load.json").exists():
            raise ValueError("guard loaded before agent")
        if self.behavior == "ignore_term":
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        (self.root / f"{self.role}_load.json").write_text(json.dumps({"pid": os.getpid()}))
        if self.behavior == "load_error":
            raise ValueError("synthetic sensitive load failure")
        if self.behavior == "load_timeout":
            time.sleep(30)
        return Backend(self.role, self.behavior)


class Backend:
    def __init__(self, role: str, behavior: str = "") -> None:
        self.model_id = role
        self.model_revision = "wrong" if behavior == "identity" else "v1"
        self.behavior = behavior
        self.calls = 0

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        self.calls += 1
        if self.behavior == "error":
            raise RuntimeError("synthetic sensitive error")
        if self.behavior in {"timeout", "ignore_term"}:
            time.sleep(30)
        if self.behavior == "drift":
            self.model_revision = "drift"
        if self.behavior == "exit":
            os._exit(7)
        return ModelResponse(
            text=str(self.calls),
            model_id=self.model_id,
            model_revision="wrong" if self.behavior == "response_identity" else self.model_revision,
        )


def pair(root: Path, agent: str = "", guard: str = "") -> ModelPair:
    return ModelPair(
        Factory("agent", root, agent),
        Factory("guard", root, guard),
        PairConfig(
            ModelIdentity("agent", "v1"),
            ModelIdentity("guard", "v1"),
            agent_start_seconds=3,
            guard_start_seconds=3,
            agent_call_seconds=0.5,
            guard_call_seconds=0.5,
            terminate_grace_seconds=0.1,
            kill_grace_seconds=1,
        ),
    )


def generate(instance: ModelPair, role: Any = "agent") -> ModelResponse:
    return instance.generate(
        role,
        [{"role": "user", "content": "synthetic request"}],
        GenerationConfig(max_new_tokens=512 if role == "agent" else 128),
    )


def assert_reaped(instance: ModelPair) -> None:
    for worker in instance.snapshot()["workers"].values():
        assert not worker["handle_pending"]
        assert worker["closed"]
        assert all(event["reaped"] for event in worker["lifecycle"])


def test_readiness_does_not_generate() -> None:
    raw = Backend("agent")
    backend = ReadyBackend(raw)
    result = backend.generate([{"role": "user", "content": READY_COMMAND}], GenerationConfig())
    assert result.text == READY_ACK and raw.calls == 0
    with pytest.raises(ValueError):
        backend.generate([{"role": "user", "content": READY_COMMAND}], GenerationConfig(seed=2))


def test_real_spawn_order_reuse_and_text_free_snapshot(tmp_path: Path) -> None:
    instance = pair(tmp_path)
    with instance:
        assert instance.state == "READY"
        agent_pid = json.loads((tmp_path / "agent_load.json").read_text())["pid"]
        guard_pid = json.loads((tmp_path / "guard_load.json").read_text())["pid"]
        assert len({agent_pid, guard_pid, os.getpid()}) == 3
        assert [e["role"] for e in instance.events if e["stage"] == "ready"] == ["agent", "guard"]
        for role in ("agent", "guard"):
            assert generate(instance, role).text == "1"
            assert generate(instance, role).text == "2"
            attempts = instance.snapshot()["workers"][role]["attempts"]
            assert [r["cold_start"] for r in attempts] == [True, False, False]
            assert len({r["pid"] for r in attempts}) == 1
            assert (
                attempts[0]["execution_config_sha256"]
                == instance.config.execution(role, cold=True).identity
            )
            assert (
                attempts[1]["execution_config_sha256"]
                == instance.config.execution(role, cold=False).identity
            )
        snapshot = instance.snapshot()
        snapshot["events"].clear()
        assert instance.events
        assert "synthetic request" not in json.dumps(instance.snapshot())
    assert instance.state == "CLOSED"
    assert_reaped(instance)
    assert [e["role"] for e in instance.events if e["stage"] == "cleanup"] == ["guard", "agent"]


@pytest.mark.parametrize("role", ["agent", "guard"])
@pytest.mark.parametrize("failure", ["load_error", "identity", "load_timeout"])
def test_start_failure_cleans_both(tmp_path: Path, role: str, failure: str) -> None:
    instance = pair(tmp_path, **{role: failure})
    with pytest.raises((ValueError, RuntimeError, TimeoutError)):
        instance.start()
    assert instance.state == "FAILED"
    assert_reaped(instance)
    if role == "agent":
        assert not (tmp_path / "guard_load.json").exists()
    with pytest.raises(RuntimeError):
        instance.start()
    with pytest.raises(RuntimeError):
        generate(instance)


@pytest.mark.parametrize("role", ["agent", "guard"])
@pytest.mark.parametrize(
    "failure", ["error", "timeout", "ignore_term", "drift", "exit", "response_identity"]
)
def test_call_failure_cleans_sibling(tmp_path: Path, role: str, failure: str) -> None:
    instance = pair(tmp_path, **{role: failure})
    instance.start()
    with pytest.raises((RuntimeError, TimeoutError)):
        generate(instance, role)
    assert instance.state == "FAILED"
    assert_reaped(instance)
    snap = instance.snapshot()
    if failure == "ignore_term":
        assert snap["workers"][role]["lifecycle"][0]["method"] == "KILL"
        assert snap["workers"][role]["lifecycle"][0]["exitcode"] == -9
    assert "synthetic sensitive" not in json.dumps(snap)
    before = [len(w["attempts"]) for w in snap["workers"].values()]
    with pytest.raises(RuntimeError):
        generate(instance)
    assert before == [len(w["attempts"]) for w in instance.snapshot()["workers"].values()]


@pytest.mark.parametrize(
    "case", ["reserved", "role", "oversize", "dead_sibling", "config", "worker_config"]
)
def test_invalid_request_or_owner_state(tmp_path: Path, case: str) -> None:
    instance = pair(tmp_path)
    instance.start()
    messages = [{"role": "user", "content": "fixture"}]
    role = "agent"
    if case == "reserved":
        messages[0]["content"] = READY_COMMAND
    elif case == "oversize":
        messages[0]["content"] = "x" * 140000
    elif case == "role":
        role = "other"
    elif case == "dead_sibling":
        process = instance._workers["guard"]._process
        process.terminate()
        process.join(2)
    elif case == "config":
        instance.config = replace(instance.config, agent_call_seconds=9)
    else:
        instance._workers["agent"].config = instance.config.execution("agent", cold=True)
    with pytest.raises((ValueError, RuntimeError)):
        instance.generate(role, messages, GenerationConfig())  # type: ignore[arg-type]
    assert instance.state == "FAILED"
    assert_reaped(instance)


def test_repeated_start_and_close_without_start(tmp_path: Path) -> None:
    instance = pair(tmp_path)
    with pytest.raises(RuntimeError):
        generate(instance)
    instance.close()
    instance.close()
    assert_reaped(instance)
    assert not list(tmp_path.iterdir())
    with pytest.raises(RuntimeError):
        instance.start()
    instance = pair(tmp_path)
    with instance:
        with pytest.raises(RuntimeError):
            instance.start()
    assert_reaped(instance)


def test_owner_and_concurrency_rejected(tmp_path: Path) -> None:
    instance = pair(tmp_path)
    instance._owner = -1
    for method in (instance.start, instance.close, instance.snapshot):
        with pytest.raises(RuntimeError, match="another process"):
            method()
    instance._owner = os.getpid()
    instance._lock.acquire()
    try:
        for method in (instance.start, instance.close, instance.snapshot):
            with pytest.raises(RuntimeError, match="in flight"):
                method()
    finally:
        instance._lock.release()
    instance.close()


def test_context_error_still_closes(tmp_path: Path) -> None:
    instance = pair(tmp_path)
    with pytest.raises(KeyboardInterrupt), instance:
        raise KeyboardInterrupt()
    assert_reaped(instance)


def test_cleanup_failure_attempts_both_and_retains_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance = pair(tmp_path)
    instance.start()
    guard = instance._workers["guard"]
    original = guard.close

    def fail() -> None:
        raise RuntimeError("synthetic cleanup details")

    monkeypatch.setattr(guard, "close", fail)
    try:
        with pytest.raises(RuntimeError, match="cleanup incomplete"):
            instance.close()
        snap = instance.snapshot()
        assert snap["workers"]["guard"]["handle_pending"]
        assert not snap["workers"]["agent"]["handle_pending"]
        assert instance.state == "FAILED"
        assert "synthetic cleanup details" not in json.dumps(snap)
    finally:
        monkeypatch.setattr(guard, "close", original)
        instance.close()
    assert_reaped(instance)


@pytest.mark.parametrize("value", [True, 0, -1, float("nan"), float("inf")])
def test_deadline_validation(value: float) -> None:
    with pytest.raises(ValueError):
        PairConfig(ModelIdentity("a", "v1"), ModelIdentity("g", "v1"), agent_start_seconds=value)


def test_defaults_and_identity() -> None:
    config = PairConfig(ModelIdentity("a", "v1"), ModelIdentity("g", "v1"))
    assert config.execution("agent", cold=True).timeout_seconds == 1200
    assert config.execution("agent", cold=False).timeout_seconds == 180
    assert config.execution("guard", cold=True).timeout_seconds == 120
    assert replace(config, agent_call_seconds=1).sha256 != config.sha256
    with pytest.raises(ValueError):
        ModelIdentity("", "v1")


def test_distinct_fresh_pairs(tmp_path: Path) -> None:
    pids = []
    for i in range(2):
        root = tmp_path / str(i)
        root.mkdir()
        with pair(root) as instance:
            assert generate(instance).text == "1"
            pids.extend(e["pid"] for e in instance.events if e["stage"] == "ready")
    assert len(set(pids)) == 4
