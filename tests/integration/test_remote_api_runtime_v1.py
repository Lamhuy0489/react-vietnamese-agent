"""Real public runtime + spawned guard + journal, with synthetic transport only."""
import json
import time
from pathlib import Path

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.llm.base import GenerationConfig
from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.session_journal_v1 import SessionJournal
from react_agent.llm.structured_http_v1 import StructuredHTTPBackend
from react_agent.llm.structured_session_factory_v1 import StructuredSessionFactory
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.remote_api_runtime_v1 import RemoteAPIRuntime
from react_agent.security_v1.runtime_v12 import SecurityRuntime
from react_agent.security_v1.warm_guard import WarmGuardBackend, WarmGuardConfig
from react_agent.serving.structured_api_v1 import (
    AGENT_SCHEMA,
    GUARD_SCHEMA,
    PROFILE,
    canonical,
    sha,
)
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]
FILES = {"config.json": {"sha256": "0" * 64, "size": 1}}
REVISION = "sha256:" + sha(canonical(FILES).encode())


class SyntheticFactory(StructuredSessionFactory):
    def __call__(self):
        def transport(method, path, payload):
            common = {"profile": PROFILE, "session_id": self.session_id,
                      "model_revision": self.model_revision}
            if method == "GET":
                return {**common, "source_commit": self.source_commit,
                    "worker_sha256": self.worker_sha256, "role": self.role,
                    "data": [{"id": self.model_id, "object": "model"}],
                    "capabilities": {"json_schema": True}, "model_fingerprint": {"files": FILES}}
            if self.task_id == "awb_hang":
                time.sleep(10)
            schema = GUARD_SCHEMA if self.role == "guard" else AGENT_SCHEMA
            content = '{"risk":"SAFE","labels":[],"confidence":"LOW"}'
            if self.role == "agent":
                content = (action_response(Action(name="calculator",
                    arguments={"expression": "19*4+3"})) if len(payload["messages"]) == 2
                    else final_response("79"))
            return {**common, "model": self.model_id,
                "execution": {"constrained_decoding": True, "seed": payload["seed"],
                              "schema_sha256": sha(canonical(schema).encode())},
                "choices": [{"finish_reason": "stop", "message": {"role": "assistant",
                    "content": content}}]}
        backend = StructuredHTTPBackend(
            SessionJournal(transport, self.journal_root, self.public_identity(), self.task_id),
            model=self.model_id, role=self.role, session_id=self.session_id,
            source_commit=self.source_commit, model_revision=self.model_revision,
            worker_sha256=self.worker_sha256)
        backend.probe()
        return backend


def factory(tmp_path, task_id="awb_remote"):
    return SyntheticFactory(tmp_path, tmp_path / "journal", task_id, "guard", "c", "m", 150,
                            "synthetic", REVISION, "session", "source", "worker")


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A3", "A4", "A5", "A6"])
def test_public_api_matches_existing_runtime_and_labels_cleanup(tmp_path, level):
    task = PublicWorkbenchTask(task_id="awb_remote",
                              instruction="Dùng calculator tính 19*4+3 rồi trả kết quả.")
    responses = [action_response(Action(name="calculator", arguments={"expression": "19*4+3"})),
                 final_response("79")]
    options = {"security_config": configuration(level)}
    if level not in {"A0", "A1"}:
        options.update(guard_factory=factory(tmp_path),
                       guard_execution=WarmGuardConfig("synthetic", REVISION, 10))
    results = []
    for name, cls in (("base", SecurityRuntime), ("remote", RemoteAPIRuntime)):
        runtime = cls(RecordingBackend(responses.copy()), build_smoke_registry(ROOT / "data/smoke"),
                      runtime_config=RuntimeConfig(max_steps=3))
        result = runtime.run_instrumented(task, output=tmp_path / name, **options)
        results.append(result.result.model_dump(exclude={"run_id"}))
    assert results[0] == results[1]
    metadata = json.loads((tmp_path / "remote/run_metadata.json").read_text())
    assert metadata["remote_cancellation_supported"] is False
    if level in {"A0", "A1"}:
        assert metadata["guard_lifecycle_scope"] is None
        assert not (tmp_path / "journal").exists()
    else:
        assert metadata["guard_lifecycle_scope"] == "host_http_process_only"
        assert metadata["guard_closed"]
        assert all(e["reaped"] for e in metadata["guard_lifecycle_events"])
        assert list((tmp_path / "journal").rglob("*.started.json"))


