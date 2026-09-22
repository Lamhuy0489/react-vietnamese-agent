"""Current-runtime smoke decisions, not inference or benchmark quality."""

import socket
from pathlib import Path

import pytest

from react_agent.security_v1.a6_qa import Case, cases
from react_agent.validation.acceptance_controls_v1 import run_control

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def reject(*args, **kwargs):
        raise AssertionError("mock sinks must never use network")

    monkeypatch.setattr(socket, "socket", reject)
    monkeypatch.setattr(socket, "create_connection", reject)


@pytest.mark.parametrize("case", cases(), ids=lambda c: c.name)
def test_current_runtime_control(case, tmp_path):
    result = run_control(ROOT, tmp_path / "control", case)
    assert result["valid"] and result["expectation_met"]


@pytest.mark.parametrize("case", cases(), ids=lambda c: c.name)
def test_sentence_form_preserves_known_authorization_gap(case, tmp_path):
    result = run_control(ROOT, tmp_path / "control", case, form="sentence")
    gap = case.level == "A6" and case.denied == 0
    assert result["valid"]
    assert result["expectation_met"] is not gap
    if gap:
        assert result["denied"] == 1
        assert not result["checks"]["tool_dispatch"]


def test_unknown_case_rejected_before_output(tmp_path):
    with pytest.raises(ValueError, match="predeclared"):
        run_control(ROOT, tmp_path / "control", Case("undeclared"))
    assert not (tmp_path / "control").exists()


def test_existing_output_preserved(tmp_path):
    with pytest.raises(ValueError, match="fresh"):
        run_control(ROOT, tmp_path, cases()[0])
