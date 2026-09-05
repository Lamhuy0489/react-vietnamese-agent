import json
from pathlib import Path

from react_agent.agent import AgentRuntime
from react_agent.llm import ReplayBackend
from react_agent.schemas.task import SmokeTask
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "smoke"


def test_all_replay_smoke_tasks_reach_expected_outcome() -> None:
    tasks = [
        SmokeTask.model_validate_json(line)
        for line in (DATA_ROOT / "tasks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    responses = json.loads((DATA_ROOT / "replay_responses.json").read_text(encoding="utf-8"))
    observed_tools: set[str] = set()
    for task in tasks:
        result = AgentRuntime(
            ReplayBackend(responses[task.task_id]), build_smoke_registry(DATA_ROOT)
        ).run(task)
        assert result.status == "completed", task.task_id
        assert result.tool_sequence in task.expected.acceptable_tool_sequences, task.task_id
        assert result.final_answer is not None
        assert all(
            fact.casefold() in result.final_answer.casefold()
            for fact in task.expected.required_answer_facts
        ), task.task_id
        observed_tools.update(result.tool_sequence)
    assert observed_tools == {
        "doc_search",
        "doc_read",
        "db_query",
        "cached_search",
        "cached_fetch",
        "calculator",
        "send_email_mock",
        "post_webhook_mock",
    }
