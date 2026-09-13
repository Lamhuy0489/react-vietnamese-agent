from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def load_auditor():
    path = Path(__file__).resolve().parents[2] / "scripts/verify_phase5_remediation.py"
    spec = importlib.util.spec_from_file_location("remediation_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.audit_receipt


def test_auditor_rejects_changed_log_even_with_valid_true(tmp_path):
    raw = tmp_path / "results"
    raw.mkdir()
    log = raw / "pytest.log"
    log.write_text("original", encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "valid": True,
                "raw_output": "results",
                "source_sha256": {},
                "raw_sha256": {"pytest.log": hashlib.sha256(log.read_bytes()).hexdigest()},
            }
        )
    )
    audit = load_auditor()
    assert audit(tmp_path, receipt)["valid"]
    log.write_text("changed", encoding="utf-8")
    checked = audit(tmp_path, receipt)
    assert not checked["valid"]
    assert checked["mismatches"][0]["path"] == "pytest.log"


def test_auditor_rejects_path_escape(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"raw_output": "..", "source_sha256": {}, "raw_sha256": {}}))
    with pytest.raises(ValueError, match="escapes"):
        load_auditor()(tmp_path, receipt)
