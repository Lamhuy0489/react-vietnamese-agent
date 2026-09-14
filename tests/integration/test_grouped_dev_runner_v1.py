"""All public Dev keys plus immutable prefix resume and hostile receipt controls."""

import json
import socket
from dataclasses import dataclass
from pathlib import Path

import pytest

from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.grouped_dev_identity_v1 import identity
from react_agent.llm.grouped_dev_runner_v1 import ScriptedBackend, run
from react_agent.validation.grouped_dev_checkpoint_v1 import audit_prefix

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "data/adversarial/release_v2"
ENV = ROOT / "data/clean/v1_1/environment"
COMMIT = "a" * 40


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("CPU grouped runner must not access network")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def invoke(path, shard=0, **kwargs):
    return run(path, RELEASE, ENV, commit=COMMIT, shard=shard, **kwargs)


@pytest.mark.parametrize("shard", range(8))
def test_all_112_tasks_real_spawn_resume_readonly(tmp_path, shard):
    path = tmp_path / "run"
    first = invoke(path, shard, max_new_tasks=1)
    assert first["completed"] == 1
    manifest, _ = identity(RELEASE, ENV, COMMIT)
    firstkey = next(t["key"] for t in manifest["tasks"] if t["shard"] == shard)
    before = inventory(path / "tasks" / firstkey)
    done = invoke(path, shard, resume=True)
    assert done["completed"] == 14 and done["remaining"] == 0
    assert before == inventory(path / "tasks" / firstkey)
    all_before = inventory(path)
    assert done == invoke(path, shard, resume=True)
    assert len(audit_prefix(path, manifest, shard)) == 14
    assert all_before == inventory(path)
    events = [
        json.loads(s)
        for p in (path / "tasks").rglob("trace_legacy.jsonl")
        for s in p.read_text().splitlines()
    ]
    assert any(e["event"] == "tool_result" for e in events)


@pytest.mark.parametrize(
    "mutation", ["identity", "partial", "unknown", "gap", "raw", "metadata", "checkpoint", "link"]
)
def test_bad_resume_refuses_before_more_tasks(tmp_path, mutation):
    path = tmp_path / "run"
    invoke(path, max_new_tasks=1)
    manifest, _ = identity(RELEASE, ENV, COMMIT)
    task = manifest["tasks"][0]
    root = path / "tasks" / task["key"]
    checkpoint = root / "checkpoint.json"
    if mutation == "identity":
        saved = json.loads((path / "identity.json").read_text())
        saved["run"]["runtime"]["max_steps"] = 1
        (path / "identity.json").write_text(json.dumps(saved))
    elif mutation == "partial":
        (path / "tasks" / manifest["tasks"][1]["key"]).mkdir()
    elif mutation == "unknown":
        (path / "tasks" / "unexpected").mkdir()
    elif mutation == "gap":
        root.rename(path / "tasks" / manifest["tasks"][2]["key"])
    elif mutation == "raw":
        (root / "extra.json").write_text("{}")
    elif mutation == "link":
        (root / "link").symlink_to(tmp_path)
    elif mutation == "metadata":
        meta = root / "execution/runtime/run_metadata.json"
        saved = json.loads(meta.read_text())
        saved["runtime_version"] = "security_runtime_v9"
        meta.write_text(json.dumps(saved))
        saved = json.loads(checkpoint.read_text())
        saved["raw_sha256"] = {k: v for k, v in inventory(root).items() if k != "checkpoint.json"}
        checkpoint.write_text(json.dumps(saved))
    else:
        saved = json.loads(checkpoint.read_text())
        saved["key"] = manifest["tasks"][1]["key"]
        checkpoint.write_text(json.dumps(saved))
    with pytest.raises((ValueError, FileNotFoundError)):
        invoke(path, resume=True)
    assert len(list((path / "tasks").iterdir())) == (2 if mutation in {"partial", "unknown"} else 1)


@dataclass(frozen=True)
class InvalidAgentFactory:
    def __call__(self):
        return InvalidAgent()


class InvalidAgent(ScriptedBackend):
    def __init__(self):
        super().__init__("agent", "not-json")

    def generate(self, messages, config):
        self.calls = 0
        return super().generate(messages, config)


def test_terminal_failure_checkpoint_never_retried(tmp_path, monkeypatch):
    import react_agent.llm.grouped_dev_runner_v1 as module

    original = module.run_pair_task

    def inject_failure(task, **kwargs):
        kwargs["agent_factory"] = InvalidAgentFactory()
        return original(task, **kwargs)

    monkeypatch.setattr(module, "run_pair_task", inject_failure)
    path = tmp_path / "fault_control"
    result = invoke(path, max_new_tasks=1)
    assert result["terminal_statuses"] == ["parse_failure"]
    before = inventory(path)

    def must_not_run(*args, **kwargs):
        raise AssertionError("completed semantic failure must not rerun")

    monkeypatch.setattr(module, "run_pair_task", must_not_run)
    assert result == invoke(path, resume=True, max_new_tasks=0)
    assert before == inventory(path)


def test_missing_input_identity_or_shard_does_not_resume(tmp_path):
    path = tmp_path / "run"
    invoke(path, max_new_tasks=0)
    before = inventory(path)
    with pytest.raises(ValueError):
        invoke(path, 1, resume=True)
    with pytest.raises(ValueError):
        run(path, RELEASE, ENV, commit="b" * 40, shard=0, resume=True)
    assert before == inventory(path)
