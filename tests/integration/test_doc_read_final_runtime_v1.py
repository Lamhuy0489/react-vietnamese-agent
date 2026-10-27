"""Paired CPU controls and externally pinned replay audit, with real doc_read."""

import json
import shutil
from pathlib import Path

import pytest

from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.security_v1.doc_read_final_runtime_v1 import run_synthetic_pair_task
from react_agent.validation.doc_read_final_controls_v1 import (
    BENIGN,
    CASES,
    TOKEN,
    approval,
    run_control,
    specimen,
)
from react_agent.validation.doc_read_final_runtime_audit_v1 import audit_runtime

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module", params=CASES)
def control(request, tmp_path_factory):
    output = tmp_path_factory.mktemp("doc_read_final") / request.param
    return output, run_control(ROOT, output, request.param)


def test_paired_matrix_preserves_dispatch_and_meets_predeclared_gate(control):
    _, receipt = control
    assert receipt["expectation_met"], receipt["checks"]
    case = receipt["case"]
    if case in BENIGN:
        assert receipt["arms"]["candidate"]["final_answer"] == TOKEN
        assert receipt["arms"]["candidate"]["proof_status"] == "issued_doc_read_content"
        assert receipt["arms"]["baseline"]["desired_pass"] == (case == "no_collision")


def test_repeated_audit_uses_external_pin_and_is_read_only(control):
    output, receipt = control
    runtime = output / "candidate/execution/runtime"
    result = audit_runtime(
        runtime, approval=approval(), expected_approval_sha256=approval().identity
    )
    assert result == receipt["arms"]["candidate"]["audit"]
    with pytest.raises(ValueError, match="hash mismatch"):
        audit_runtime(runtime, approval=approval(), expected_approval_sha256="0" * 64)


@pytest.mark.parametrize("fault", ["pin", "catalog", "level"])
def test_bad_admission_stops_before_worker_and_output(tmp_path, fault):
    approved = approval()  # before content
    task, kwargs = specimen(ROOT, tmp_path / "input", "s2_collision")
    expected = approved.identity
    if fault == "pin":
        expected = "0" * 64
    elif fault == "catalog":
        kwargs["source_catalog"] = SourceCatalog()
    else:
        kwargs["security"] = kwargs["security"].model_copy(update={"level": "A5"})
    with pytest.raises(ValueError):
        run_synthetic_pair_task(
            task, approval=approved, expected_approval_sha256=expected, **kwargs
        )
    assert kwargs["pair"].state == "NEW"
    assert not kwargs["output"].exists()


@pytest.mark.parametrize("terminal", ["max_steps", "parse_failure", "model_error"])
def test_nonfinal_terminal_never_releases_answer(tmp_path, terminal):
    approved = approval()
    responses = None if terminal == "max_steps" else () if terminal == "model_error" else ("bad",)
    task, kwargs = specimen(ROOT, tmp_path / "input", "s2_collision", responses=responses)
    kwargs["runtime_config"] = kwargs["runtime_config"].model_copy(update={
        "max_steps": 1, "max_format_retries_per_step": 0,
    })
    result = run_synthetic_pair_task(
        task, approval=approved, expected_approval_sha256=approved.identity, **kwargs,
    )
    assert result.result.status == terminal
    assert result.result.final_answer is None
    audited = audit_runtime(kwargs["output"] / "runtime", approval=approved,
                            expected_approval_sha256=approved.identity)
    assert audited["final_count"] == 0


@pytest.fixture(scope="module")
def successful_runtime(tmp_path_factory):
    output = tmp_path_factory.mktemp("doc_read_audit") / "clean"
    run_control(ROOT, output, "s2_collision")
    return output / "candidate/execution/runtime"


@pytest.mark.parametrize("fault", ["approval", "path", "source_hash", "call", "answer", "scope"])
def test_corrupted_public_proof_audit_rejected(successful_runtime, tmp_path, fault):
    output = tmp_path / "corrupt"
    shutil.copytree(successful_runtime, output)
    path = output / "final_literal_gate.json"
    value = json.loads(path.read_text())
    if fault == "approval":
        value["public_final_approval"]["review_ref"] = "other-review"
    elif fault == "path":
        value["records"][0]["proof"]["field_path"] = "/title"
    elif fault == "source_hash":
        value["records"][0]["proof"]["source_sha256"] = "0" * 64
    elif fault == "call":
        value["records"][0]["proof"]["source_call_id"] = "another_call"
    elif fault == "scope":
        value["public_field_runtime_enabled"] = False
    else:
        path = output / "run_metadata.json"
        value = json.loads(path.read_text())
        value["result"]["final_answer"] = "tampered"
    path.write_text(json.dumps(value))
    before = {str(p): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    with pytest.raises(ValueError):
        audit_runtime(output, approval=approval(), expected_approval_sha256=approval().identity)
    assert {str(p): p.read_bytes() for p in output.rglob("*") if p.is_file()} == before
