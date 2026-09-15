"""Checkpoint/resume integrity with real CPU processes and no benchmark oracle."""

import json
import shutil
from pathlib import Path

import pytest

from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.guard_observer_probe_v2 import SCHEDULE, checkpoint, fixed_identity, run
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver

ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENT = ROOT / "data/clean/v1_1/environment"
COMMIT = "1" * 40


def invoke(output, condition="valid", **kwargs):
    return run(
        output,
        ENVIRONMENT,
        backend="stub",
        commit=COMMIT,
        observer_factory=SyntheticPairObserver,
        condition=condition,
        **kwargs,
    )


@pytest.fixture(scope="module", params=["valid", "trailing_comma"])
def source(tmp_path_factory, request):
    root = tmp_path_factory.mktemp("observer_probe") / request.param
    summary = invoke(root, request.param)
    return root, request.param, summary


def test_expected_coverage_and_completed_resume(source):
    root, condition, summary = source
    assert summary["tasks"] == 4
    assert summary["completed"] == (4 if condition == "valid" else 0)
    assert summary["model_errors"] == (0 if condition == "valid" else 4)
    before = inventory(root)
    assert invoke(root, condition, resume=True) == summary
    assert inventory(root) == before
    for key in SCHEDULE:
        folder = root / "tasks" / key
        assert checkpoint(folder)["recovered"]
        join = json.loads((folder / "join.json").read_text())
        assert join["response_records"] == (2 if condition == "valid" else 1)
        assert [r["stage"] for r in join["joined"]] == (
            ["PRE", "POST"] if condition == "valid" else ["PRE"]
        )
        receipt = json.loads((folder / "execution/pair_runtime.json").read_text())
        for role in ("agent", "guard"):
            worker = receipt["snapshot"]["workers"][role]
            assert len(worker["attempts"]) == (3 if condition == "valid" else 2)
            assert worker["closed"] and not worker["handle_pending"]
            assert all(e["reaped"] for e in worker["lifecycle"])


def test_missing_only_resume(source, tmp_path):
    root, condition, summary = source
    partial = tmp_path / "partial"
    partial.mkdir()
    shutil.copy2(root / "identity.json", partial / "identity.json")
    for key in SCHEDULE[:-1]:
        shutil.copytree(root / "tasks" / key, partial / "tasks" / key)
    before = inventory(partial)
    assert invoke(partial, condition, resume=True) == summary
    assert all(inventory(partial)[name] == value for name, value in before.items())


@pytest.mark.parametrize(
    "mutation", ["partial", "extra", "identity", "raw", "witness", "checkpoint"]
)
def test_bad_resume_retains_evidence(source, tmp_path, mutation):
    root, condition, _ = source
    target = tmp_path / "copy"
    shutil.copytree(root, target)
    folder = target / "tasks" / SCHEDULE[0]
    if mutation == "partial":
        (folder / "checkpoint.json").unlink()
    elif mutation == "extra":
        (target / "tasks" / "extra").mkdir()
    elif mutation == "identity":
        p = target / "identity.json"
        d = json.loads(p.read_text())
        d["source_commit"] = "2" * 40
        p.write_text(json.dumps(d))
    elif mutation == "raw":
        (folder / "join.json").write_text("{}")
    elif mutation == "witness":
        (folder / "witness.jsonl").unlink()
    else:
        p = folder / "checkpoint.json"
        d = json.loads(p.read_text())
        d["terminal"] = "completed" if condition != "valid" else "model_error"
        p.write_text(json.dumps(d))
    before = inventory(target)
    with pytest.raises(ValueError):
        invoke(target, condition, resume=True)
    assert inventory(target) == before


def test_native_injection_rejected():
    with pytest.raises(ValueError, match="injection"):
        fixed_identity("hf", "trailing_comma")


def test_hf_branch_validates_fresh_roots_before_start(tmp_path, monkeypatch):
    """Execute actual HF factory/path validation; stop at runtime before model load."""
    import react_agent.llm.guard_observer_probe_v2 as module
    from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
    from react_agent.llm.guard_snapshot_v1 import GuardSnapshot

    pin = GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    model_inventory = tmp_path / "inventory.json"
    model_inventory.write_text("{}")
    visited = []

    class StopBeforeWeights(Exception):
        pass

    def stop(task, **kwargs):
        pair = kwargs["pair"]
        assert isinstance(pair, DiagnosticPair)
        assert (tmp_path / "hf/tasks/CALC_A2/native").is_dir()
        assert all(not w.attempts for w in pair._workers.values())
        visited.append(task.task_id)
        raise StopBeforeWeights

    monkeypatch.setattr(module, "run_pair_task", stop)
    with pytest.raises(StopBeforeWeights):
        run(
            tmp_path / "hf",
            ENVIRONMENT,
            backend="hf",
            commit=COMMIT,
            observer_factory=SyntheticPairObserver,
            agent=tmp_path / "agent",
            model_inventory=model_inventory,
            guard=tmp_path / "guard",
            snapshot=pin,
        )
    assert visited == ["awb_observer_calc_a2"]
    assert (tmp_path / "hf/tasks/CALC_A2/recovery.json").is_file()


def test_audit_does_not_depend_on_current_git_head(source, monkeypatch):
    import subprocess
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from audit_phase5_guard_observer_probe_v2 import audit_probe
    finally:
        sys.path.pop(0)

    def forbidden(*args, **kwargs):
        raise AssertionError("historical audit must not query current Git HEAD")

    monkeypatch.setattr(subprocess, "check_output", forbidden)
    root, condition, _ = source
    report = audit_probe(root, condition, COMMIT)
    assert report["tasks"] == 4 and report["execution_source_pins_verified"]
    with pytest.raises(ValueError, match="source commit mismatch"):
        audit_probe(root, condition, "2" * 40)


def test_resume_checks_later_partial_before_any_new_task(source, tmp_path, monkeypatch):
    import react_agent.llm.guard_observer_probe_v2 as module

    root, condition, _ = source
    partial = tmp_path / "later_partial"
    (partial / "tasks" / SCHEDULE[-1]).mkdir(parents=True)
    shutil.copy2(root / "identity.json", partial / "identity.json")

    def forbidden(*args, **kwargs):
        raise AssertionError("must reject before any new process")

    monkeypatch.setattr(module, "DiagnosticPair", forbidden)
    before = inventory(partial)
    with pytest.raises(ValueError, match="partial attempt"):
        invoke(partial, condition, resume=True)
    assert inventory(partial) == before


def test_unrecovered_stops_before_second_pair(tmp_path):
    class Unrecovered(SyntheticPairObserver):
        def sample(self, phase):
            rows = super().sample(phase)
            if phase == "recovery":
                rows[0]["free_bytes"] = 0
            return rows

    root = tmp_path / "failed"
    with pytest.raises(ValueError, match="unrecovered"):
        run(root, ENVIRONMENT, backend="stub", commit=COMMIT, observer_factory=Unrecovered)
    assert sorted(p.name for p in (root / "tasks").iterdir()) == [SCHEDULE[0]]
    assert not checkpoint(root / "tasks" / SCHEDULE[0])["recovered"]
    before = inventory(root)
    with pytest.raises(ValueError, match="unrecovered"):
        invoke(root, resume=True)
    assert inventory(root) == before
