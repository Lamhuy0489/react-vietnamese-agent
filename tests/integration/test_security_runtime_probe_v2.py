"""Real-spawn probe v2 controls; no native model load or benchmark payloads."""

import copy
import json
from pathlib import Path

import pytest
import test_security_runtime_probe_v1 as legacy

from react_agent.llm import security_runtime_probe_v2 as probe
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver
from react_agent.llm.model_pair_v2 import AgentWorkerConfig, ShutdownPair
from react_agent.security_v1.worker_shutdown_v2 import ShutdownBackend


@pytest.fixture(autouse=True)
def version(monkeypatch):
    monkeypatch.setattr(legacy, "probe", probe)


def test_all_levels_resume_and_shutdown(tmp_path, monkeypatch):
    legacy.test_seven_levels_and_immutable_resume(tmp_path, monkeypatch)
    for level in probe.LEVELS:
        root = tmp_path / "probe/tasks" / level
        assert probe.checkpoint(root)["terminal"] == "completed"
        receipt = json.loads((root / "execution/pair_runtime.json").read_text())
        assert receipt["profile"] == "model_pair_security_runtime_v3"
        assert all(
            e["method"] == "GRACEFUL"
            for worker in receipt["snapshot"]["workers"].values()
            for e in worker["lifecycle"]
        )


def test_native_partial_is_retained(tmp_path, monkeypatch):
    legacy.test_native_metrics_parent_and_partial_resume(tmp_path, monkeypatch)


def test_identity_refusal(tmp_path):
    legacy.test_partial_identity_and_hash_rejections(tmp_path)


@pytest.mark.parametrize("level", ["A0", "A2"])
def test_native_entry_selects_new_workers_before_load(tmp_path, monkeypatch, level):
    pin = GuardSnapshot.model_validate_json(
        (legacy.ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text()
    )
    seen = []

    def stop_before_load(*args, **kwargs):
        if level == "A0":
            assert "pair" not in kwargs and type(kwargs["agent_execution"]) is AgentWorkerConfig
        else:
            pair = kwargs["pair"]
            assert type(pair) is ShutdownPair
            assert all(type(w) is ShutdownBackend for w in pair._workers.values())
            assert all(not w.attempts for w in pair._workers.values())
        seen.append(level)
        raise RuntimeError("synthetic stop before native load")

    monkeypatch.setattr(probe, "LEVELS", (level,))
    monkeypatch.setattr(probe, "run_pair_task", stop_before_load)
    with pytest.raises(RuntimeError, match="before native load"):
        probe.run(
            tmp_path / "probe",
            legacy.ROOT / "data/clean/v1_1/environment",
            backend="hf",
            commit="a" * 40,
            observer_factory=SyntheticPairObserver,
            agent=tmp_path / "agent",
            guard=tmp_path / "guard",
            snapshot=pin,
            model_inventory=legacy.ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json",
        )
    assert seen == [level]
    assert (tmp_path / "probe/tasks" / level / "recovery.json").is_file()


def test_identity_mutations_preserve_original(tmp_path, monkeypatch):
    root = tmp_path / "probe"
    legacy.run(root)
    before = probe.inventory(root)
    path = root / "identity.json"
    identity = json.loads(path.read_text())
    for field, replacement in {
        "protocol": "security_runtime_probe_v1",
        "levels": ["A6"],
        "task_sha256": "0" * 64,
        "pair_config": {},
        "agent_only_execution": {},
        "generation": {},
        "source_catalog": {},
        "automatic_retry": True,
        "test_tasks": 1,
    }.items():
        changed = copy.deepcopy(identity)
        changed[field] = replacement
        original = Path.read_text

        def read(target, *args, replacement=changed, reader=original, **kwargs):
            return json.dumps(replacement) if target == path else reader(target, *args, **kwargs)

        with monkeypatch.context() as patch:
            patch.setattr(Path, "read_text", read)
            with pytest.raises(ValueError, match="identity"):
                probe.checkpoint(root / "tasks/A0")
            with pytest.raises(ValueError, match="identity"):
                legacy.run(root, resume=True)
    assert probe.inventory(root) == before