def test_wrong_task_is_rejected_before_worker_or_tool(tmp_path):
    runtime = RemoteAPIRuntime(RecordingBackend([]), build_smoke_registry(ROOT / "data/smoke"))
    task = PublicWorkbenchTask(task_id="awb_remote", instruction="synthetic")
    with pytest.raises(ValueError, match="task-bound"):
        runtime.run_instrumented(task, output=tmp_path / "output",
            security_config=configuration("A2"), guard_factory=factory(tmp_path, "wrong"),
            guard_execution=WarmGuardConfig("synthetic", REVISION))
    assert not (tmp_path / "output").exists() and not (tmp_path / "journal").exists()


def test_killed_http_process_leaves_session_blocked(tmp_path):
    with WarmGuardBackend(factory(tmp_path, "awb_hang"),
                          WarmGuardConfig("synthetic", REVISION, 2)) as worker:
        with pytest.raises(TimeoutError):
            worker.generate([{"role": "user", "content": "synthetic"}],
                            GenerationConfig(max_new_tokens=128))
        assert worker.attempts[-1]["reaped"]
    assert list((tmp_path / "journal").rglob("*.started.json"))
    assert not list((tmp_path / "journal").rglob("*.finished.json"))
    next_task = factory(tmp_path, "awb_next")()
    with pytest.raises(APIError, match="UNCERTAIN"):
        next_task.generate([{"role": "user", "content": "synthetic"}],
                           GenerationConfig(max_new_tokens=128))
    assert len(list((tmp_path / "journal").rglob("*.started.json"))) == 1


class RunnerFactory(SyntheticFactory):
    @classmethod
    def from_directory(cls, directory, journal_root, task_id, role, **kwargs):
        return cls(directory, journal_root, task_id, role, "c", "m", 150,
                   "synthetic", REVISION, "session_" + role, "source", "worker")


def test_exact_seven_level_runner_cpu(tmp_path, monkeypatch):
    import importlib
    import sys
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_remote_api_levels_v1")
    monkeypatch.setattr(runner, "ROOT", ROOT)
    # Output admission remains rooted in repo; use an isolated build location.
    import tempfile
    with tempfile.TemporaryDirectory(dir=ROOT / "build", prefix="remote_cpu_") as temp:
        output = Path(temp) / "build/evaluation/diagnostic"
        monkeypatch.setattr(runner, "ROOT", Path(temp))
        (Path(temp) / "src/react_agent").mkdir(parents=True)
        (Path(temp) / "data").symlink_to(ROOT / "data", target_is_directory=True)
        # Restore only source identity calculation's __file__ to the isolated root.
        script_path = Path(temp) / "runner.py"
        script_path.write_text("synthetic runner identity")
        monkeypatch.setattr(runner, "__file__", str(script_path))
        monkeypatch.setattr(runner, "JOURNAL", Path(temp) / "journal")
        monkeypatch.setattr(runner, "StructuredSessionFactory", RunnerFactory)
        monkeypatch.setattr(sys, "argv", ["runner", "--directory", str(tmp_path),
                                        "--output", str(output)])
        runner.main()
        summary = json.loads((output / "summary.json").read_text())
        assert summary["missing_levels"] == [] and not summary["remote_delivery_uncertain"]
        assert [r["level"] for r in summary["conditions"]] == list(runner.LEVELS)
        assert all(r["status"] == "completed" for r in summary["conditions"])
        assert all(r["agent_attempts"] == 2 for r in summary["conditions"])
        with pytest.raises(ValueError, match="fresh"):
            runner.main()
