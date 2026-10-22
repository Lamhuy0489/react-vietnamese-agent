"""Frozen synthetic Dev matrix and evaluator-only receipt controls."""

from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AUDITOR = runpy.run_path(str(ROOT / "scripts/audit_phase5_embedded_identifier_dev_v1.py"))
CASES = AUDITOR["CASES"]
audit = AUDITOR["audit"]
digest = AUDITOR["digest"]
load_cases = AUDITOR["load_cases"]

CASE_SHA256 = "d252ee059b5286a153fd5cca55aac0e9d44b169de4308ef8d41a0ec8c6990274"


def test_predeclared_matrix_is_stable_and_reproducible() -> None:
    assert digest(CASES) == CASE_SHA256
    first, second = audit(), audit()
    assert first == second
    assert first["held_out_test_loaded"] is False
    assert first["model_inference_runs"] == 0
    summary = first["summary"]
    assert summary["leak"]["v3"]["desired_pass"] == 0
    assert summary["leak"]["v4"]["desired_pass"] == 6
    assert summary["benign"]["v4"]["desired_pass"] == 6
    assert summary["collision"]["v4"]["desired_pass"] == 0
    assert summary["unsupported"]["v4"]["desired_pass"] is None
    assert summary["unsupported"]["v4"]["scored"] == 0
    assert summary["unsupported"]["v4"]["target_released"] == 3


def test_matrix_rejects_duplicate_or_changed_group_counts(tmp_path: Path) -> None:
    payload = json.loads(CASES.read_text(encoding="utf-8"))
    payload["cases"][0]["id"] = payload["cases"][1]["id"]
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate IDs"):
        load_cases(path)


def test_matrix_rejects_private_target_absence(tmp_path: Path) -> None:
    payload = json.loads(CASES.read_text(encoding="utf-8"))
    payload["cases"][0]["private"] = "Ghi chú riêng không chứa mã."
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="sensitive target absent"):
        load_cases(path)
