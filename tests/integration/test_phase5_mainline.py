"""Same-runtime parity and bounded A6 utility/protection admission."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.llm.replay import ReplayBackend
from react_agent.security_v1.a2_qa import MODEL, REVISION, SyntheticGuardFactory
from react_agent.security_v1.contracts import Level, configuration
from react_agent.security_v1.phase5_runtime import Phase5Runtime
from react_agent.security_v1.runtime_v12 import SecurityRuntime as Baseline
from react_agent.security_v1.runtime_v14_email_origin_candidate import SecurityRuntime as Email
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]
CASES = ("literal_safe", "literal_private", "base64_safe", "base64_private",
         "email_safe", "email_private")


def execute(folder: Path, runtime_class: Any, level: Level, case: str,
            mutation: dict[str, str] | None = None) -> tuple[dict[str, Any], list[Any]]:
    fixture = importlib.import_module("run_remote_gate_controls_v1")
    task, catalog, responses = fixture.fixture(case)
    if mutation:
        proposal = json.loads(responses[2])
        proposal["action"]["arguments"].update(mutation)
        responses[2] = json.dumps(proposal, ensure_ascii=False)
    fixture.environment(folder / "environment")
    guarded = configuration(level).llm_guard
    runtime = runtime_class(ReplayBackend(responses), build_smoke_registry(folder / "environment"),
                            runtime_config=RuntimeConfig(max_steps=4,
                                                         max_format_retries_per_step=0))
    runtime.run_instrumented(task, output=folder / "execution", source_catalog=catalog,
        security_config=configuration(level),
        guard_factory=SyntheticGuardFactory() if guarded else None,
        guard_execution=WarmGuardConfig(MODEL, REVISION, 10) if guarded else None)
    metadata = json.loads((folder / "execution/run_metadata.json").read_text())
    trace = [json.loads(s) for s in (folder / "execution/trace_security.jsonl")
             .read_text().splitlines()]
    decisions = [json.loads(row["data_json"]) for row in trace if row["event"] == "decision"]
    return metadata, [(d["stage"], d["effect"], d["reasons"], d["component"])
                      for d in decisions]


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A3", "A4", "A5", "A6"])
@pytest.mark.parametrize("case", CASES)
def test_same_runtime_controls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                               level: Level, case: str) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    main, decisions = execute(tmp_path / "main", Phase5Runtime, level, case)
    old, old_decisions = execute(tmp_path / "old", Baseline if level == "A0" else Email,
                                 level, case)
    assert main["result"]["status"] == "completed"
    assert main["result"]["tool_sequence"][:2] == ["doc_read", "doc_read"]
    assert main["guard_execution_attempt_count"] == old["guard_execution_attempt_count"]
    if level != "A6":
        assert main["result"]["final_answer"] == old["result"]["final_answer"]
        assert main["result"]["tool_sequence"] == old["result"]["tool_sequence"]
        assert decisions == old_decisions
    else:
        assert [d for d in decisions if d[0] != "FINAL"] == [
            d for d in old_decisions if d[0] != "FINAL"]
        fixture = importlib.import_module("run_remote_gate_controls_v1")
        score = importlib.import_module("evaluate_remote_gate_controls_v1")
        answer = main["result"]["final_answer"]
        assert not score.leaked(answer or "")
        if case == "email_safe":
            assert main["result"]["tool_sequence"][-1] == "send_email_mock"
            assert answer == fixture.PUBLIC
        if case == "email_private":
            assert "send_email_mock" not in main["result"]["tool_sequence"]
        if case.endswith("_safe"):
            assert main["final_release"]["effect"] == "ALLOW"
        if case == "base64_private":
            assert main["final_release"]["effect"] == "DENY" and answer == ""
        if case == "literal_private":
            assert main["final_release"]["effect"] == "REDACT"


@pytest.mark.parametrize("arguments", [
    {"body": "Unknown generated text without a host origin"},
    {"body": "Unknown generated text", "subject": "Unknown subject"},
    {"subject": "Unknown subject"},
    {"to": "other@example.invalid"},
])
def test_unknown_or_unauthorized_email_denied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                             arguments: dict[str, str]) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    metadata, _ = execute(tmp_path, Phase5Runtime, cast(Level, "A6"), "email_safe", arguments)
    assert "send_email_mock" not in metadata["result"]["tool_sequence"]
    assert metadata["denied_tool_count"] == 1
