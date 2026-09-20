"""Fresh CPU spawned workers; inject teardown mechanisms without changing production code."""

import json
import multiprocessing as mp

import pytest

from react_agent.llm import teardown_probe_v1
from react_agent.llm.teardown_probe_v1 import MODES, run, run_case
from react_agent.validation.teardown_probe_audit_v1 import METHOD, audit_case


@pytest.mark.parametrize("mode", MODES)
def test_real_cpu_control(mode):
    record = run_case(mode)
    result = audit_case(record, mode)
    assert result["method"] == METHOD[mode]
    assert result["pid"] not in {p.pid for p in mp.active_children()}
    assert not record["generation_error"]


def test_unknown_control_rejected_before_spawn():
    with pytest.raises(ValueError, match="fixed"):
        run_case("native")


def test_existing_output_never_overwritten(tmp_path):
    (tmp_path / "sentinel").write_text("retained")
    with pytest.raises(ValueError, match="fresh"):
        run(tmp_path, "a" * 40)
    assert (tmp_path / "sentinel").read_text() == "retained"


def test_invalid_base_rejected_before_create(tmp_path):
    out = tmp_path / "not-created"
    with pytest.raises(ValueError):
        run(out, "not-a-commit")
    assert not out.exists()


def test_orchestrator_creates_case_directory_before_first_worker(tmp_path, monkeypatch):
    out = tmp_path / "controls"
    calls = []

    def record(mode):
        assert (out / "cases").is_dir()
        calls.append(mode)
        return dict(mode=mode, lifecycle=[dict(method="synthetic routing only")])

    monkeypatch.setattr(teardown_probe_v1, "run_case", record)
    run(out, "a" * 40)
    assert calls == list(MODES) * 3
    assert len(list((out / "cases").glob("*.json"))) == 18
    assert json.loads((out / "identity.json").read_text())["actual_model_loads"] == 0
