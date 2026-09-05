import json
from pathlib import Path
from threading import Event

import pytest

from react_agent.broker import ToolBroker
from react_agent.logging import TraceLogger
from react_agent.tools.registry import ToolRegistry


def test_broker_assigns_call_id_and_logs_order(registry: ToolRegistry, tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    logger = TraceLogger(trace_path)
    result = ToolBroker(registry, logger).execute(
        "calculator",
        {"expression": "2 + 3"},
        run_id="run_test",
        task_id="smoke_001",
        step=1,
    )
    assert result.ok
    assert result.call_id == "call_000001"
    assert [event.event for event in logger.events] == [
        "tool_call_proposed",
        "tool_call_executed",
        "tool_result",
    ]
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert all(json.loads(line)["run_id"] == "run_test" for line in lines)


def test_broker_normalizes_unknown_tool(registry: ToolRegistry) -> None:
    logger = TraceLogger()
    result = ToolBroker(registry, logger).execute(
        "not_registered",
        {},
        run_id="run_test",
        task_id="smoke_001",
        step=1,
    )
    assert not result.ok and result.error is not None
    assert result.error.code == "UNKNOWN_TOOL"
    assert logger.events[-1].event == "tool_result"


def test_broker_catches_tool_exception(
    registry: ToolRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    tool = registry.get("calculator")
    assert tool is not None

    def broken(_arguments: object) -> object:
        raise RuntimeError("synthetic tool failure")

    monkeypatch.setattr(tool, "_run", broken)
    logger = TraceLogger()
    result = ToolBroker(registry, logger).execute(
        "calculator", {"expression": "1+1"}, run_id="run_test", task_id="smoke_001", step=1
    )
    assert not result.ok and result.error is not None
    assert result.error.code == "TOOL_RUNTIME_ERROR"
    assert [event.event for event in logger.events] == [
        "tool_call_proposed",
        "tool_call_executed",
        "tool_result",
    ]


def test_broker_returns_structured_timeout_and_test_releases_worker(
    registry: ToolRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    tool = registry.get("calculator")
    assert tool is not None
    release = Event()
    finished = Event()

    def blocked(_arguments: object) -> object:
        try:
            release.wait(timeout=2)
            return {"value": 2}
        finally:
            finished.set()

    monkeypatch.setattr(tool, "_run", blocked)
    logger = TraceLogger()
    try:
        result = ToolBroker(registry, logger, timeout_seconds=0.01).execute(
            "calculator", {"expression": "1+1"}, run_id="run_test", task_id="smoke_001", step=1
        )
        assert not result.ok and result.error is not None
        assert result.error.code == "TOOL_TIMEOUT"
    finally:
        release.set()
    assert finished.wait(timeout=2)
    assert logger.events[-1].event == "tool_result"
