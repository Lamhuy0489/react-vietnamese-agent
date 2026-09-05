from pathlib import Path

import pytest

from react_agent.agent import AgentRuntime
from react_agent.agent.checkpoint import run_checkpointed
from react_agent.llm import ReplayBackend
from react_agent.schemas.task import SmokeTask
from react_agent.tools.registry import ToolRegistry


def task() -> SmokeTask:
    return SmokeTask.model_validate(
        {
            "task_id": "smoke_001",
            "instruction": "Synthetic checkpoint task.",
            "category": "no_tool",
            "expected": {"acceptable_tool_sequences": [[]], "required_answer_facts": []},
            "fixture_version": "phase1_v1",
            "author": "huy",
        }
    )


def test_resume_skips_semantic_failure_and_checks_identity(
    tmp_path: Path, registry: ToolRegistry
) -> None:
    output = tmp_path / "run"
    calls = 0

    def factory(_task: object) -> AgentRuntime:
        nonlocal calls
        calls += 1
        return AgentRuntime(ReplayBackend(["bad", "bad", "bad"]), registry)

    first = run_checkpointed([task()], factory, output, {"source": "frozen"})
    assert first[0].status == "parse_failure"
    second = run_checkpointed([task()], factory, output, {"source": "frozen"}, resume=True)
    assert first == second and calls == 1
    with pytest.raises(ValueError, match="identity"):
        run_checkpointed([task()], factory, output, {"source": "changed"}, resume=True)
    with pytest.raises(ValueError, match="output exists"):
        run_checkpointed([task()], factory, output, {"source": "frozen"})


def test_trace_tamper_is_not_silently_resumed(tmp_path: Path, registry: ToolRegistry) -> None:
    output = tmp_path / "run"

    def factory(_task: object) -> AgentRuntime:
        return AgentRuntime(ReplayBackend(['{"final_answer":{"answer":"toy"}}']), registry)

    run_checkpointed([task()], factory, output, {})
    (output / "tasks/smoke_001/trace.jsonl").write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="trace hash"):
        run_checkpointed([task()], factory, output, {}, resume=True)
