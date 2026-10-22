"""Negative controls for integrity and the bounded acceptance claim."""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def audit(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("evaluate_phase5_acceptance_v1")


@pytest.fixture
def controls(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("evaluate_phase5_native_closure_controls_v1")


def test_even_full_control_success_does_not_accept_all_twenty_dod(tmp_path, monkeypatch, audit):
    manifest = {
        "schedule": [{"key": f"{case}__{level}", "case": case, "level": level}
                     for case in audit.CASES for level in audit.LEVELS],
        "agent_backend": "native_qwen_api", "guard_backend": "native_llama_api",
        "test_payloads_loaded": 0, "private_ground_truth_loaded": 0,
        "closure_runtime_family": audit.RUNTIME_FAMILY,
        "closure_runtime_version": audit.RUNTIME_VERSION,
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(audit, "_hashes", lambda *args: 1)
    monkeypatch.setattr(audit, "_row", lambda root, condition, failures: (
        {"condition": condition, "status": "completed", "guard_risks": ["SAFE"],
         "remote_delivery_uncertain": False}, 1))
    monkeypatch.setattr(audit, "evaluate_controls", lambda root: {"control_matrix_passed": True})
    result = audit.evaluate(tmp_path)
    assert result["native_control_checks_passed"]
    assert result["phase5_accepted"] is False
    assert all(row["status"] == "open" for row in result["dod"].values())
    assert result["guard_confusion_matrix"] is None
    assert result["guard_risk_counts"] == {"SAFE": 84}


@pytest.mark.parametrize("name", ["../outside", "/outside"])
def test_artifact_paths_cannot_escape_run(tmp_path, name, controls):
    with pytest.raises(ValueError, match="unsafe artifact"):
        controls._hashes(tmp_path, {name: "f" * 64})


def test_symlink_parent_rejected_before_read(tmp_path, controls):
    outside = tmp_path / "outside"
    outside.mkdir()
    run = tmp_path / "run"
    run.mkdir()
    (run / "execution").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinked"):
        controls._hashes(run, {"execution/metadata.json": "f" * 64})


def test_empty_inventory_is_not_verified(tmp_path, controls):
    with pytest.raises(ValueError, match="inventory"):
        controls._hashes(tmp_path, {})


def event(kind, **data):
    return {"event": kind, "data_json": json.dumps(data)}


def test_post_allow_cannot_hide_pre_deny(controls):
    trace = [event("decision", proposal_id="p1", stage="PRE", effect="DENY"),
             event("decision", proposal_id="p1", stage="POST", effect="ALLOW")]
    decisions = controls._decision_map(trace)
    passed, _ = controls._check_external(
        "c2_email_public", "A6", ({"proposal_id": "p1"},), decisions,
        ({"proposal_id": "p1", "tool": "send_email_mock"},),
    )
    assert not passed


@pytest.mark.parametrize("mutation", ["broker_first", "missing_post", "duplicate_pre"])
def test_ordered_lifecycle_rejects_invalid_execution(audit, mutation):
    trace = [event("proposal", proposal_id="p1"),
             event("decision", proposal_id="p1", stage="PRE", effect="ALLOW"),
             event("broker_result", proposal_id="p1", call_id="c1"),
             event("decision", proposal_id="p1", stage="POST", effect="ALLOW"),
             event("decision", stage="FINAL", effect="ALLOW"), event("released_final")]
    if mutation == "broker_first":
        trace[1], trace[2] = trace[2], trace[1]
    elif mutation == "missing_post":
        trace.pop(3)
    else:
        trace.insert(2, trace[1].copy())
    for index, row in enumerate(trace, 1):
        row.update(sequence=index, run_id="r1", task_id="t1")
    with pytest.raises(ValueError):
        audit._trace_order(trace, {"run_id": "r1", "task_id": "t1"})


def test_legacy_native_resume_cannot_rewrite_manifest(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_phase5_native_closure_v1")
    original = b'{"source_sha256":{"wrapper":"unchanged"}}\n'
    (tmp_path / "manifest.json").write_bytes(original)
    monkeypatch.setattr("sys.argv", ["closure", "--directory", str(tmp_path),
                                    "--output", str(tmp_path), "--resume"])
    with pytest.raises(SystemExit, match="retired"):
        runner.main()
    assert (tmp_path / "manifest.json").read_bytes() == original
