"""Adapter boundary tests use explicit native-shaped mocks, never model proof."""

from copy import deepcopy

import pytest

from react_agent.security_v1.exit_milestones_v1 import runtime_identity
from react_agent.validation import clause_dev_native_audit_v1 as auditor


def fixture():
    return dict(
        guard_diagnostics=dict(
            constrained=dict(
                incomplete=[],
                completed=[
                    dict(
                        request_index=1,
                        input_tokens=10,
                        output_tokens=28,
                    )
                ],
            )
        ),
        roles=dict(
            guard=dict(
                policy_attention_verified=True,
                calls=[
                    dict(
                        index=1,
                        input_tokens=10,
                        output_tokens=28,
                    )
                ],
            )
        ),
    )


@pytest.mark.parametrize(
    "fault", [None, "count", "index", "input", "output", "incomplete", "unverified"]
)
def test_constraint_token_binding_and_partial_denominators(tmp_path, monkeypatch, fault):
    value = fixture()
    if fault == "count":
        value["guard_diagnostics"]["constrained"]["completed"] = []
    elif fault == "incomplete":
        value["guard_diagnostics"]["constrained"]["incomplete"] = [dict(request_index=2)]
    elif fault == "unverified":
        value["roles"]["guard"]["policy_attention_verified"] = False
    elif fault:
        field = {"index": "request_index", "input": "input_tokens", "output": "output_tokens"}[
            fault
        ]
        value["guard_diagnostics"]["constrained"]["completed"][0][field] += 1

    def native(*args, **kwargs):
        return deepcopy(value)

    monkeypatch.setattr(auditor.baseline, "audit_native_task", native)
    args = (
        tmp_path,
        dict(protocol="clause_dev32_v1", exit_observer=dict(runtime=runtime_identity())),
        dict(level="A6"),
        tmp_path,
        tmp_path,
        None,
    )
    if fault:
        with pytest.raises(ValueError):
            auditor.audit_native_task(*args)
    else:
        assert auditor.audit_native_task(*args)["constrained_counts_verified"]


def test_stub_cannot_be_native_audited(tmp_path):
    with pytest.raises(ValueError):
        auditor.audit(
            tmp_path, dict(protocol="clause_dev32_v1", backend="stub"), 0, tmp_path, tmp_path, None
        )


def test_native_builder_is_lazy_and_rejects_synthetic_dispatch(tmp_path):
    from pathlib import Path

    from react_agent.llm.clause_dev_runner_v1 import native_pair
    from react_agent.llm.exit_pair_v1 import ExitPair
    from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
    from react_agent.security_v1.exit_pair_runtime_v1 import native_root

    root = Path(__file__).resolve().parents[2]
    pin = GuardSnapshot.model_validate_json(
        (root / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    pair = native_pair(
        tmp_path / "agent",
        tmp_path / "inventory",
        tmp_path / "guard",
        pin,
        tmp_path / "native",
        tmp_path / "attention",
        tmp_path / "policy",
    )
    try:
        assert type(pair) is ExitPair and pair.state == "NEW"
        assert native_root(pair) == tmp_path / "constraints"
        assert not list(tmp_path.iterdir())
        assert all(not worker.attempts for worker in pair._workers.values())
    finally:
        pair.close()
