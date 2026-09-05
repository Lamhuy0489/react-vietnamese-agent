import json
from pathlib import Path

from react_agent.agent import AgentRuntime, RuntimeConfig
from react_agent.llm import ReplayBackend
from react_agent.schemas.task import SmokeTask
from react_agent.tools.registry import ToolRegistry


def task() -> SmokeTask:
    return SmokeTask.model_validate(
        {
            "task_id": "smoke_001",
            "instruction": "Test synthetic runtime.",
            "category": "no_tool",
            "expected": {
                "acceptable_tool_sequences": [[]],
                "required_answer_facts": [],
            },
            "fixture_version": "phase1_v1",
            "author": "huy",
        }
    )


def test_document_trajectory_completes(registry: ToolRegistry, tmp_path: Path) -> None:
    responses = [
        '{"action":{"name":"doc_search","arguments":{"query":"học phần"}}}',
        '{"action":{"name":"doc_read","arguments":{"doc_id":"DOC_001"}}}',
        '{"final_answer":{"answer":"Bắt đầu 15/08/2026."}}',
    ]
    trace_path = tmp_path / "trace.jsonl"
    result = AgentRuntime(ReplayBackend(responses), registry).run(task(), trace_path=trace_path)
    assert result.status == "completed"
    assert result.tool_sequence == ["doc_search", "doc_read"]
    events = [
        json.loads(line)["event"] for line in trace_path.read_text(encoding="utf-8").splitlines()
    ]
    assert events[0] == "run_start"
    assert events[-1] == "run_end"
    assert "final_answer" in events


def test_malformed_output_recovers(registry: ToolRegistry) -> None:
    result = AgentRuntime(
        ReplayBackend(["not json", '{"final_answer":{"answer":"recovered"}}']),
        registry,
    ).run(task())
    assert result.status == "completed"
    assert result.parse_errors == 1


def test_repeated_malformed_output_terminates(registry: ToolRegistry) -> None:
    result = AgentRuntime(
        ReplayBackend(["bad", "still bad", "bad again"]),
        registry,
    ).run(task())
    assert result.status == "parse_failure"
    assert result.parse_errors == 3


def test_max_steps_terminates(registry: ToolRegistry) -> None:
    action = '{"action":{"name":"calculator","arguments":{"expression":"1+1"}}}'
    result = AgentRuntime(
        ReplayBackend([action, action, action]),
        registry,
        runtime_config=RuntimeConfig(max_steps=3),
    ).run(task())
    assert result.status == "max_steps"
    assert result.steps == 3
    assert len(result.tool_sequence) == 3


def test_backend_exhaustion_is_model_error(registry: ToolRegistry) -> None:
    result = AgentRuntime(ReplayBackend([]), registry).run(task())
    assert result.status == "model_error"
