"""Read-only controls for the Phase 5 20-DoD readiness audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from react_agent.validation.phase5_gate_readiness_v1 import (
    GateAuditError,
    audit,
    validate_api_pilot,
)

ROOT = Path(__file__).resolve().parents[2]


def test_audit_has_all_dods_and_never_promotes_phase() -> None:
    report = audit(ROOT)
    assert report["schema_version"] == "phase5_gate_readiness_v1"
    assert report["phase5_accepted"] is False
    assert report["test_payloads_read"] == 0
    assert report["private_ground_truth_read"] == 0
    assert [gate["id"] for gate in report["gates"]] == list(range(1, 21))
    assert all(gate["overall_status"] == "open" for gate in report["gates"])
    assert report["cpu_evidence_count"] == 16
    assert report["diagnostic_only_count"] == 3
    assert report["missing_cpu_evidence_count"] == 1


def test_api_metadata_validation_reads_no_task_payloads(tmp_path: Path) -> None:
    pilot = tmp_path / "pilot"
    pilot.mkdir()
    (pilot / "manifest.json").write_text(
        json.dumps({"test_tasks_loaded": 0, "private_ground_truth_loaded": 0}),
        encoding="utf-8",
    )
    (pilot / "summary.json").write_text(
        json.dumps(
            {
                "expected": 37,
                "completed": 37,
                "failed": 0,
                "interrupted": 0,
                "missing": 0,
                "test_tasks_loaded": 0,
                "private_ground_truth_loaded": 0,
                "agent_tasks": 21,
                "guard_controls": 16,
            }
        ),
        encoding="utf-8",
    )
    result = validate_api_pilot(pilot, tmp_path)
    assert result["expected"] == 37
    assert result["evaluation_path"] is None


def test_api_metadata_rejects_forbidden_runtime_access(tmp_path: Path) -> None:
    pilot = tmp_path / "pilot"
    pilot.mkdir()
    (pilot / "manifest.json").write_text(
        json.dumps({"test_tasks_loaded": 1, "private_ground_truth_loaded": 0}),
        encoding="utf-8",
    )
    (pilot / "summary.json").write_text(
        json.dumps(
            {
                "expected": 0,
                "completed": 0,
                "failed": 0,
                "interrupted": 0,
                "missing": 0,
                "test_tasks_loaded": 0,
                "private_ground_truth_loaded": 0,
                "agent_tasks": 1,
                "guard_controls": 1,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(GateAuditError, match="Test/private ground truth"):
        validate_api_pilot(pilot, tmp_path)


def test_api_metadata_rejects_partial_terminal_set(tmp_path: Path) -> None:
    pilot = tmp_path / "pilot"
    pilot.mkdir()
    (pilot / "manifest.json").write_text("{}", encoding="utf-8")
    (pilot / "summary.json").write_text(
        json.dumps(
            {
                "expected": 2,
                "completed": 1,
                "failed": 0,
                "interrupted": 0,
                "missing": 1,
                "test_tasks_loaded": 0,
                "private_ground_truth_loaded": 0,
                "agent_tasks": 1,
                "guard_controls": 1,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(GateAuditError, match="incomplete"):
        validate_api_pilot(pilot, tmp_path)


def test_api_metadata_rejects_private_or_test_path(tmp_path: Path) -> None:
    for name in ("private", "test"):
        pilot = tmp_path / name
        pilot.mkdir()
        with pytest.raises(GateAuditError, match="Test or private"):
            validate_api_pilot(pilot, tmp_path)
