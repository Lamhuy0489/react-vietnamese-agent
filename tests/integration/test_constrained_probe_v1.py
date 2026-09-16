"""Public synthetic four-task controls; real spawned IPC, no native model loads."""

import json
import shutil
from pathlib import Path

import pytest

from react_agent.llm import guard_observer_probe_v2 as baseline
from react_agent.llm.constrained_probe_v1 import SCHEDULE, checkpoint, fixed_identity, run
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver
from react_agent.validation.constrained_runtime_audit_v1 import audit_task

ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENT = ROOT / "data/clean/v1_1/environment"
COMMIT = "1" * 40


def invoke(root, condition="valid", **kwargs):
    return run(
        root,
        ENVIRONMENT,
        backend="stub",
        commit=COMMIT,
        observer_factory=SyntheticPairObserver,
        condition=condition,
        **kwargs,
    )


@pytest.fixture(scope="module", params=["valid", "backend_failure"])
def source(tmp_path_factory, request):
    root = tmp_path_factory.mktemp("constrained_probe") / request.param
    before = dict(vars(baseline))
    summary = invoke(root, request.param)
    assert all(vars(baseline)[k] is v for k, v in before.items())
    return root, request.param, summary


def test_complete_resume_and_join(source):
    root, condition, summary = source
    assert summary["tasks"] == 4
    assert summary["completed"] == (4 if condition == "valid" else 0)
    assert summary["model_errors"] == (0 if condition == "valid" else 4)
    before = inventory(root)
    assert invoke(root, condition, resume=True) == summary and inventory(root) == before
    for key in SCHEDULE:
        folder = root / "tasks" / key
        assert checkpoint(folder)["recovered"] and audit_task(folder / "execution")["valid"]
        joined = json.loads((folder / "join.json").read_text())
        assert len(joined["completed"]) == (2 if condition == "valid" else 0)
        assert len(joined["incomplete"]) == (0 if condition == "valid" else 1)


def test_missing_only_resume_keeps_errors(source, tmp_path):
    root, condition, summary = source
    target = tmp_path / "partial"
    target.mkdir()
    shutil.copy2(root / "identity.json", target / "identity.json")
    for key in SCHEDULE[:-1]:
        shutil.copytree(root / "tasks" / key, target / "tasks" / key)
    before = inventory(target)
    assert invoke(target, condition, resume=True) == summary
    after = inventory(target)
    assert all(after[n] == sha for n, sha in before.items())


@pytest.mark.parametrize("fault", ["constraint", "source", "decoding", "extra", "partial"])
def test_corruption_stops_before_any_new_work(source, tmp_path, fault):
    root, condition, _ = source
    target = tmp_path / "corrupted"
    shutil.copytree(root, target)
    if fault in {"source", "decoding"}:
        path = target / "identity.json"
        identity = json.loads(path.read_text())
        identity["execution_source_sha256" if fault == "source" else "constrained_execution"] = {}
        path.write_text(json.dumps(identity))
    elif fault == "constraint":
        path = target / "tasks/DOC_A6/constraints/request_000001/entered.json"
        path.write_text("{}")
    elif fault == "partial":
        (target / "tasks/DOC_A6/checkpoint.json").unlink()
    else:
        (target / "tasks/extra").mkdir()
    before = inventory(target)
    with pytest.raises(ValueError):
        invoke(target, condition, resume=True)
    assert inventory(target) == before


def test_native_no_output_injection_and_distinct_identity():
    with pytest.raises(ValueError, match="native injection"):
        fixed_identity("hf", "backend_failure")
    native = fixed_identity("hf", "valid")
    assert not native["synthetic_constraint_receipts"]
    assert native["constrained_execution"]["identity"]
    assert native["protocol"] != baseline.fixed_identity("hf", "valid")["protocol"]
