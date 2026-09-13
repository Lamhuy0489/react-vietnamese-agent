"""No native loads: check construction, pinned identities and fail-before-allocation."""

import pickle
from dataclasses import replace
from pathlib import Path

import pytest

from react_agent.llm import request_policy_pair_v2 as policy
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_v1 import ModelIdentity, ReadyFactory
from react_agent.llm.model_pair_v2 import ShutdownPair, ShutdownPairConfig
from react_agent.llm.native_agent_only_v1 import native_agent
from react_agent.llm.native_shutdown_v2 import agent_config, native_config, native_pair
from react_agent.llm.ordinary_pair_probe_v1 import native_config as old_config
from react_agent.security_v1.worker_shutdown_v2 import ShutdownBackend

ROOT = Path(__file__).resolve().parents[2]


def forbidden_load():
    raise AssertionError("native load/transport allocation forbidden")


def test_lazy_native_pair_agent_stack_and_pickle(tmp_path):
    pin = GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    pair = native_pair(
        tmp_path / "agent",
        tmp_path / "inventory",
        tmp_path / "guard",
        pin,
        tmp_path / "native",
        tmp_path / "attention",
        tmp_path / "policy",
    )
    try:
        assert type(pair) is ShutdownPair and type(pair.config) is ShutdownPairConfig
        assert pair.state == "NEW" and not list(tmp_path.iterdir())
        single = native_agent(
            tmp_path / "agent",
            tmp_path / "inventory",
            tmp_path / "native/agent_hf_metrics.jsonl",
            tmp_path / "attention/agent",
            tmp_path / "policy/agent",
        )
        for role, worker in pair._workers.items():
            assert type(worker) is ShutdownBackend and type(worker.factory) is ReadyFactory
            assert pickle.loads(pickle.dumps(worker.factory)) == worker.factory  # noqa: S301
            assert worker.config == pair.config.execution(role, cold=True)
            assert not worker.attempts
        assert single == pair._workers["agent"].factory.factory
        for cold in (True, False):
            assert agent_config(pair.config).execution(cold=cold) == pair.config.execution(
                "agent", cold=cold
            )
    finally:
        pair.close()


@pytest.mark.parametrize("role", ["agent", "guard"])
@pytest.mark.parametrize("fault", ["identity", "ready", "progress", "attention", "policy", "none"])
def test_reject_before_transport(tmp_path, monkeypatch, role, fault):
    config = native_config()
    factories = {"agent": forbidden_load, "guard": forbidden_load}
    adapter = policy.EfficientRequestFactory(forbidden_load, role, tmp_path / "a")
    if fault == "identity":
        config = replace(config, **{role: ModelIdentity("wrong", "wrong")})
    else:
        factories[role] = {
            "ready": ReadyFactory(forbidden_load),
            "progress": policy.ThreadProgressFactory(forbidden_load),
            "attention": adapter,
            "policy": policy.RequestPolicyFactory(adapter, tmp_path / "p"),
            "none": None,
        }[fault]
    monkeypatch.setattr(policy, "ShutdownPair", lambda *a: forbidden_load())
    with pytest.raises(ValueError):
        policy.policy_pair(
            factories["agent"],
            factories["guard"],
            config,
            tmp_path / "attention",
            tmp_path / "policy",
        )
    assert not list(tmp_path.iterdir())


def test_reject_old_config(tmp_path, monkeypatch):
    monkeypatch.setattr(policy, "ShutdownPair", lambda *a: forbidden_load())
    with pytest.raises(TypeError):
        policy.policy_pair(
            forbidden_load, forbidden_load, old_config(), tmp_path / "a", tmp_path / "p"
        )
    with pytest.raises(TypeError):
        agent_config(old_config())


@pytest.mark.parametrize("fault", ["same", "nested", "existing", "symlink", "input", "pin"])
def test_native_paths_and_pin_rejected(tmp_path, monkeypatch, fault):
    pin = GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    model, inventory, guard = tmp_path / "agent", tmp_path / "inventory", tmp_path / "guard"
    output, attention, path = tmp_path / "native", tmp_path / "att", tmp_path / "policy"
    if fault == "same":
        path = attention
    elif fault == "nested":
        path = attention / "nested"
    elif fault == "existing":
        output.mkdir()
    elif fault == "symlink":
        model.symlink_to(tmp_path, target_is_directory=True)
    elif fault == "input":
        output = model / "nested"
    else:
        pin = None
    monkeypatch.setattr(policy, "ShutdownPair", lambda *a: forbidden_load())
    with pytest.raises(ValueError):
        native_pair(model, inventory, guard, pin, output, attention, path)
