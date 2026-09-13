"""Versioned real-spawn regressions; reuse frozen v1 fixtures without editing them."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import test_phase5_pair_runtime as legacy

from react_agent.llm.model_pair_v1 import ModelPair
from react_agent.security_v1.pair_runtime_v2 import run_pair_task
from react_agent.validation.pair_runtime_audit_v1 import audit_task as old_audit
from react_agent.validation.pair_runtime_audit_v2 import audit_task


@pytest.fixture(autouse=True)
def v2_entry(monkeypatch):
    monkeypatch.setattr(legacy, "run_pair_task", run_pair_task)
    monkeypatch.setattr(legacy, "audit_task", audit_task)


@pytest.mark.parametrize("level", [f"A{i}" for i in range(7)])
@pytest.mark.parametrize("terminal", ["completed", "parse_failure", "max_steps", "model_error"])
def test_all_levels_and_terminals(tmp_path, level, terminal):
    legacy.test_real_spawn_pair_all_levels_terminals_and_cleanup(tmp_path, level, terminal)


@pytest.mark.parametrize("level", [f"A{i}" for i in range(7)])
def test_v7_observable_parity(tmp_path, level):
    legacy.test_observable_parity_with_v7(tmp_path, level)
    legacy.check_cleanup(tmp_path / "spawned", level)


@pytest.mark.parametrize("failure", ["load", "timeout"])
@pytest.mark.parametrize("role", ["agent", "guard"])
def test_failed_startup_or_call_timing(tmp_path, failure, role):
    legacy.test_startup_and_inference_failures_keep_cleanup_evidence(tmp_path, failure, role)
    receipt = legacy.check_cleanup(tmp_path / "run", "A6")
    assert receipt["startup_completed"] is (failure != "load")
    assert receipt["startup_seconds"] > 0


@pytest.mark.parametrize("level", ["A0", "A1"])
def test_agent_only_failed_startup_timing(tmp_path, level):
    with pytest.raises(RuntimeError):
        legacy.invoke(tmp_path / "run", level=level, agent_failure="load")
    receipt = legacy.check_cleanup(tmp_path / "run", level)
    assert not receipt["startup_completed"]
    assert receipt["startup_seconds"] > 0
    assert receipt["terminal"] is None


def test_post_startup_cancellation(tmp_path):
    legacy.test_cancellation_between_startup_and_runtime_reaps_both_workers(tmp_path)
    assert legacy.check_cleanup(tmp_path / "run", "A6")["startup_completed"]


def test_interruption_during_guard_startup(tmp_path, monkeypatch):
    from react_agent.security_v1.warm_guard import WarmGuardBackend

    original = WarmGuardBackend.generate

    def cancel(worker, messages, config):
        if worker.model_id == "guard":
            raise KeyboardInterrupt("synthetic startup cancellation")
        return original(worker, messages, config)

    monkeypatch.setattr(WarmGuardBackend, "generate", cancel)
    with pytest.raises(KeyboardInterrupt):
        legacy.invoke(tmp_path / "run")
    receipt = legacy.check_cleanup(tmp_path / "run", "A6")
    assert not receipt["startup_completed"] and receipt["startup_seconds"] > 0
    assert receipt["error_class"] == "KeyboardInterrupt"


def test_invalid_guard_rejection_is_not_worker_inference(tmp_path):
    legacy.test_invalid_guard_output_retires_pair_and_discards_cache(tmp_path)
    receipt = legacy.check_cleanup(tmp_path / "run", "A6")
    rejected = receipt["host_role_attempts"]["agent"][-1]
    assert rejected["status"] == "ERROR"
    assert rejected["pair_events_before"] == rejected["pair_events_after"]
    assert rejected["worker_attempts_before"] == rejected["worker_attempts_after"]


def kill_after_response(monkeypatch, role, victim):
    original = ModelPair._alive
    killed = []

    def check(pair):
        original(pair)
        if not killed and len(pair._workers[role].attempts) > 1:
            process = pair._workers[victim]._process
            assert process is not None
            killed.append(process.pid)
            process.terminate()
            process.join(timeout=5)
            assert not process.is_alive()
            original(pair)

    monkeypatch.setattr(ModelPair, "_alive", check)
    return killed


@pytest.mark.parametrize("role", ["agent", "guard"])
@pytest.mark.parametrize("victim", ["agent", "guard"])
def test_real_worker_death_after_response(tmp_path, monkeypatch, role, victim):
    killed = kill_after_response(monkeypatch, role, victim)
    result = legacy.invoke(tmp_path / "run")
    assert killed and result.result.status == "model_error"
    receipt = legacy.check_cleanup(tmp_path / "run", "A6")
    worker = receipt["snapshot"]["workers"][role]["attempts"][-1]
    host = receipt["host_role_attempts"][role][0]
    assert worker["status"] == "OK"
    assert host["status"] == "ERROR"
    assert host["error_class"] == "RuntimeError"
    assert receipt["snapshot"]["state"] == "FAILED"
    # Old source remains useful to reproduce the false rejection, not to edit raw data.
    with pytest.raises(ValueError, match="host/worker result mismatch"):
        old_audit(tmp_path / "run")


@pytest.mark.parametrize("entitled", [True, False])
def test_final_entitlement_unchanged(tmp_path, entitled):
    legacy.test_pair_retains_final_entitlement_on_actual_database_rows(tmp_path, entitled)


@pytest.mark.parametrize("level", ["A4", "A5", "A6"])
def test_scope_unchanged(tmp_path, level):
    legacy.test_pair_retains_scope_denial_before_broker(tmp_path, level)


def test_external_veto_unchanged(tmp_path):
    legacy.test_pair_retains_guard_veto_on_external_sink(tmp_path)


def test_fresh_output_required_before_startup(tmp_path):
    legacy.test_existing_output_rejected_before_worker_start(tmp_path)


@pytest.mark.parametrize("fault", ["schema", "attempt", "readiness", "host_count"])
def test_original_corruption_controls(tmp_path, monkeypatch, fault):
    legacy.test_joined_audit_detects_corrupt_views_without_rewriting_raw_files(
        tmp_path, monkeypatch, fault
    )


@pytest.mark.parametrize(
    "fault", ["event_status", "event_range", "startup_zero", "completed", "nan"]
)
def test_v2_corrupt_receipt_views(tmp_path, monkeypatch, fault):
    root = tmp_path / "run"
    kill_after_response(monkeypatch, "agent", "guard")
    legacy.invoke(root)
    assert audit_task(root)["valid"]
    original = Path.read_text

    def corrupted(path, *args, **kwargs):
        raw = original(path, *args, **kwargs)
        if path != root / "pair_runtime.json":
            return raw
        receipt = json.loads(raw)
        if fault == "event_status":
            for event in receipt["snapshot"]["events"]:
                if event["stage"] == "generate":
                    event["status"] = "OK"
        elif fault == "event_range":
            receipt["host_role_attempts"]["agent"][0]["pair_events_after"] = 0
        elif fault == "startup_zero":
            receipt["startup_seconds"] = 0
        elif fault == "completed":
            receipt["startup_completed"] = False
        else:
            receipt["total_seconds"] = float("nan")
        return json.dumps(receipt)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_text", corrupted)
        with pytest.raises(ValueError):
            audit_task(root)
    assert audit_task(root)["valid"]
