from __future__ import annotations

import json
from pathlib import Path

import pytest

from react_agent.llm import security_runtime_probe_v1 as probe
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver
from react_agent.llm.native_agent_only_v1 import native_agent
from react_agent.llm.ordinary_pair_probe_v1 import native_config
from react_agent.llm.request_policy_pair_v1 import policy_pair

ROOT = Path(__file__).resolve().parents[2]


def run(output, **kwargs):
    return probe.run(
        output,
        ROOT / "data/clean/v1_1/environment",
        backend="stub",
        commit="a" * 40,
        observer_factory=SyntheticPairObserver,
        **kwargs,
    )


def test_seven_levels_and_immutable_resume(tmp_path, monkeypatch):
    output = tmp_path / "probe"
    result = run(output)
    assert result["terminals"] == ["completed"] * 7
    before = probe.inventory(output)

    def fail(*args, **kwargs):
        raise AssertionError("completed tasks must not infer again")

    with monkeypatch.context() as patch:
        patch.setattr(probe, "run_pair_task", fail)
        assert run(output, resume=True) == result
    assert probe.inventory(output) == before
    # Move one checkpoint out to simulate wholly missing work without altering its bytes.
    (output / "tasks/A6").rename(tmp_path / "retained_A6")
    retained = probe.inventory(output)
    assert run(output, resume=True) == result
    assert all(probe.inventory(output)[n] == h for n, h in retained.items())
    for level in probe.LEVELS:
        receipt = json.loads((output / "tasks" / level / "execution/pair_runtime.json").read_text())
        assert len(receipt["snapshot"]["workers"]) == (1 if level in {"A0", "A1"} else 2)


def test_partial_identity_and_hash_rejections(tmp_path):
    output = tmp_path / "probe"
    output.mkdir()
    (output / "identity.json").write_text("{}")
    with pytest.raises(ValueError, match="identity"):
        run(output, resume=True)
    with pytest.raises(ValueError, match="overlap"):
        probe.run(
            output, output, backend="stub", commit="a" * 40, observer_factory=SyntheticPairObserver
        )


def test_native_metrics_parent_and_partial_resume(tmp_path, monkeypatch):
    from react_agent.llm.guard_snapshot_v1 import GuardSnapshot

    pin = GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    root = tmp_path / "native_run"

    def fail_before_load(*args, **kwargs):
        assert (root / "tasks/A0/native").is_dir()
        raise RuntimeError("synthetic infrastructure failure")

    monkeypatch.setattr(probe, "run_pair_task", fail_before_load)
    arguments = dict(
        backend="hf",
        commit="a" * 40,
        observer_factory=SyntheticPairObserver,
        agent=tmp_path / "model",
        guard=tmp_path / "guard",
        snapshot=pin,
        model_inventory=ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json",
    )
    with pytest.raises(RuntimeError, match="synthetic infrastructure"):
        probe.run(root, ROOT / "data/clean/v1_1/environment", **arguments)
    assert (root / "tasks/A0/recovery.json").is_file()
    with pytest.raises(ValueError, match="partial attempt"):
        probe.run(root, ROOT / "data/clean/v1_1/environment", resume=True, **arguments)


def test_agent_factory_matches_pair_stack_without_loading(tmp_path):
    agent, inventory = tmp_path / "model", tmp_path / "inventory.json"
    single = native_agent(
        agent, inventory, tmp_path / "metrics", tmp_path / "att", tmp_path / "policy"
    )
    native = single.factory.attention.native_factory
    paired = policy_pair(
        native, lambda: None, native_config(), tmp_path / "pair_att", tmp_path / "pair_policy"
    )
    try:
        paired_stack = paired._workers["agent"].factory.factory
        assert type(single) is type(paired_stack)
        assert type(single.factory) is type(paired_stack.factory)
        assert type(single.factory.attention) is type(paired_stack.factory.attention)
        assert single.factory.attention.role == "agent"
        assert paired_stack.factory.attention.native_factory == native
        assert not list(tmp_path.iterdir())
    finally:
        paired.close()


@pytest.mark.parametrize("kind", ["existing", "overlap", "input_overlap"])
def test_native_factory_validates_paths_before_loading(tmp_path, kind):
    metrics, attention, policy = tmp_path / "metrics", tmp_path / "attention", tmp_path / "policy"
    model, inventory = tmp_path / "model", tmp_path / "inventory.json"
    if kind == "existing":
        metrics.touch()
    elif kind == "overlap":
        policy = attention / "nested"
    else:
        attention = model / "inside"
    with pytest.raises(ValueError):
        native_agent(model, inventory, metrics, attention, policy)
