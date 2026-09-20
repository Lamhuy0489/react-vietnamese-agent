"""Real spawned sibling controls and task receipts; no local native inference."""

import json
import shutil
from pathlib import Path

import pytest

from react_agent.llm import constrained_probe_v1 as previous
from react_agent.llm import guard_observer_probe_v2 as baseline
from react_agent.llm.document_runtime_probe_v1 import GENERATION, RUNTIME, inventory
from react_agent.llm.exit_pair_probe_v1 import SCHEDULE, checkpoint, config, run, synthetic_pair
from react_agent.llm.exit_pair_v1 import ExitPair
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticFactory
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.exit_pair_runtime_v1 import run_synthetic_pair_task
from react_agent.tools.factory import build_clean_registry
from react_agent.validation.exit_pair_audit_v1 import audit_exit

ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENT = ROOT / "data/clean/v1_1/environment"


def invoke(root, condition="valid", **kwargs):
    return run(
        root,
        ENVIRONMENT,
        backend="stub",
        commit="1" * 40,
        observer_factory=SyntheticPairObserver,
        condition=condition,
        **kwargs,
    )


@pytest.fixture(scope="module", params=["valid", "backend_failure"])
def source(tmp_path_factory, request):
    root = tmp_path_factory.mktemp("exit_pair") / request.param
    before = {module: dict(vars(module)) for module in (baseline, previous)}
    summary = invoke(root, request.param)
    assert all(all(vars(m)[k] is v for k, v in values.items()) for m, values in before.items())
    return root, request.param, summary


def test_completed_failures_and_resume_are_preserved(source):
    root, condition, summary = source
    assert summary["completed"] == (4 if condition == "valid" else 0)
    assert summary["model_errors"] == (0 if condition == "valid" else 4)
    before = inventory(root)
    assert invoke(root, condition, resume=True) == summary
    assert inventory(root) == before
    for key in SCHEDULE:
        task = root / "tasks" / key
        assert checkpoint(task)["recovered"]
        joined = audit_exit(task / "execution")
        assert joined["valid"] and set(joined["roles"]) == {"agent", "guard"}
        pids = [r["pid"] for r in joined["roles"].values()]
        assert pids[0] != pids[1]


def test_missing_only_resume(source, tmp_path):
    root, condition, summary = source
    output = tmp_path / "resume"
    output.mkdir()
    shutil.copy2(root / "identity.json", output / "identity.json")
    for key in SCHEDULE[:-1]:
        shutil.copytree(root / "tasks" / key, output / "tasks" / key)
    before = inventory(output)
    assert invoke(output, condition, resume=True) == summary
    after = inventory(output)
    assert all(after[key] == value for key, value in before.items())


@pytest.mark.parametrize(
    "fault",
    [
        "pid",
        "role",
        "config",
        "task",
        "snapshot",
        "owner",
        "missing",
        "partial",
        "source",
        "extra_field",
        "time",
    ],
)
def test_corruption_rejected_without_new_work(source, tmp_path, fault):
    root, condition, _ = source
    output = tmp_path / "corrupt"
    shutil.copytree(root, output)
    task = output / "tasks/DOC_A6"
    sidecar = task / "execution/exit_milestones.json"
    if fault == "source":
        path = output / "identity.json"
        value = json.loads(path.read_text())
        value["execution_source_sha256"] = {}
        path.write_text(json.dumps(value))
    elif fault == "partial":
        (task / "checkpoint.json").unlink()
    elif fault == "missing":
        sidecar.unlink()
    else:
        value = json.loads(sidecar.read_text())
        if fault == "pid":
            value["workers"]["agent"]["milestones"]["events"]["target_enter"]["pid"] += 1
        elif fault == "role":
            value["workers"]["agent"], value["workers"]["guard"] = (
                value["workers"]["guard"],
                value["workers"]["agent"],
            )
        elif fault == "config":
            value["pair_config_sha256"] = "0" * 64
        elif fault == "task":
            value["task_id"] = "other"
        elif fault == "snapshot":
            value["pair_snapshot_sha256"] = "0" * 64
        elif fault == "owner":
            value["owner_pid"] += 1
        elif fault == "extra_field":
            value["arbitrary_payload"] = "not-allowed"
        elif fault == "time":
            value["observed_until"] = 0.01
        sidecar.write_text(json.dumps(value))
        # Check join directly too: checkpoint hash failure alone is insufficient.
        with pytest.raises(ValueError):
            audit_exit(task / "execution")
    before = inventory(output)
    with pytest.raises((ValueError, FileNotFoundError)):
        invoke(output, condition, resume=True)
    assert inventory(output) == before


class FailedFactory:
    def __call__(self):
        raise RuntimeError("not-serialized-startup-detail")


@pytest.mark.parametrize("failed_role", ["agent", "guard"])
def test_startup_failure_keeps_unstarted_or_partial_markers(tmp_path, failed_role):
    pair = synthetic_pair(
        baseline.StubFactory("agent", "CALC_A2", "valid"),
        DiagnosticFactory(
            baseline.StubFactory("guard", "CALC_A2", "valid"),
            tmp_path / "native/guard_response_diagnostics.jsonl",
        ),
        config("stub"),
        tmp_path / "witness.jsonl",
    )
    factories = [pair._workers[r].factory.factory for r in ("agent", "guard")]
    pair.close()
    factories[0 if failed_role == "agent" else 1] = FailedFactory()
    pair = ExitPair(*factories, config("stub"), tmp_path / "new_witness.jsonl")
    (tmp_path / "native").mkdir()
    task, catalog, level = baseline.case("CALC_A2")
    with pytest.raises(RuntimeError):
        run_synthetic_pair_task(
            task,
            pair=pair,
            constrained=tmp_path / "constraints",
            output=tmp_path / "execution",
            registry_factory=lambda: build_clean_registry(ENVIRONMENT),
            security=configuration(level),
            runtime_config=RUNTIME,
            generation=GENERATION,
            source_catalog=catalog,
        )
    result = audit_exit(tmp_path / "execution")
    if failed_role == "agent":
        assert result["roles"]["guard"]["boundary"] == "not_started"
    assert all(worker._process is None for worker in pair._workers.values())
    assert (
        "not-serialized-startup-detail"
        not in (tmp_path / "execution/exit_milestones.json").read_text()
    )


def test_linked_resume_identity_rejected_before_frozen_runner(tmp_path, monkeypatch):
    output = tmp_path / "resume"
    output.mkdir()
    protected = tmp_path / "do-not-read.json"
    protected.write_text("not for runner")
    (output / "identity.json").symlink_to(protected)

    def forbidden(*args, **kwargs):
        pytest.fail("must reject tree before invoking baseline runner")

    monkeypatch.setattr(baseline, "run", forbidden)
    with pytest.raises(ValueError):
        invoke(output, resume=True)


def test_recorded_runtime_binding_not_host_runtime(source, monkeypatch):
    from react_agent.validation import exit_pair_audit_v1 as auditor

    root, _, _ = source
    output = root / "tasks/CALC_A2/execution"
    recorded = json.loads((output / "exit_milestones.json").read_text())["workers"]["agent"][
        "milestones"
    ]["runtime"]
    other = dict(recorded, system="different-host")
    monkeypatch.setattr(auditor, "runtime_identity", lambda: other)
    assert auditor.audit_exit(output, expected_runtime=recorded)["valid"]
    with pytest.raises(ValueError):
        auditor.audit_exit(output)
