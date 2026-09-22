"""Candidate validation only: all declared controls, unchanged frozen comparator."""

import socket
from pathlib import Path

import pytest

from react_agent.security_v1.a6_qa import cases
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.runtime_v10 import RUNTIME_VERSION as BASELINE
from react_agent.security_v1.runtime_v11 import RUNTIME_VERSION, SecurityRuntime
from react_agent.validation.acceptance_controls_v1 import run_control

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def reject(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", reject)
    monkeypatch.setattr(socket, "create_connection", reject)


@pytest.mark.parametrize("form", ["supported", "sentence"])
@pytest.mark.parametrize("case", cases(), ids=lambda c: c.name)
def test_candidate_preserves_security_and_restores_bounded_utility(case, form, tmp_path):
    run = bind(
        run_control,
        SecurityRuntime=SecurityRuntime,
        RUNTIME_VERSION=RUNTIME_VERSION if case.level == "A6" else BASELINE,
    )
    result = run(ROOT, tmp_path / "control", case, form=form)
    assert result["valid"] and result["expectation_met"]
