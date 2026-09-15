"""Synthetic arithmetic/mutation checks; fixtures are not native authentication evidence."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def case(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "observer_report", ROOT / "scripts/report_phase5_observer_gpu_v2.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    raw = tmp_path / "raw"
    base = raw / "observer/tasks/SYNTHETIC/execution"
    (base / "runtime").mkdir(parents=True)
    event = dict(method="TERMINATE", reaped=True, pid=1)
    (base / "pair_runtime.json").write_text(
        json.dumps(
            dict(
                snapshot=dict(workers=dict(agent=dict(lifecycle=[event]), guard=dict(lifecycle=[])))
            )
        )
    )
    (base / "runtime/trace_guard.jsonl").write_text(
        json.dumps(dict(outcome=dict(error_code="BACKEND_FAILURE"))) + "\n"
    )
    roles = {role: dict(calls=[], failed_or_partial=False) for role in ("agent", "guard")}
    roles["agent"]["calls"] = [
        dict(input_tokens=10, output_tokens=4, generate_seconds=2.0, call_seconds=2.5)
    ]
    response = dict(
        stage="PRE",
        classification_status="ERROR",
        diagnostic=dict(
            baseline=dict(category="json_syntax"), framing="fenced", syntax_kind="expected_value"
        ),
    )
    task = dict(
        key="SYNTHETIC",
        terminal="model_error",
        executed_tool_calls=0,
        guard_diagnostics=dict(joined=[response]),
        recovered=True,
        roles=roles,
        startup_seconds=3.0,
        total_seconds=6.0,
    )
    verified = dict(
        valid=True,
        source_authenticated=True,
        raw_sha256=module.inventory(raw),
        native=dict(tasks=[task], expected=1),
        source_commit="a" * 40,
        notebook_url="synthetic",
        kernel_version=1,
        remote_sha256={},
    )
    return module, raw, verified


def test_descriptive_counts_and_denominators(case):
    module, raw, verified = case
    result = module.summarize(verified, raw)
    assert result["terminal_counts"] == {"model_error": 1}
    assert result["guard_stage_categories"] == {"PRE:json_syntax": 1}
    assert result["tasks"][0]["guard_backend_failure_events"] == 1
    assert result["tasks"][0]["guard_responses"] == 1
    assert result["shutdown_methods"] == {"TERMINATE": 1}
    assert result["role_totals"]["agent"]["pooled_output_tokens_per_generate_second"] == 2
    assert result["role_totals"]["guard"]["pooled_output_tokens_per_generate_second"] is None
    assert result["phase5_accepted"] is False
    assert result["semantic_utility_measured"] is False
    assert module.summarize(verified, raw) == result


def test_raw_mutation_rejected(case):
    module, raw, verified = case
    (raw / "extra.json").write_text("{}")
    with pytest.raises(ValueError, match="raw hash"):
        module.summarize(verified, raw)


@pytest.mark.parametrize("field", ["valid", "source_authenticated"])
def test_unauthenticated_input_rejected(case, field):
    module, raw, verified = case
    verified[field] = False
    with pytest.raises(ValueError, match="authenticated"):
        module.summarize(verified, raw)


def test_duplicate_tasks_rejected(case):
    module, raw, verified = case
    verified["native"]["tasks"] *= 2
    verified["native"]["expected"] = 2
    with pytest.raises(ValueError, match="unique"):
        module.summarize(verified, raw)


def test_cli_reaudits_instead_of_loading_valid_flag(case, monkeypatch):
    module, raw, verified = case
    called = []

    def reject(*args):
        called.append(args)
        raise ValueError("release pin mismatch")

    monkeypatch.setattr(module, "audit", reject)
    args = ["report"]
    for name in ("raw", "remote", "preflight", "submission", "observation"):
        args.extend(["--" + name, str(raw)])
    args.extend(["--output", str(raw.parent / "report")])
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(ValueError, match="release pin"):
        module.main()
    assert len(called) == 1
    assert not (raw.parent / "report").exists()
