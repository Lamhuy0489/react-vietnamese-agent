"""Synthetic boundary mutations around the candidate native auditor."""

import json

import pytest
from test_observer_native_audit_v2 import full_case as prior_case  # noqa: F401

from react_agent.llm.guard_bare_json_probe_v1 import execution_sources, fixed_identity
from react_agent.validation import guard_bare_json_native_audit_v1 as candidate
from react_agent.validation import observer_native_audit_v2 as baseline


@pytest.fixture
def case(request, monkeypatch):
    args = request.getfixturevalue("prior_case")
    path = args[0] / "identity.json"
    identity = json.loads(path.read_text())
    identity.update(fixed_identity("hf", "valid"), execution_source_sha256=execution_sources())
    path.write_text(json.dumps(identity))
    monkeypatch.setattr(candidate, "checkpoint", baseline.checkpoint)
    monkeypatch.setattr(candidate, "audit_join", baseline.audit_guard)
    return args


def test_native_reuses_complete_audit_and_preserves_globals(case):
    before = dict(baseline.__dict__)
    result = candidate.audit(*case)
    assert result["complete"] and result["protocol"] == "guard_bare_json_native_audit_v1"
    assert len(result["tasks"]) == 4 and not result["source_authenticated"]
    assert all(baseline.__dict__[k] is v for k, v in before.items())


@pytest.mark.parametrize("fault", ["prompt", "backend", "snapshot", "missing", "extra"])
def test_native_identity_and_coverage_mutations(case, fault):
    probe = case[0]
    path = probe / "identity.json"
    identity = json.loads(path.read_text())
    if fault == "prompt":
        identity["guard_prompt"]["sha256"] = "0" * 64
    elif fault == "backend":
        identity["backend"] = "stub"
    elif fault == "snapshot":
        identity["snapshot_sha256"] = "0" * 64
    elif fault == "missing":
        (probe / "tasks/DOC_A6").rename(probe / "retained_DOC_A6")
    else:
        (probe / "tasks/extra").mkdir()
    path.write_text(json.dumps(identity))
    with pytest.raises(ValueError):
        candidate.audit(*case)
