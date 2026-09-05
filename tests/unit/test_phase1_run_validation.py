import json
from pathlib import Path

import pytest

from react_agent.schemas.trace import TraceEvent
from react_agent.validation.phase1_run import validate_phase1_run


def write_toy_run(tmp_path: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for index in range(1, 21):
        for name, step, data in (
            ("run_start", 0, {}),
            ("model_output", 1, {"raw_output": '{"final_answer":{"answer":"toy"}}'}),
            ("final_answer", 1, {"answer": "toy"}),
            ("run_end", 1, {"status": "completed", "steps": 1}),
        ):
            events.append(
                TraceEvent.model_validate(
                    {
                        "run_id": f"run_toy_{index}",
                        "task_id": f"smoke_{index:03d}",
                        "step": step,
                        "event": name,
                        "data": data,
                    }
                ).model_dump(mode="json")
            )
    (tmp_path / "summary.json").write_text(
        json.dumps(
            {
                "total_tasks": 20,
                "terminal_runs": 20,
                "completed_runs": 20,
                "crashed_runs": 0,
                "schema_validity_rate": 1.0,
                "tools_covered": [],
            }
        ),
        encoding="utf-8",
    )
    write_events(tmp_path, events)
    return events


def write_events(tmp_path: Path, events: list[dict[str, object]]) -> None:
    (tmp_path / "traces.jsonl").write_text(
        "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
    )


def test_valid_twenty_task_run_passes(tmp_path: Path) -> None:
    write_toy_run(tmp_path)
    result = validate_phase1_run(tmp_path)
    assert result["valid"], result["failures"]


def test_twenty_runs_of_one_task_do_not_pass(tmp_path: Path) -> None:
    events = write_toy_run(tmp_path)
    for event in events:
        event["task_id"] = "smoke_001"
    write_events(tmp_path, events)
    assert not validate_phase1_run(tmp_path)["valid"]


@pytest.mark.parametrize("status", ["not_terminal", [], None])
def test_invalid_terminal_payload_is_rejected(tmp_path: Path, status: object) -> None:
    events = write_toy_run(tmp_path)
    events[-1]["data"] = {"status": status}
    write_events(tmp_path, events)
    assert not validate_phase1_run(tmp_path)["valid"]


def test_inconsistent_task_id_within_run_is_rejected(tmp_path: Path) -> None:
    events = write_toy_run(tmp_path)
    events[1]["task_id"] = "smoke_999"
    write_events(tmp_path, events)
    assert not validate_phase1_run(tmp_path)["valid"]


def test_missing_final_answer_is_rejected(tmp_path: Path) -> None:
    events = write_toy_run(tmp_path)
    del events[2]
    write_events(tmp_path, events)
    assert not validate_phase1_run(tmp_path)["valid"]


def test_summary_cannot_claim_tool_coverage_absent_from_trace(tmp_path: Path) -> None:
    write_toy_run(tmp_path)
    path = tmp_path / "summary.json"
    summary = json.loads(path.read_text())
    summary["tools_covered"] = ["calculator"]
    path.write_text(json.dumps(summary), encoding="utf-8")
    assert not validate_phase1_run(tmp_path)["valid"]


def test_invalid_trace_schema_is_rejected(tmp_path: Path) -> None:
    events = write_toy_run(tmp_path)
    events[1]["event"] = "invented_event"
    write_events(tmp_path, events)
    assert not validate_phase1_run(tmp_path)["valid"]


def test_missing_artifacts_are_a_validation_failure(tmp_path: Path) -> None:
    assert not validate_phase1_run(tmp_path)["valid"]


def test_parse_failure_ends_at_last_completed_step(tmp_path: Path) -> None:
    events = write_toy_run(tmp_path)
    events[2]["event"] = "parse_error"
    events[2]["data"] = {"code": "INVALID_JSON"}
    events[3]["step"] = 0
    events[3]["data"] = {"status": "parse_failure", "steps": 0}
    write_events(tmp_path, events)
    path = tmp_path / "summary.json"
    summary = json.loads(path.read_text())
    summary["completed_runs"] = 19
    summary["schema_validity_rate"] = 19 / 20
    path.write_text(json.dumps(summary), encoding="utf-8")
    result = validate_phase1_run(tmp_path)
    assert result["valid"], result["failures"]
