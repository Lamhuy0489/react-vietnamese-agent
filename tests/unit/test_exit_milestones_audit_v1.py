"""Observer contract and strict milestone receipt validation."""

import copy
import json
import multiprocessing as mp
import os
from types import SimpleNamespace

import pytest

from react_agent.llm.exit_milestone_probe_v1 import config, run, run_case
from react_agent.llm.teardown_probe_v1 import worker_config
from react_agent.security_v1.exit_milestones_v1 import (
    EVENTS,
    MilestoneBackend,
    _Context,
    install_hook,
    mark,
    new_slots,
    runtime_identity,
)
from react_agent.security_v1.worker_shutdown_v2 import ShutdownBackend
from react_agent.validation.exit_milestones_v1 import audit_milestones


def test_frozen_methods_and_distinct_identity():
    assert MilestoneBackend.generate is ShutdownBackend.generate
    assert MilestoneBackend._cleanup is ShutdownBackend._cleanup
    assert config().identity != worker_config().identity
    assert config().graceful_shutdown_seconds == 2.0


@pytest.mark.parametrize("error", [None, ValueError, KeyboardInterrupt, SystemExit])
def test_hooks_delegate_restore_and_propagate(error):
    slots = new_slots(mp.get_context("spawn"))
    calls = []
    sentinel = object()

    def original(*args, **kwargs):
        calls.append((args, kwargs))
        if error:
            raise error("private-detail-not-serialized")
        return sentinel

    owner = SimpleNamespace(callback=original)
    install_hook(owner, "callback", "finalizers", slots)
    if error:
        with pytest.raises(error):
            owner.callback(1, key=2)
    else:
        assert owner.callback(1, key=2) is sentinel
    assert calls == [((1,), {"key": 2})]
    assert owner.callback is original
    assert slots["time"][EVENTS.index("finalizers_enter")] > 0
    completion = "error" if error else "return"
    assert slots["time"][EVENTS.index("finalizers_" + completion)] > 0
    assert "private-detail" not in repr(slots)


def test_duplicate_marker_rejected():
    slots = new_slots(mp.get_context("spawn"))
    mark(slots, "target_enter")
    with pytest.raises(RuntimeError, match="duplicate"):
        mark(slots, "target_enter")


def test_live_or_foreign_snapshot_rejected():
    backend = MilestoneBackend(lambda: None, config())
    assert all(value is None for value in backend.exit_milestones()["events"].values())
    backend._process = object()
    with pytest.raises(RuntimeError, match="reaping"):
        backend.exit_milestones()
    backend._process = None
    backend._owner_pid = os.getpid() + 1
    with pytest.raises(RuntimeError):
        backend.exit_milestones()


def test_plain_config_rejected():
    with pytest.raises(TypeError):
        MilestoneBackend(lambda: None, worker_config())


def test_context_rejects_other_target():
    with pytest.raises(ValueError):
        _Context(None, {}, {}).Process(target=lambda: None, args=(), daemon=True)


def snapshot():
    events = {name: None for name in EVENTS}
    for index, name in enumerate(name for name in EVENTS if not name.endswith("error")):
        events[name] = dict(at=float(index + 1), pid=123, non_daemon_threads=0)
    record = dict(
        protocol="exit_milestones_v1",
        runtime=runtime_identity(),
        execution_config_sha256=config().identity,
        events=events,
    )
    event = dict(
        schema_version="worker_shutdown_v2",
        sequence=1,
        pid=123,
        method="GRACEFUL",
        reaped=True,
        exitcode=0,
        elapsed_seconds=1.0,
        graceful_requested=True,
        graceful_shutdown_seconds=2.0,
        stop_received=True,
        stop_received_seconds=0.01,
        serve_returned=True,
        serve_returned_after_stop_seconds=0.02,
    )
    return record, event


def check(record, event):
    return audit_milestones(
        record,
        event,
        runtime=runtime_identity(),
        config_sha256=config().identity,
        observed_until=9.0,
    )


def test_complete_and_partial_observations():
    record, event = snapshot()
    assert check(record, event) == "observed_stages_returned"
    event.update(method="TERMINATE", exitcode=-15)
    record["events"]["threads_return"] = None
    assert check(record, event) == "threads_entered_only"
    for name in EVENTS:
        record["events"][name] = None
    assert check(record, event) == "unobserved"


