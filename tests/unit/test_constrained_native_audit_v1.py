"""Explicitly mocked native boundaries; never claims native execution or weight admission."""

import copy
import json
from pathlib import Path

import pytest
from test_observer_native_audit_v2 import full_case as prior_case  # noqa: F401

from react_agent.llm.constrained_probe_v1 import execution_sources, fixed_identity, native_pair
from react_agent.validation import constrained_native_audit_v1 as candidate
from react_agent.validation import observer_native_audit_v2 as baseline


@pytest.fixture
def role_case(tmp_path, monkeypatch):
    native = dict(
        policy_attention_verified=True,
        calls=[
            dict(
                index=1,
                input_tokens=7,
                output_tokens=28,
                generate_seconds=0.5,
                tokens_per_generate_second=56,
            )
        ],
        failed_or_partial=False,
        load_verified=True,
        worker_attempts=1,
    )
    constraints = dict(
        completed=[dict(request_index=1, input_tokens=7, output_tokens=28)], incomplete=[]
    )
    monkeypatch.setattr(baseline, "role_evidence", lambda *args: copy.deepcopy(native))
    monkeypatch.setattr(candidate, "audit_join", lambda *args: copy.deepcopy(constraints))
    args = (tmp_path, "guard", {}, {}, tmp_path / "tokenizers", tmp_path / "publishers", None, [])
    return args, native, constraints


def test_cross_layer_counts_and_timing_scope(role_case):
    args, native, _ = role_case
    result = candidate.role_evidence(*args)
    assert result["constrained_native_counts_verified"]
    assert result["calls"] == native["calls"]
    assert result["constraint_calls"] == [dict(request_index=1, input_tokens=7, output_tokens=28)]


@pytest.mark.parametrize(
    "fault", ["index", "input", "output", "bool", "missing", "extra", "partial"]
)
def test_native_constraint_mismatch_rejected(role_case, fault):
    args, _, constraint = role_case
    if fault == "missing":
        constraint["completed"].clear()
    elif fault == "extra":
        constraint["completed"].append(constraint["completed"][0])
    elif fault == "partial":
        constraint["incomplete"].append({})
    else:
        key = dict(
            index="request_index",
            input="input_tokens",
            output="output_tokens",
            bool="output_tokens",
        )[fault]
        constraint["completed"][0][key] = True if fault == "bool" else 999
    with pytest.raises(ValueError):
        candidate.role_evidence(*args)


def test_failed_role_excluded_from_timing_and_agent_unchanged(role_case):
    args, native, constraint = role_case
    native.update(policy_attention_verified=False, calls=[], failed_or_partial=True)
    constraint["incomplete"] = [dict(request_index=2)]
    result = candidate.role_evidence(*args)
    assert not result["constrained_native_counts_verified"] and not result["calls"]
    assert not result["constraint_calls"] and result["incomplete_constraint_requests"] == 1
    agent_args = (args[0], "agent", *args[2:])
    assert candidate.role_evidence(*agent_args) == native


def test_partial_role_must_not_report_throughput(role_case):
    args, native, _ = role_case
    native["policy_attention_verified"] = False
    with pytest.raises(ValueError, match="denominators"):
        candidate.role_evidence(*args)


@pytest.fixture
def case(request, monkeypatch):
    args = request.getfixturevalue("prior_case")
    path = args[0] / "identity.json"
    identity = json.loads(path.read_text())
    identity.update(fixed_identity("hf", "valid"), execution_source_sha256=execution_sources())
    path.write_text(json.dumps(identity))
    monkeypatch.setattr(candidate, "checkpoint", baseline.checkpoint)
    monkeypatch.setattr(candidate, "audit_join", baseline.audit_guard)
    monkeypatch.setattr(candidate, "role_evidence", baseline.role_evidence)
    return args


def test_full_native_wrapper_keeps_baseline_globals(case):
    before = dict(vars(baseline))
    result = candidate.audit(*case)
    assert result["protocol"] == "constrained_native_audit_v1" and result["complete"]
    assert len(result["tasks"]) == 4 and not result["source_authenticated"]
    assert all(vars(baseline)[key] is value for key, value in before.items())


@pytest.mark.parametrize("fault", ["decoding", "synthetic", "source", "missing", "extra"])
def test_native_wrapper_rejects_identity_or_schedule_drift(case, fault):
    probe = case[0]
    path = probe / "identity.json"
    identity = json.loads(path.read_text())
    if fault in {"decoding", "synthetic", "source"}:
        key = dict(
            decoding="constrained_execution",
            synthetic="synthetic_constraint_receipts",
            source="execution_source_sha256",
        )[fault]
        identity[key] = True if fault == "synthetic" else {}
        path.write_text(json.dumps(identity))
    elif fault == "missing":
        (probe / "tasks/DOC_A6").rename(probe / "retained_DOC_A6")
    else:
        (probe / "tasks/extra").mkdir()
    with pytest.raises(ValueError):
        candidate.audit(*case)


def test_native_route_names_constraint_root_without_loading(monkeypatch, tmp_path):
    from react_agent.llm import constrained_probe_v1 as runner

    captured = {}

    def factory(*args, **kwargs):
        captured.update(kwargs)
        return "lazy-pair"

    monkeypatch.setattr(runner, "constrained_pair", factory)
    assert native_pair(Path("agent"), witness=tmp_path / "witness.jsonl") == "lazy-pair"
    assert captured["constrained"] == tmp_path / "constraints"
