"""Synthetic descriptive summaries retain failures and distinguish timing denominators."""

import importlib
from pathlib import Path


def test_failed_workers_stay_in_denominator(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    report = importlib.import_module("report_phase5_grouped_gpu_v3")
    task = dict(
        key="ATK_SYNTHETIC__A2",
        level="A2",
        terminal="model_error",
        recovered=True,
        observed_graceful=False,
        startup_seconds=10,
        runtime_total_seconds=15,
        task_timing=dict(task_wall_seconds_including_setup_cleanup_recovery=22),
        guard_diagnostics=dict(joined=[dict(stage="PRE", classification_status="ERROR")]),
        roles=dict(
            agent=dict(
                worker_attempts=2, policy_attention_verified=False, failed_or_partial=True, calls=[]
            ),
            guard=dict(
                worker_attempts=1,
                policy_attention_verified=True,
                failed_or_partial=False,
                calls=[dict(input_tokens=30, output_tokens=4, generate_seconds=2)],
            ),
        ),
    )
    result = report.summarize([task])
    assert result["terminals"] == {"model_error": 1}
    assert result["returned_guard_classifications"] == {"PRE:ERROR": 1}
    assert result["recovered_tasks"] == 1 and result["all_graceful_tasks"] == 0
    assert result["roles"]["agent"]["worker_attempts"] == 2
    assert result["roles"]["agent"]["tokens_per_generate_second_joined_only"] is None
    assert result["roles"]["guard"]["tokens_per_generate_second_joined_only"] == 2
    assert result["tasks"][0]["branch"] == "attack"
    assert result["tasks"][0]["valid_guard_responses"] == 0


def test_agent_only_benign_has_no_guard_counts(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    report = importlib.import_module("report_phase5_grouped_gpu_v3")
    task = dict(
        key="BEN_SYNTHETIC__A0",
        level="A0",
        terminal="completed",
        recovered=True,
        observed_graceful=True,
        startup_seconds=2,
        runtime_total_seconds=5,
        task_timing=dict(task_wall_seconds_including_setup_cleanup_recovery=12),
        guard_diagnostics=None,
        roles={},
    )
    result = report.summarize([task])
    assert result["returned_guard_classifications"] == {}
    assert result["tasks"][0]["branch"] == "benign"
    assert result["task_wall_seconds_total"] == 12
    assert result["startup_seconds_total"] == 2
