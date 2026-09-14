"""Fresh real-spawn pair/Broker controls on selected public Dev source reads."""

import json
import socket
from pathlib import Path

import pytest
from test_phase5_pair_runtime import SAFE, Factory

from react_agent.agent.state import RuntimeConfig
from react_agent.llm.base import GenerationConfig
from react_agent.llm.guard_diagnostic_backend_v1 import DiagnosticFactory
from react_agent.llm.model_pair_v1 import ModelIdentity
from react_agent.llm.model_pair_v2 import AgentWorkerConfig, ShutdownPair, ShutdownPairConfig
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.resource_pair_runtime_v1 import run_pair_task
from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog, selected_fixtures
from react_agent.validation.guard_diagnostic_audit_v1 import audit as audit_diagnostics
from react_agent.validation.pair_runtime_audit_v3 import audit_task

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "data/adversarial/release_v2"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("public source QA must never access network")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def invoke(path, row, level, actions):
    responses = tuple(json.dumps({"action": a.model_dump()}) for a in actions) + (
        '{"final_answer":{"answer":"Kiểm tra đường đi công cụ đã kết thúc."}}',
    )
    agent = Factory("agent", responses)
    sidecar = path.parent / (path.name + "_diagnostics.jsonl")
    if int(level[1:]) >= 2:
        guard = DiagnosticFactory(Factory("guard", (SAFE,) * 8), sidecar)
        pair = ShutdownPair(
            agent,
            guard,
            ShutdownPairConfig(
                ModelIdentity("agent", "synthetic_v1"),
                ModelIdentity("guard", "synthetic_v1"),
                agent_start_seconds=10,
                guard_start_seconds=10,
                agent_call_seconds=5,
                guard_call_seconds=5,
            ),
        )
        kwargs = {"pair": pair}
    else:
        kwargs = {
            "agent_factory": agent,
            "agent_execution": AgentWorkerConfig(
                "agent",
                "synthetic_v1",
                start_seconds=10,
                call_seconds=5,
            ),
        }
    result = run_pair_task(
        PublicWorkbenchTask(task_id=row.task.task_id, instruction=row.task.instruction),
        output=path,
        registry_factory=lambda: row.registry(
            ROOT / "data/clean/v1_1/environment", path.parent / (path.name + "_environment")
        ),
        security=configuration(level),
        runtime_config=RuntimeConfig(max_steps=len(responses)),
        generation=GenerationConfig(),
        source_catalog=fixture_catalog(row),
        **kwargs,
    )
    assert audit_task(path)["valid"]
    if int(level[1:]) >= 2:
        assert audit_diagnostics(path, sidecar)["valid"]
    metadata = json.loads((path / "runtime/run_metadata.json").read_text())
    assert metadata["runtime_version"] == "security_runtime_v9"
    assert metadata["processing_scope_profile"] == (
        "a4_processing_scope_v4" if int(level[1:]) >= 4 else None
    )
    events = [
        json.loads(line) for line in (path / "runtime/trace_legacy.jsonl").read_text().splitlines()
    ]
    return result, events


@pytest.mark.parametrize("family", ["CAND_LINKMAIL", "CAND_SOURCEBINDING"])
def test_other_selected_document_page_sources_a6(tmp_path, family):
    row = next(
        r for r in selected_fixtures(RELEASE) if r.family_id == family and r.branch == "benign"
    )
    result, events = invoke(tmp_path / "run", row, "A6", [row.overlay.trigger])
    assert result.result.tool_sequence == [row.overlay.trigger.name]
    returned = [e for e in events if e["event"] == "tool_result"]
    assert len(returned) == 1 and returned[0]["data"]["ok"]


@pytest.mark.parametrize("level", [f"A{i}" for i in range(7)])
@pytest.mark.parametrize("family", ["CAND_LINKPAGE", "CAND_QUOTED"])
def test_public_trigger_reaches_broker_with_original_bytes(tmp_path, level, family):
    row = next(
        r for r in selected_fixtures(RELEASE) if r.family_id == family and r.branch == "benign"
    )
    result, events = invoke(tmp_path / "run", row, level, [row.overlay.trigger])
    assert result.result.tool_sequence == [row.overlay.trigger.name]
    returned = [e for e in events if e["event"] == "tool_result"]
    assert len(returned) == 1 and returned[0]["data"]["ok"]
    # Public fixture text stays byte-for-byte in observable tool results, never rewritten.
    expected = row.overlay.base_content + "\n" + row.overlay.benign_text
    content = returned[0]["data"]["content"]
    assert content["content"] == expected


@pytest.mark.parametrize("level", ["A3", "A4", "A5", "A6"])
def test_known_but_unrequested_auxiliary_never_becomes_scope_grant(tmp_path, level):
    row = next(
        r
        for r in selected_fixtures(RELEASE)
        if r.family_id == "CAND_LINKPAGE" and r.branch == "benign"
    )
    identities = [r.identity for r in row.resources.cached_pages]
    outside = next(identity for identity in identities if identity not in row.task.instruction)
    proposal = Action(name="cached_fetch", arguments={"page_id": outside})
    _, events = invoke(tmp_path / "run", row, level, [row.overlay.trigger, proposal])
    returned = [e for e in events if e["event"] == "tool_result" and e["data"]["ok"]]
    assert len(returned) == (2 if level == "A3" else 1)
    if level != "A3":
        scope = [
            json.loads(s)
            for s in (tmp_path / "run/runtime/trace_scope.jsonl").read_text().splitlines()
        ]
        pre = [s for s in scope if s["stage"] == "PRE"]
        assert pre[1]["decision"]["effect"] == "DENY"
        assert pre[1]["decision"]["authorized_by"] == "missing_explicit_resource_anchor"
