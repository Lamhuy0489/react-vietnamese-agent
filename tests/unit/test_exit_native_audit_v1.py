"""Mocked native boundary composition; no model or GPU execution claims."""

import copy
import json

import pytest
from test_constrained_native_audit_v1 import case as constrained_case  # noqa: F401
from test_constrained_native_audit_v1 import prior_case  # noqa: F401

from react_agent.llm.exit_pair_probe_v1 import execution_sources, fixed_identity
from react_agent.validation import constrained_native_audit_v1 as constrained
from react_agent.validation import exit_native_audit_v1 as candidate


@pytest.fixture
def case(request, monkeypatch):
    args = request.getfixturevalue("constrained_case")
    path = args[0] / "identity.json"
    identity = json.loads(path.read_text())
    identity.update(fixed_identity("hf", "valid"), execution_source_sha256=execution_sources())
    path.write_text(json.dumps(identity))
    monkeypatch.setattr(candidate, "checkpoint", lambda *a, **k: constrained.checkpoint(*a))
    monkeypatch.setattr(candidate, "constraint_join", lambda *a, **k: constrained.audit_join(*a))
    monkeypatch.setattr(candidate, "role_evidence", lambda *a, **k: constrained.role_evidence(*a))
    monkeypatch.setattr(candidate, "audit_exit", lambda *a, **k: dict(valid=True, scope="mock"))
    return args


def test_full_native_composition_leaves_globals_and_marks_scope(case):
    before = dict(vars(constrained))
    result = candidate.audit(*case)
    assert result["protocol"] == "exit_constrained_native_audit_v1"
    assert all(t["exit_milestones"] == dict(valid=True, scope="mock") for t in result["tasks"])
    assert not result["source_authenticated"] and not result["native_cause_identified"]
    assert all(vars(constrained)[k] is value for k, value in before.items())


@pytest.mark.parametrize("fault", ["observer", "config", "source", "missing", "extra"])
def test_native_protocol_drift_rejected(case, fault):
    root = case[0]
    path = root / "identity.json"
    identity = json.loads(path.read_text())
    if fault in {"observer", "config", "source"}:
        name = dict(
            observer="exit_observer", config="pair_config", source="execution_source_sha256"
        )[fault]
        identity[name] = {}
        path.write_text(json.dumps(identity))
    elif fault == "missing":
        (root / "tasks/DOC_A6").rename(root / "retained_DOC_A6")
    else:
        (root / "tasks/extra").mkdir()
    with pytest.raises(ValueError):
        candidate.audit(*case)


def test_failed_exit_join_not_silently_accepted(case, monkeypatch):
    def reject(*args, **kwargs):
        raise ValueError("invalid role binding")

    monkeypatch.setattr(candidate, "audit_exit", reject)
    with pytest.raises(ValueError, match="role binding"):
        candidate.audit(*case)


def test_role_token_join_uses_combined_auditor(tmp_path, monkeypatch):
    native = dict(
        policy_attention_verified=True, calls=[dict(index=1, input_tokens=7, output_tokens=28)]
    )
    combined = dict(
        constrained=dict(
            completed=[dict(request_index=1, input_tokens=7, output_tokens=28)], incomplete=[]
        ),
        exit=dict(valid=True),
    )
    monkeypatch.setattr(constrained.original, "role_evidence", lambda *a: copy.deepcopy(native))
    monkeypatch.setattr(candidate, "audit_join", lambda *a, **k: copy.deepcopy(combined))
    args = (tmp_path, "guard", {}, {}, tmp_path, tmp_path, None, [])
    result = candidate.role_evidence(*args)
    assert result["constrained_native_counts_verified"]
    combined["constrained"]["completed"][0]["output_tokens"] = 999
    with pytest.raises(ValueError):
        candidate.role_evidence(*args)


def test_native_audit_uses_recorded_interpreter_not_host(case, monkeypatch):
    path = case[0] / "identity.json"
    identity = json.loads(path.read_text())
    runtime = identity["exit_observer"]["runtime"]
    runtime.update(system="Linux", version="3.12.10", threads_sha256="a" * 64)
    path.write_text(json.dumps(identity))
    seen = []

    def observe(*args, expected_runtime):
        seen.append(expected_runtime)
        return dict(valid=True, scope="mock")

    monkeypatch.setattr(candidate, "audit_exit", observe)
    assert candidate.audit(*case)["complete"]
    assert seen == [runtime] * 4
