"""Regression for actual factory topology; no model construction or inference."""

import gc
import importlib
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.base import GenerationConfig
from react_agent.llm.context_stress_v1 import ContextStressFactory
from react_agent.llm.generation_policy_v1 import PolicyStressFactory
from react_agent.llm.model_pair_v1 import (
    READY_ACK,
    READY_COMMAND,
    ModelIdentity,
    ModelPair,
    PairConfig,
    ReadyBackend,
    ReadyFactory,
)
from react_agent.llm.policy_stress_factory_v2 import instrument_pair
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory


@pytest.fixture
def sample(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    cli = importlib.import_module("check_phase5_policy_factory")
    pair = ModelPair(
        cli.NativeShapeFactory("agent", tmp_path / "agent.json"),
        cli.NativeShapeFactory("guard", tmp_path / "guard.json"),
        PairConfig(
            ModelIdentity(cli.MODEL, cli.AGENT_REVISION),
            ModelIdentity(cli.MODEL_ID, cli.GUARD_REVISION),
        ),
    )
    events: list[str] = []
    monkeypatch.setattr(
        "react_agent.llm.worker_progress_v1.configure_worker_progress",
        lambda: events.append("progress"),
    )
    yield pair, tmp_path / "probe", tmp_path / "policy", events
    pair.close()
    monkeypatch.undo()
    gc.collect()


def test_original_factory_shape_reproduces_failure(sample: Any) -> None:
    pair, output, policy, events = sample
    broken = ThreadProgressFactory(
        PolicyStressFactory(
            pair._workers["agent"].factory, "agent", output / "agent_stress", policy / "agent"
        )
    )
    with pytest.raises(ValueError, match="authenticated frozen native loader"):
        broken()
    assert events == ["progress"]
    assert not (output / "agent_stress").exists()


def test_fixed_factory_order_and_readiness_does_not_consume_stress(sample: Any) -> None:
    pair, output, policy, events = sample
    instrument_pair(pair, output, policy)
    assert not events
    for role in ("agent", "guard"):
        ready = pair._workers[role].factory
        assert type(ready) is ReadyFactory and type(ready.factory) is ThreadProgressFactory
        assert type(ready.factory.factory) is PolicyStressFactory
        backend = ready()
        assert type(backend) is ReadyBackend
        assert not backend.backend._used and not backend.backend.inner._used
        response = backend.generate(
            [{"role": "user", "content": READY_COMMAND}], GenerationConfig()
        )
        assert response.text == READY_ACK
        assert not backend.backend._used and not backend.backend.inner._used
        assert not (policy / role).exists()
        assert not list((output / f"{role}_stress").iterdir())
    assert events == ["progress", "progress"]


@pytest.mark.parametrize("case", ["started", "nested", "existing", "missing_ready", "double"])
def test_rejects_invalid_topology_before_mutation(sample: Any, case: str) -> None:
    pair, output, policy, events = sample
    if case == "started":
        pair.state = "READY"
    elif case == "nested":
        policy = output / "policy"
    elif case == "existing":
        policy.mkdir()
    elif case == "missing_ready":
        pair._workers["guard"].factory = pair._workers["guard"].factory.factory
    elif case == "double":
        instrument_pair(pair, output, policy)
    before = [pair._workers[r].factory for r in ("agent", "guard")]
    with pytest.raises(ValueError):
        instrument_pair(pair, output, policy)
    assert [pair._workers[r].factory for r in ("agent", "guard")] == before
    assert not events


def test_native_type_check_not_relaxed() -> None:
    assert ContextStressFactory.__module__ == "react_agent.llm.context_stress_v1"
