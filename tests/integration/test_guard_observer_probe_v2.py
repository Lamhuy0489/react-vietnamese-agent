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
