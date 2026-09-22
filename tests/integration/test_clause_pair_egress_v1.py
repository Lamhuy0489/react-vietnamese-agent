"""Real sibling-process compound authorization/value-origin controls."""

from pathlib import Path

import pytest

from react_agent.validation.clause_pair_controls_v1 import CASES, run_control

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", CASES)
def test_paired_sensitive_unknown_and_a5_vetoes(name, tmp_path):
    value = run_control(ROOT, tmp_path / "control", name)
    assert value["expectation_met"]
    assert all(r["boundary"] != "not_started" for r in value["join"]["exit"]["roles"].values())


def test_unknown_control_rejected_before_output(tmp_path):
    with pytest.raises(ValueError):
        run_control(ROOT, tmp_path / "control", "other")
    assert not list(tmp_path.iterdir())