@pytest.mark.parametrize(
    "mutation",
    [
        "pid",
        "nan",
        "negative_threads",
        "bool_threads",
        "extra",
        "order",
        "missing_enter",
        "both_completions",
        "gap",
        "runtime",
        "config",
        "live",
        "graceful_partial",
    ],
)
def test_tampering_rejected(mutation):
    record, event = snapshot()
    target = record["events"]["target_enter"]
    if mutation == "pid":
        target["pid"] = 999
    elif mutation == "nan":
        target["at"] = float("nan")
    elif mutation == "negative_threads":
        target["non_daemon_threads"] = -1
    elif mutation == "bool_threads":
        target["non_daemon_threads"] = True
    elif mutation == "extra":
        target["name"] = "must-not-log"
    elif mutation == "order":
        target["at"] = 8.0
    elif mutation == "missing_enter":
        record["events"]["target_enter"] = None
    elif mutation == "both_completions":
        record["events"]["target_error"] = copy.deepcopy(target)
    elif mutation == "gap":
        record["events"]["target_return"] = None
    elif mutation == "runtime":
        record["runtime"]["version"] = "other"
    elif mutation == "config":
        record["execution_config_sha256"] = "other"
    elif mutation == "live":
        event["reaped"] = False
    elif mutation == "graceful_partial":
        record["events"]["threads_return"] = None
    with pytest.raises((ValueError, KeyError)):
        check(record, event)


def test_fresh_output_and_invalid_modes(tmp_path):
    with pytest.raises(ValueError):
        run(tmp_path, "a" * 40)
    with pytest.raises(ValueError):
        run(tmp_path / "absent", "not-a-commit")
    with pytest.raises(ValueError):
        run_case("native")


def test_uncommitted_marker_is_not_published():
    backend = MilestoneBackend(lambda: None, config())
    backend._milestones["pid"][0] = os.getpid()
    backend._milestones["threads"][0] = 1
    assert backend.exit_milestones()["events"]["target_enter"] is None


def test_unsupported_interpreter_rejected(monkeypatch):
    from react_agent.security_v1 import exit_milestones_v1

    monkeypatch.setattr(exit_milestones_v1.platform, "python_implementation", lambda: "unknown")
    with pytest.raises(RuntimeError, match="unsupported"):
        runtime_identity()


def test_orchestrator_checkpoints_all_fixed_cases(tmp_path, monkeypatch):
    from react_agent.llm import exit_milestone_probe_v1

    output = tmp_path / "fresh"
    calls = []

    def fake_case(mode):
        assert (output / "cases").is_dir()
        calls.append(mode)
        return {"lifecycle": [{"method": "routing-test-only"}]}

    monkeypatch.setattr(exit_milestone_probe_v1, "run_case", fake_case)
    run(output, "a" * 40)
    assert calls == list(exit_milestone_probe_v1.MODES) * 3
    assert len(list((output / "cases").glob("*.json"))) == 18


def test_audit_rejects_link_before_any_json_read(tmp_path, monkeypatch):
    from react_agent.llm import exit_milestone_probe_v1

    root = tmp_path / "artifacts"
    root.mkdir()
    target = tmp_path / "not-for-reading.json"
    target.write_text("private sentinel")
    (root / "identity.json").symlink_to(target)

    def forbidden_read(_):
        pytest.fail("must reject symlink before reading payload")

    monkeypatch.setattr(exit_milestone_probe_v1, "read_record", forbidden_read)
    with pytest.raises(ValueError, match="linked"):
        exit_milestone_probe_v1.audit(root)


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "extra",
        "missing",
        "source",
        "runtime",
        "overlap",
        "scope",
        "duplicate_json",
        "empty_directory",
    ],
)
def test_schedule_and_inventory_audit(tmp_path, monkeypatch, mutation):
    from react_agent.llm import exit_milestone_probe_v1 as probe

    # Deliberately synthetic routing fixture; per-case validation is tested separately.
    output = tmp_path / "controls"
    sequence = 0

    def fake_case(_):
        nonlocal sequence
        sequence += 1
        return dict(
            milestones={"events": {"target_enter": {"at": float(sequence)}}},
            close_started=float(sequence),
            close_finished=sequence + 0.5,
            lifecycle=[dict(method="routing-test-only")],
        )

    monkeypatch.setattr(probe, "run_case", fake_case)
    monkeypatch.setattr(probe, "audit_case", lambda *args: "fixture-only")
    probe.run(output, "a" * 40)
    identity_path = output / "identity.json"
    identity = json.loads(identity_path.read_text())
    if mutation == "extra":
        (output / "extra.json").write_text("{}")
    elif mutation == "missing":
        (output / "cases/r1_fast.json").unlink()
    elif mutation in {"source", "runtime", "scope"}:
        key = {"source": "source_sha256", "runtime": "runtime", "scope": "gpu_runs"}[mutation]
        identity[key] = "tampered"
        identity_path.write_text(json.dumps(identity))
    elif mutation == "overlap":
        path = output / "cases/r2_fast.json"
        record = json.loads(path.read_text())
        record["milestones"]["events"]["target_enter"]["at"] = 0.1
        path.write_text(json.dumps(record))
    elif mutation == "duplicate_json":
        identity_path.write_text('{"plan": {}, "plan": {}}')
    elif mutation == "empty_directory":
        (output / "unrelated").mkdir()
    if mutation is None:
        assert probe.audit(output) == probe.audit(output)
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            probe.audit(output)
