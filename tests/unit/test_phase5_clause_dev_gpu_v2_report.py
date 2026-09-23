"""Descriptive Dev32 report counts only observable outcomes, not answer text."""

import importlib.util
import json
from pathlib import Path

import pytest


def reporter():
    path = Path(__file__).resolve().parents[2] / "scripts/report_phase5_clause_dev_gpu_v2.py"
    spec = importlib.util.spec_from_file_location("clause_dev_gpu_v2_report_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_nearest_rank_is_explicit():
    report = reporter()
    assert report.nearest_rank([5.0, 1.0, 3.0, 2.0], 0.5) == 2.0
    assert report.nearest_rank([5.0, 1.0, 3.0, 2.0], 0.95) == 5.0
    with pytest.raises(ValueError, match="nonempty"):
        report.nearest_rank([], 0.95)


def test_task_row_counts_events_without_copying_final_text(tmp_path):
    report = reporter()
    runtime = tmp_path / "execution/runtime"
    runtime.mkdir(parents=True)
    legacy = [
        ("run_start", {}),
        ("model_output", {}),
        ("tool_call_proposed", {"name": "doc_read"}),
        ("tool_call_executed", {}),
        ("tool_result", {"ok": False}),
        ("final_answer", {"answer": "PRIVATE_TEST_STRING"}),
        ("run_end", {}),
    ]
    (runtime / "trace_legacy.jsonl").write_text(
        "\n".join(json.dumps({"event": event, "data": data}) for event, data in legacy) + "\n"
    )
    (runtime / "trace_security.jsonl").write_text(
        json.dumps({"event": "decision", "data_json": json.dumps({
            "stage": "PRE", "effect": "DENY", "component": "a6_composition_v1"
        })}) + "\n"
    )
    task = {
        "key": "ATK_CAND_EXAMPLE__A6",
        "level": "A6",
        "terminal": "completed",
        "recovered": True,
        "observed_graceful": False,
        "startup_seconds": 3.0,
        "task_timing": {"task_wall_seconds_including_setup_cleanup_recovery": 5.0},
        "roles": {"agent": {"calls": [{}]}, "guard": {"calls": [{}]}},
        "guard_diagnostics": {"constrained": {"observer": {
            "response_records": 1,
            "joined": [{"stage": "PRE", "classification_status": "OK"}],
        }}},
    }
    row, events, security, tools = report.task_row(task, tmp_path)
    assert (row["agent_calls"], row["guard_calls"], row["guard_ok"]) == (1, 1, 1)
    assert (row["tool_proposals"], row["tool_results_error"], row["pre_denials"]) == (1, 1, 1)
    assert events["final_answer"] == security["decision"] == tools["doc_read"] == 1
    assert "PRIVATE_TEST_STRING" not in json.dumps(row)


def test_report_rejects_unverified_or_incomplete_audit(tmp_path):
    report = reporter()
    with pytest.raises(ValueError, match="v2 audit protocol"):
        report.summarize({"protocol": "other"}, tmp_path)
    with pytest.raises(ValueError, match="release audit"):
        report.summarize(
            {"protocol": "clause_dev32_gpu_release_audit_v2", "valid": False}, tmp_path
        )
