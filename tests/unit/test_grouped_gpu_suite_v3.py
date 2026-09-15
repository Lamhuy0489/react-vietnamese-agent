"""Only synthetic pieces; no benchmark payloads or model execution."""

import copy
import importlib
from pathlib import Path

import pytest


@pytest.fixture
def report(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("report_phase5_grouped_suite_v3")


@pytest.fixture
def pieces():
    expected = [
        dict(
            key=f"{prefix}_SYNTHETIC_{s}__A{i}",
            shard=s,
            pair_id=f"pair{s}",
            branch=branch,
            level=f"A{i}",
        )
        for s in range(8)
        for i in range(7)
        for branch, prefix in (("attack", "ATK"), ("benign", "BEN"))
    ]
    run = dict(
        backend="hf",
        expected_tasks=112,
        tasks=expected,
        source_commit="synthetic",
        test_payload_accessed=False,
        quality_scoring=False,
    )
    result = []
    for s in range(8):
        tasks = [
            dict(
                key=t["key"],
                level=t["level"],
                terminal="completed",
                recovered=True,
                observed_graceful=True,
                startup_seconds=2,
                runtime_total_seconds=3,
                task_timing=dict(task_wall_seconds_including_setup_cleanup_recovery=5),
                guard_diagnostics=None,
                roles={},
            )
            for t in expected
            if t["shard"] == s
        ]
        result.append(
            dict(
                shard=s,
                run=copy.deepcopy(run),
                tasks=tasks,
                path_coverage=dict(
                    trace_events={"final_answer": 14}, lifecycle={"GRACEFUL:reaped": 24}
                ),
                classifications=[],
            )
        )
    return result


def test_complete_schedule_not_quality(report, pieces):
    result = report.combine(pieces)
    assert result["complete_schedule"]
    assert result["totals"]["tasks_count"] == 112
    assert result["totals"]["task_wall_seconds_total"] == 560
    assert all(row["tasks_count"] == 16 for row in result["levels"].values())
    assert result["trace_events"].get("tool_call_executed", 0) == 0
    assert not result["quality_scoring"] and not result["phase5_accepted"]


def test_failures_and_no_response_counts_retained(report, pieces):
    pieces[0]["tasks"][4]["terminal"] = "model_error"
    pieces[0]["tasks"][4]["observed_graceful"] = False
    pieces[0]["tasks"][4]["guard_diagnostics"] = dict(
        joined=[
            dict(
                stage="PRE", classification_status="ERROR", diagnostic=dict(category="json_syntax")
            )
        ]
    )
    pieces[0]["classifications"] = [
        dict(stage="PRE", status="ERROR", error_code="INVALID_OUTPUT"),
        dict(stage="POST", status="ERROR", error_code="BACKEND_FAILURE"),
    ]
    result = report.combine(pieces)
    assert result["totals"]["terminals"] == {"completed": 111, "model_error": 1}
    assert result["totals"]["returned_guard_classifications"] == {"PRE:ERROR": 1}
    assert result["guard_response_categories"] == {"json_syntax": 1}
    assert sum(r["count"] for r in result["guard_classifications"]) == 2
    assert result["totals"]["all_graceful_tasks"] == 111


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_shard",
        "duplicate_shard",
        "duplicate_task",
        "wrong_level",
        "wrong_run",
        "test_access",
        "bool_shard",
        "wrong_pair",
    ],
)
def test_reject_incompatible_or_incomplete(report, pieces, mutation):
    if mutation == "missing_shard":
        pieces.pop()
    elif mutation == "duplicate_shard":
        pieces[7]["shard"] = 6
    elif mutation == "duplicate_task":
        pieces[0]["tasks"][1] = pieces[0]["tasks"][0]
    elif mutation == "wrong_level":
        pieces[0]["tasks"][0]["level"] = "A6"
    elif mutation == "wrong_run":
        pieces[7]["run"]["source_commit"] = "other-source"
    elif mutation == "test_access":
        pieces[0]["run"]["test_payload_accessed"] = True
    elif mutation == "bool_shard":
        pieces[0]["shard"] = False
    else:
        pieces[0]["run"]["tasks"][0]["branch"] = "benign"
    with pytest.raises((ValueError, AssertionError)):
        report.combine(pieces)
