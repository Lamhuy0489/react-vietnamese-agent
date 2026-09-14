"""Stop before native load: authenticate topology/ownership, not HF execution."""

from pathlib import Path

import pytest

from react_agent.llm import grouped_dev_runner_v2 as runner
from react_agent.llm.guard_diagnostic_backend_v1 import DiagnosticFactory
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver
from react_agent.llm.model_pair_v2 import AgentWorkerConfig, ShutdownPair

ROOT = Path(__file__).resolve().parents[2]


class NativeShapedObserver(SyntheticPairObserver):
    interval = 1.0


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A6"])
def test_native_routing_stops_before_load_retains_recovery(tmp_path, monkeypatch, level):
    original = runner.identity

    def select_first(*args):
        manifest, rows = original(*args)
        manifest["tasks"] = [t for t in manifest["tasks"] if t["level"] == level]
        return manifest, rows

    seen = []

    def stop(task, **kwargs):
        assert (kwargs["output"].parent / "native").is_dir()
        if level in {"A0", "A1"}:
            assert "pair" not in kwargs
            assert type(kwargs["agent_execution"]) is AgentWorkerConfig
        else:
            pair = kwargs["pair"]
            assert type(pair) is ShutdownPair
            assert isinstance(pair._workers["guard"].factory.factory, DiagnosticFactory)
            assert all(not w.attempts for w in pair._workers.values())
        seen.append(level)
        raise RuntimeError("test stop before native model load")

    monkeypatch.setattr(runner, "identity", select_first)
    monkeypatch.setattr(runner, "run_pair_task", stop)
    monkeypatch.setattr(runner.time, "sleep", lambda _: None)
    pin = GuardSnapshot.model_validate_json(
        (ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    output = tmp_path / "native_routing_control"
    with pytest.raises(RuntimeError, match="before native model load"):
        runner.run(
            output,
            ROOT / "data/adversarial/release_v2",
            ROOT / "data/clean/v1_1/environment",
            commit="a" * 40,
            shard=0,
            backend="hf",
            agent=tmp_path / "agent",
            guard=tmp_path / "guard",
            snapshot=pin,
            model_inventory=ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json",
            observer_factory=NativeShapedObserver,
        )
    assert seen == [level]
    task = next((output / "tasks").iterdir())
    assert (task / "recovery.json").is_file()
    assert not (task / "checkpoint.json").exists()
    assert not list(task.rglob("*_hf_metrics.jsonl"))
