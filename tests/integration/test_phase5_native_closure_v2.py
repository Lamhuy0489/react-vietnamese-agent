"""Native-run orchestration is tested offline; synthetic output cannot accept it."""

import importlib
import json
import tempfile
from pathlib import Path

import pytest

from react_agent.llm.request_worker_journal_v1 import RequestWorkerJournal
from react_agent.llm.request_worker_runtime_v1 import (
    RequestWorkerBackend,
    RequestWorkerSessionFactory,
)
from react_agent.llm.request_worker_transport_v1 import WorkerExchange
from react_agent.serving.structured_api_v1 import AGENT_SCHEMA, GUARD_SCHEMA, canonical, sha

ROOT = Path(__file__).resolve().parents[2]


class SyntheticTransport:
    def __init__(self, identity):
        self.identity = identity

    def exchange(self, method, path, payload):
        assert (method, path) == ("POST", "/chat/completions")
        role = self.identity["role"]
        content = '{"risk":"SAFE","labels":[],"confidence":"LOW"}'
        if role == "agent":
            content = (
                '{"action":{"name":"calculator","arguments":{"expression":"19*4+3"}}}'
                if len(payload["messages"]) == 2
                else '{"final_answer":{"answer":"79"}}'
            )
        result = {
            "profile": "react-vn-structured-api-v1",
            "model": "synthetic",
            "model_revision": self.identity["model_revision"],
            "session_id": self.identity["session_id"],
            "choices": [
                {"finish_reason": "stop", "message": {"role": "assistant", "content": content}}
            ],
            "execution": {
                "constrained_decoding": True,
                "seed": payload["seed"],
                "schema_sha256": sha(
                    canonical(GUARD_SCHEMA if role == "guard" else AGENT_SCHEMA).encode()
                ),
            },
        }
        status = {
            "instance_id": "boot1",
            "request_id": payload["request_id"],
            "request_sha256": sha(canonical(payload).encode()),
            "state": "SUCCEEDED",
            "engine_returned": True,
            "engine_active": False,
            "gpu_quiescence_attested": True,
            "quiescence_basis": "device_synchronize",
            "durable": True,
            "instance_retired": False,
            "http_status": 200,
            "cancel_requested": False,
            "response_sha256": sha(canonical(result).encode()),
        }
        return WorkerExchange(200, {"identity": self.identity, "request": status, "result": result})

    def __call__(self, method, path, payload):
        return self.exchange(method, path, payload).payload


class RunnerFactory(RequestWorkerSessionFactory):
    @classmethod
    def from_directory(cls, directory, journal_root, task_id, role, **kwargs):
        return cls(
            directory,
            journal_root,
            task_id,
            role,
            "c",
            "m",
            150,
            "synthetic",
            "sha256:" + "c" * 64,
            "session_" + role,
            "source",
            "worker",
            "boot1",
        )

    def __call__(self):
        transport = SyntheticTransport(self.public_identity())
        journal = RequestWorkerJournal(transport, self.journal_root, self.task_id)
        return RequestWorkerBackend(
            journal, model=self.model_id, role=self.role, identity=self.public_identity()
        )


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = importlib.import_module("run_phase5_native_closure_v2")
    monkeypatch.setattr(module, "RequestWorkerSessionFactory", RunnerFactory)
    return module


def test_whole_schedule_durable_checkpoints_and_no_semantic_retry(runner, monkeypatch):
    with tempfile.TemporaryDirectory(dir=ROOT / "build/evaluation", prefix="closure_v2_qa_") as tmp:
        root = Path(tmp)
        monkeypatch.setattr(runner, "JOURNAL", root / "journal")
        output = root / "run"
        assert runner.run(root, output, max_new_conditions=0)["remaining"] == 84
        assert not (root / "journal").exists()
        manifest_bytes = (output / "manifest.json").read_bytes()
        assert runner.run(root, output, resume=True, max_new_conditions=1)["completed"] == 1
        assert runner.run(root, output, resume=True)["completed"] == 84
        journals = runner.inventory(root / "journal")
        assert runner.run(root, output, resume=True)["new_conditions"] == 0
        assert runner.inventory(root / "journal") == journals
        assert (output / "manifest.json").read_bytes() == manifest_bytes
        report = importlib.import_module("evaluate_phase5_native_observations_v2").evaluate(output)
        assert len(report["observations"]) == 84
        assert report["phase5_accepted"] is False
        # Actual synthetic execution identity rejects native claim.
        assert report["readiness"]["failures"]
        checkpoint = next((output / "conditions").glob("*/completed.json"))
        saved = json.loads(checkpoint.read_text())
        saved["final_answer"] = "tamper"
        checkpoint.write_text(json.dumps(saved))
        with pytest.raises(ValueError, match="checkpoint"):
            runner.run(root, output, resume=True)


def test_started_only_or_source_tamper_cannot_resume(runner, monkeypatch):
    with tempfile.TemporaryDirectory(dir=ROOT / "build/evaluation", prefix="closure_v2_qa_") as tmp:
        root = Path(tmp)
        monkeypatch.setattr(runner, "JOURNAL", root / "journal")
        output = root / "run"
        runner.run(root, output, max_new_conditions=0)
        condition = output / "conditions/c1_read_public__A0"
        condition.mkdir()
        with pytest.raises(ValueError, match="started-only"):
            runner.run(root, output, resume=True)
        condition.rmdir()
        (output / "source_snapshot/scripts/run_phase5_native_closure_v2.py").write_text("tamper")
        with pytest.raises(ValueError, match="artifact"):
            runner.run(root, output, resume=True)


def test_uncertain_journal_blocks_before_any_condition(runner, monkeypatch):
    with tempfile.TemporaryDirectory(dir=ROOT / "build/evaluation", prefix="closure_v2_qa_") as tmp:
        root = Path(tmp)
        journal = root / "journal"
        journal.mkdir()
        (journal / "lost.started.json").write_text("{}")
        monkeypatch.setattr(runner, "JOURNAL", journal)
        with pytest.raises(ValueError, match="unresolved"):
            runner.run(root, root / "run")
        assert not list((root / "run/conditions").iterdir())
