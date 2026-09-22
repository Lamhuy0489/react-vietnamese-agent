"""Exit summary joins; no model execution or remote authentication is mocked as proof."""

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def case(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "exit_report", ROOT / "scripts/report_phase5_exit_gpu_v1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    roles = dict(
        agent=dict(pid=10, method="TERMINATE", boundary="observed_stages_returned"),
        guard=dict(pid=11, method="GRACEFUL", boundary="observed_stages_returned"),
    )
    value = dict(
        protocol="exit_pair_gpu_release_audit_v1",
        raw_sha256={},
        native=dict(
            protocol="exit_constrained_native_audit_v1",
            tasks=[
                dict(
                    key="CALC_A2",
                    exit_milestones=dict(protocol="exit_pair_join_v1", valid=True, roles=roles),
                )
            ],
        ),
    )

    def baseline(adapted, raw):
        assert adapted["protocol"] == "constrained_gpu_release_audit_v1"
        assert adapted["native"]["protocol"] == "constrained_native_audit_v1"
        assert raw == tmp_path
        return dict(
            workers=[
                dict(task="CALC_A2", role=r, pid=v["pid"], method=v["method"])
                for r, v in roles.items()
            ],
            limitations=[],
        )

    monkeypatch.setattr(module, "constrained_summary", baseline)
    return module, value, tmp_path


def test_counts_without_claiming_graceful_or_cause(case):
    module, value, raw = case
    original = copy.deepcopy(value)
    result = module.summarize(value, raw)
    assert value == original
    assert result["exit_boundary_counts"] == {"observed_stages_returned": 2}
    assert result["forced_exit_boundary_counts"] == {"observed_stages_returned": 1}
    assert not result["native_cause_identified"] and not result["phase5_accepted"]


@pytest.mark.parametrize("level", ["release", "native", "join", "accepted", "roles"])
def test_invalid_join_rejected(case, level):
    module, value, raw = case
    join = value["native"]["tasks"][0]["exit_milestones"]
    if level == "release":
        value["protocol"] = "wrong"
    elif level == "native":
        value["native"]["protocol"] = "wrong"
    elif level == "join":
        join["protocol"] = "wrong"
    elif level == "accepted":
        join["valid"] = False
    else:
        join["roles"]["extra"] = dict(join["roles"]["agent"])
    with pytest.raises(ValueError):
        module.summarize(value, raw)


def test_raw_mutation_rejected(case):
    module, value, raw = case
    (raw / "extra").write_text("changed")
    with pytest.raises(ValueError, match="raw unchanged"):
        module.summarize(value, raw)


def test_native_validation_not_bypassed(case, monkeypatch):
    module, value, raw = case

    def reject(*args):
        raise ValueError("native validation failed")

    monkeypatch.setattr(module, "constrained_summary", reject)
    with pytest.raises(ValueError, match="native validation failed"):
        module.summarize(value, raw)


@pytest.mark.parametrize("field,value", [("pid", 99), ("method", "KILL")])
def test_lifecycle_mismatch_rejected(case, monkeypatch, field, value):
    module, verified, raw = case
    original = module.constrained_summary

    def mismatched(*args):
        result = original(*args)
        result["workers"][0][field] = value
        return result

    monkeypatch.setattr(module, "constrained_summary", mismatched)
    with pytest.raises(ValueError, match="exit/lifecycle"):
        module.summarize(verified, raw)
