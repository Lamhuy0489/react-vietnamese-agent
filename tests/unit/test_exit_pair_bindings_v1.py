"""Lazy native topology and explicit observer identity, without loading models."""

import pickle
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from react_agent.llm import native_constrained_pair_v1 as old_native
from react_agent.llm import native_guard_diagnostics_v2 as observer
from react_agent.llm.exit_pair_probe_v1 import config, fixed_identity
from react_agent.llm.exit_pair_v1 import ExitPair, ExitPairConfig, observer_config
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.guard_observer_probe_v2 import StubFactory
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_v2 import ShutdownPairConfig
from react_agent.llm.native_exit_pair_v1 import native_pair
from react_agent.security_v1.constrained_host_v1 import native_root as old_root
from react_agent.security_v1.exit_milestones_v1 import MilestoneBackend, runtime_identity
from react_agent.security_v1.exit_pair_runtime_v1 import native_root
from react_agent.validation.exit_pair_audit_v1 import checked_runtime

ROOT = Path(__file__).resolve().parents[2]


def pin():
    return GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )


def args(root):
    return (
        [root / name for name in ("agent", "inventory", "guard")]
        + [pin()]
        + [root / name for name in ("native", "attention", "policy")]
    )


def test_native_factories_unchanged_lazy_and_picklable(tmp_path):
    before = {module: dict(vars(module)) for module in (old_native, observer)}
    old = old_native.native_pair(
        *args(tmp_path), witness=tmp_path / "old_witness", constrained=tmp_path / "constraints"
    )
    pair = native_pair(
        *args(tmp_path), witness=tmp_path / "new_witness", constrained=tmp_path / "constraints"
    )
    try:
        assert type(pair) is ExitPair and pair.state == "NEW"
        values = asdict(pair.config)
        assert values.pop("exit_observer") == "exit_milestones_v1"
        assert values == asdict(old.config)
        assert pair.config.sha256 != old.config.sha256
        for role in ("agent", "guard"):
            worker = pair._workers[role]
            assert type(worker) is MilestoneBackend and not worker.attempts
            assert worker.factory == old._workers[role].factory
            assert pickle.loads(pickle.dumps(worker.factory)) == worker.factory  # noqa: S301
        assert native_root(pair) == tmp_path / "constraints"
        with pytest.raises(TypeError):
            old_root(pair)
        assert not list(tmp_path.iterdir())
        assert all(all(vars(m)[k] is v for k, v in state.items()) for m, state in before.items())
    finally:
        old.close()
        pair.close()


@pytest.mark.parametrize("target", ["agent", "inventory", "guard", "native", "attention", "policy"])
def test_native_overlap_rejected_before_any_worker(tmp_path, target):
    with pytest.raises(ValueError):
        native_pair(*args(tmp_path), witness=tmp_path / "witness", constrained=tmp_path / target)
    assert not list(tmp_path.iterdir())


def test_identity_and_inherited_generation():
    c = config("stub")
    assert observer_config(c) is c
    assert type(c) is ExitPairConfig
    assert ExitPair.generate is DiagnosticPair.generate
    for role in ("agent", "guard"):
        assert c.execution(role, cold=True).identity != c.execution(role, cold=False).identity
        assert c.execution(role, cold=True).graceful_shutdown_seconds == 2.0
    with pytest.raises(ValueError):
        replace(c, exit_observer="unknown")
    with pytest.raises(ValueError):
        fixed_identity("hf", "backend_failure")
    with pytest.raises(TypeError):
        observer_config(object())
    old_values = vars(c).copy()
    old_values.pop("exit_observer")
    assert observer_config(ShutdownPairConfig(**old_values)) == c


def test_only_terminal_reaped_snapshots(tmp_path):
    pair = ExitPair(
        StubFactory("agent", "CALC_A2", "valid"),
        StubFactory("guard", "CALC_A2", "valid"),
        config("stub"),
        tmp_path / "witness",
    )
    with pytest.raises(RuntimeError):
        pair.exit_snapshot()
    pair.close()
    assert all(v["status"] == "reaped" for v in pair.exit_snapshot().values())
    pair.state = "FAILED"
    pair._workers["agent"]._process = object()
    assert pair.exit_snapshot()["agent"] == dict(status="unreaped", milestones=None)
    pair._workers["agent"]._process = None


@pytest.mark.parametrize("fault", ["missing", "implementation", "hash", "version", "extra"])
def test_recorded_interpreter_shape_is_strict(fault):
    value = runtime_identity()
    if fault == "missing":
        value.pop("system")
    elif fault == "extra":
        value["payload"] = "not allowed"
    elif fault == "implementation":
        value["implementation"] = "unknown"
    elif fault == "hash":
        value["threads_sha256"] = "bad"
    else:
        value["version"] = "unknown"
    with pytest.raises(ValueError):
        checked_runtime(value)
