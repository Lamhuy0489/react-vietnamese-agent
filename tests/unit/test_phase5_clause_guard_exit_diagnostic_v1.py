"""Host-only worker-exit diagnostic controls; no model or held-out data."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "results/phase5_clause_dev_v2_gpu_audit01.json"
RAW = ROOT / "results/phase5_clause_dev_v2_gpu_monitor01/raw"


def diagnostic():  # type: ignore[no-untyped-def]
    path = ROOT / "scripts/diagnose_phase5_clause_guard_exit_v1.py"
    spec = importlib.util.spec_from_file_location("phase5_guard_exit_diagnostic_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not AUDIT.is_file() or not RAW.is_dir(), reason="downloaded raw is optional")
def test_full_local_exit_audit_is_stable_and_retains_terminate() -> None:
    check = diagnostic()
    audit = json.loads(AUDIT.read_text())
    first = check.diagnose(audit, RAW)
    assert first == check.diagnose(audit, RAW)
    assert first["task_count"] == 32 and first["all_workers_reaped"]
    assert first["methods"] == {
        "agent": {"GRACEFUL": 32},
        "guard": {"GRACEFUL": 31, "TERMINATE": 1},
    }
    assert len(first["anomalies"]) == 1
    guard = first["anomalies"][0]["roles"]["guard"]
    assert guard["host_role_attempts"] == 0 and guard["request_attempts"] == 1
    assert guard["exitcode"] == -15 and guard["stop_received"] and guard["serve_returned"]
    assert guard["finalizers_returned"] and guard["threads_returned"]
    assert first["root_cause_proven"] is False
    assert first["phase5_lifecycle_accepted"] is False
    assert first["test_payloads_read"] == first["oracle_records_read"] == 0
    audit["valid"] = False
    with pytest.raises(ValueError, match="authenticated Dev32"):
        check.diagnose(audit, RAW)


@pytest.mark.skipif(not AUDIT.is_file() or not RAW.is_dir(), reason="downloaded raw is optional")
def test_lifecycle_method_tamper_is_not_graceful() -> None:
    check = diagnostic()
    audit = json.loads(AUDIT.read_text())
    selected = audit["native"]["shards"][0]["tasks"][0]
    key = selected["key"]
    directory = RAW / "dev32/shard0/tasks" / key
    row = check.lifecycle_row(key, selected, directory)
    assert row["roles"]["guard"]["method"] == "TERMINATE"
    assert row["roles"]["guard"]["exitcode"] == -15
    assert (
        row["roles"]["guard"]["elapsed_seconds"]
        > row["roles"]["guard"]["graceful_shutdown_seconds"]
    )
