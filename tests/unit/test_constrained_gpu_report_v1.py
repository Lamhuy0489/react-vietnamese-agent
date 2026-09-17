"""Adapter tests; frozen observer summarizer has separate integration/negative tests."""

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "constrained_report", ROOT / "scripts/report_phase5_constrained_gpu_v1.py"
    )
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def fixture():
    return dict(
        protocol="constrained_gpu_release_audit_v1",
        native=dict(
            protocol="constrained_native_audit_v1",
            tasks=[
                dict(
                    guard_diagnostics=dict(
                        protocol="constrained_runtime_join_v1",
                        completed=[{}],
                        incomplete=[{}],
                        observer=dict(joined=[dict(fixture=True)]),
                    )
                )
            ],
        ),
    )


def test_adapter_preserves_original_and_delegates(module, monkeypatch, tmp_path):
    value = fixture()
    before = copy.deepcopy(value)

    def descriptive(adapted, raw):
        assert raw == tmp_path
        assert adapted["native"]["tasks"][0]["guard_diagnostics"] == {"joined": [{"fixture": True}]}
        return dict(limitations=[], phase5_accepted=False, guard_quality_validated=False)

    monkeypatch.setattr(module, "observer_summary", descriptive)
    result = module.summarize(value, tmp_path)
    assert value == before
    assert result["protocol"] == "constrained_native_descriptive_report_v1"
    assert result["constraint_completed_requests"] == result["constraint_incomplete_requests"] == 1
    assert not result["phase5_accepted"] and not result["guard_quality_validated"]


@pytest.mark.parametrize("level", ["release", "native", "join"])
def test_wrong_protocol_rejected_before_summary(module, monkeypatch, tmp_path, level):
    value = fixture()
    target = value if level == "release" else value["native"]
    if level == "join":
        target = target["tasks"][0]["guard_diagnostics"]
    target["protocol"] = "wrong"
    monkeypatch.setattr(module, "observer_summary", lambda *a: pytest.fail("must reject first"))
    with pytest.raises(ValueError):
        module.summarize(value, tmp_path)


def test_summary_does_not_bypass_legacy_validation(module, monkeypatch, tmp_path):
    def reject(*args):
        raise ValueError("raw hash mismatch")

    monkeypatch.setattr(module, "observer_summary", reject)
    with pytest.raises(ValueError, match="raw hash mismatch"):
        module.summarize(fixture(), tmp_path)
