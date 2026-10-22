"""Public runtime differential: only FINAL changes; no native calls in these tests."""
import importlib
import json
from pathlib import Path

import pytest
from test_remote_api_runtime_v1 import RunnerFactory

from react_agent.agent.state import RuntimeConfig
from react_agent.llm.replay import ReplayBackend
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.encoded_final_runtime_v1 import EncodedFinalRuntime
from react_agent.security_v1.remote_api_runtime_v1 import RemoteAPIRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("case", ["literal_safe", "literal_private", "base64_safe",
                                 "base64_private",
                                 "email_safe", "email_private"])
def test_final_only_correction_preserves_tool_gates_and_raw_release(tmp_path, monkeypatch, case):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_remote_gate_controls_v1")
    task, catalog, responses = runner.fixture(case)
    records = []
    for name, cls in (("baseline", RemoteAPIRuntime), ("candidate", EncodedFinalRuntime)):
        folder = tmp_path / name
        runner.environment(folder / "environment")
        guard = RunnerFactory.from_directory(folder, folder / "journal", task.task_id, "guard")
        runtime = cls(ReplayBackend(responses), build_smoke_registry(folder / "environment"),
                       runtime_config=RuntimeConfig(max_steps=4, max_format_retries_per_step=0))
        runtime.run_instrumented(task, output=folder / "execution", source_catalog=catalog,
            security_config=configuration("A6"), guard_factory=guard,
            guard_execution=WarmGuardConfig(guard.model_id, guard.model_revision, 10))
        meta = json.loads((folder / "execution/run_metadata.json").read_text())
        trace = [json.loads(line) for line in (folder / "execution/trace_security.jsonl")
                 .read_text().splitlines()]
        decisions = [json.loads(row["data_json"]) for row in trace if row["event"] == "decision"]
        # Compare policy behavior independent of generated run/artifact identifiers.
        gates = [(d["stage"], d["effect"], d["reasons"], d["component"])
                 for d in decisions if d["stage"] != "FINAL"]
        records.append((meta, gates))
    old, new = records
    assert old[1] == new[1]
    assert old[0]["guard_execution_attempt_count"] == new[0]["guard_execution_attempt_count"]
    assert old[0]["denied_tool_count"] == new[0]["denied_tool_count"]
    if case == "base64_private":
        assert old[0]["final_release"]["effect"] == "ALLOW"
        assert new[0]["final_release"]["effect"] == "DENY"
        assert new[0]["result"]["final_answer"] == ""
    else:
        assert old[0]["result"]["final_answer"] == new[0]["result"]["final_answer"]
        assert old[0]["final_release"]["effect"] == new[0]["final_release"]["effect"]
    evidence = json.loads((tmp_path / "candidate/execution/encoded_final_screen.json").read_text())
    assert bool(evidence["records"][0]["encoded_matches"]) == (case == "base64_private")


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A3", "A4", "A5"])
def test_non_a6_behavior_is_unchanged(tmp_path, monkeypatch, level):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    runner = importlib.import_module("run_remote_gate_controls_v1")
    task, catalog, responses = runner.fixture("base64_private")
    results = []
    for name, cls in (("baseline", RemoteAPIRuntime), ("candidate", EncodedFinalRuntime)):
        folder = tmp_path / name
        runner.environment(folder / "environment")
        guard = (RunnerFactory.from_directory(folder, folder / "journal", task.task_id, "guard")
                 if level not in {"A0", "A1"} else None)
        result = cls(ReplayBackend(responses), build_smoke_registry(folder / "environment"),
            runtime_config=RuntimeConfig(max_steps=4)).run_instrumented(task,
                output=folder / "execution", source_catalog=catalog,
                security_config=configuration(level), guard_factory=guard,
                guard_execution=WarmGuardConfig(guard.model_id, guard.model_revision, 10)
                if guard else None)
        results.append(result.result.model_dump(exclude={"run_id"}))
        assert not (folder / "execution/encoded_final_screen.json").exists()
    assert results[0] == results[1]
