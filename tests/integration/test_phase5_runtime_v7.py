from __future__ import annotations

import json
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.a2_qa import MODEL, REVISION, SyntheticGuardFactory
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.final_entitlements import EntitlementError
from react_agent.security_v1.final_entitlements_v2 import extract_final_entitlement
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v7 import SecurityRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic runtime QA must not use network")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def run_case(
    output,
    instruction,
    responses,
    *,
    level="A6",
    catalog=None,
    runtime_class=SecurityRuntime,
    entitlement=None,
    max_steps=None,
):
    backend = RecordingBackend(responses)
    runtime = runtime_class(
        backend,
        build_smoke_registry(ROOT / "data/smoke"),
        runtime_config=RuntimeConfig(
            max_steps=max_steps or len(responses), max_format_retries_per_step=0
        ),
    )
    kwargs = {"output": output, "security_config": configuration(level), "source_catalog": catalog}
    if int(level[1:]) >= 2:
        kwargs.update(
            guard_factory=SyntheticGuardFactory(),
            guard_execution=WarmGuardConfig(MODEL, REVISION, 10),
        )
    if entitlement is not None:
        kwargs["entitlement"] = entitlement
    result = runtime.run_instrumented(
        PublicWorkbenchTask(task_id="awb_remediation", instruction=instruction), **kwargs
    )
    metadata = json.loads((output / "run_metadata.json").read_text())
    return result, metadata, backend


def binding(action, source_id, source_type=SourceType.DOCUMENT, trust=Trust.TRUSTED):
    return SourceBinding(
        tool=action.name,
        arguments_json=canonical_json(action.arguments),
        label=SourceLabel(
            source_type=source_type,
            source_id=source_id,
            sensitivity=Sensitivity.CONFIDENTIAL,
            trust=trust,
        ),
    )


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A3", "A4", "A5", "A6"])
@pytest.mark.parametrize("terminal", ["completed", "parse_failure", "max_steps", "model_error"])
def test_all_level_unaffected_replay_parity_and_metadata(tmp_path, level, terminal):
    action = action_response(Action(name="calculator", arguments={"expression": "1+1"}))
    responses = {
        "completed": [action, final_response("Public summary")],
        "parse_failure": [action, "invalid"],
        "max_steps": [action],
        "model_error": [action],
    }[terminal]
    outputs = []
    for name, cls in [("old", V5Runtime), ("new", SecurityRuntime)]:
        outputs.append(
            run_case(
                tmp_path / name,
                "Calculate one plus one",
                responses,
                level=level,
                runtime_class=cls,
                max_steps=1 if terminal == "max_steps" else 2,
            )
        )
    (old, old_meta, old_backend), (new, meta, backend) = outputs
    assert old.result.model_dump(exclude={"run_id"}) == new.result.model_dump(exclude={"run_id"})
    assert old_backend.messages == backend.messages
    assert new.result.status == terminal
    traces = []
    for name in ("old", "new"):
        traces.append(
            [
                {k: v for k, v in json.loads(row).items() if k not in {"run_id", "timestamp"}}
                for row in (tmp_path / name / "trace_legacy.jsonl").read_text().splitlines()
            ]
        )
    assert traces[0] == traces[1]
    assert meta["guard_execution_attempt_count"] == old_meta["guard_execution_attempt_count"]
    assert meta["processing_scope_profile"] == (
        "a4_processing_scope_v2" if level in {"A4", "A5", "A6"} else None
    )
    assert meta["final_policy"] == ("final_entitlement_release_v2" if level == "A6" else None)
    assert (meta["a6_policy_profile"] is not None) == (level == "A6")
    if int(level[1:]) >= 2:
        assert meta["guard_closed"] is True
    if int(level[1:]) >= 3:
        assert meta["session_snapshot_count"] > 0


@pytest.mark.parametrize("level", ["A3", "A4", "A5", "A6"])
def test_a4_scope_denial_is_cumulative_and_never_reaches_broker(tmp_path, level):
    allowed = Action(name="doc_read", arguments={"doc_id": "DOC_001"})
    denied = Action(name="doc_read", arguments={"doc_id": "DOC_002"})
    catalog = SourceCatalog(
        bindings=(binding(allowed, "DOC_001", trust=Trust.UNTRUSTED), binding(denied, "DOC_002"))
    )
    result, metadata, _ = run_case(
        tmp_path / "run",
        "Read DOC_001",
        [action_response(allowed), action_response(denied), final_response("Public summary")],
        level=level,
        catalog=catalog,
    )
    scoped = level != "A3"
    assert result.denied_tool_count == int(scoped)
    assert result.control.tool_call_count == (1 if scoped else 2)
    if scoped:
        rows = [
            json.loads(line)
            for line in (tmp_path / "run/trace_scope.jsonl").read_text().splitlines()
        ]
        assert [row["sequence"] for row in rows] == list(range(1, len(rows) + 1))
        assert rows[-1]["decision"]["effect"] == "DENY"
        assert metadata["processing_scope"]["state"]["observation_count"] == 1


@pytest.mark.parametrize("entitled", [True, False])
def test_actual_database_records_go_through_scope_and_final_gate(tmp_path, entitled):
    action = Action(name="db_query", arguments={"query": "SELECT student_id FROM scholarships"})
    instruction = "Read table scholarships column student_id"
    if entitled:
        instruction += "; Show student ID from table scholarships"
    catalog = SourceCatalog(bindings=(binding(action, "scholarships", SourceType.DATABASE),))
    result, meta, _ = run_case(
        tmp_path / "run",
        instruction,
        [action_response(action), final_response("SV_SYN_001")],
        catalog=catalog,
    )
    assert result.control.tool_call_count == 1
    assert meta["final_release"]["effect"] == ("ALLOW" if entitled else "REDACT")
    assert result.result.final_answer == ("SV_SYN_001" if entitled else "[REDACTED]")
    assert len([r for r in result.artifacts if r.producer == "tool_source_snapshot"]) == 1


def test_forged_supplied_grant_rejected_before_output_or_model(tmp_path):
    instruction = "Show email from DOC_001"
    supplied = extract_final_entitlement(instruction).model_copy(update={"explicit": False})
    with pytest.raises(EntitlementError, match="canonically bound"):
        run_case(tmp_path / "run", instruction, [final_response()], entitlement=supplied)
    assert not (tmp_path / "run").exists()


def test_task_local_scope_does_not_leak_between_runs(tmp_path):
    for index, identity in enumerate(["DOC_001", "DOC_002"]):
        action = Action(name="doc_read", arguments={"doc_id": identity})
        result, meta, _ = run_case(
            tmp_path / str(index),
            f"Read {identity}",
            [action_response(action), final_response()],
            level="A4",
            catalog=SourceCatalog(bindings=(binding(action, identity),)),
        )
        assert result.denied_tool_count == 0
        assert meta["processing_scope"]["anchors"]["documents"] == [identity]


def test_missing_host_resource_mapping_denies_without_crashing(tmp_path):
    action = Action(name="doc_read", arguments={"doc_id": "DOC_001"})
    result, _, _ = run_case(
        tmp_path / "run", "Read DOC_001", [action_response(action), final_response()], level="A4"
    )
    assert result.denied_tool_count == 1
    assert result.control.tool_call_count == 0
    assert result.result.status == "completed"


@pytest.mark.parametrize(
    "sink",
    [
        Action(
            name="send_email_mock",
            arguments={"to": "synthetic@example.test", "subject": "Report", "body": "SV_SYN_001"},
        ),
        Action(
            name="post_webhook_mock",
            arguments={"endpoint": "https://example.test/hook", "payload": {"text": "SV_SYN_001"}},
        ),
    ],
)
def test_actual_private_record_cannot_exit_external_mock(tmp_path, sink):
    action = Action(name="db_query", arguments={"query": "SELECT student_id FROM scholarships"})
    result, _, _ = run_case(
        tmp_path / "run",
        "Read table scholarships column student_id",
        [action_response(action), action_response(sink), final_response("Public summary")],
        catalog=SourceCatalog(bindings=(binding(action, "scholarships", SourceType.DATABASE),)),
    )
    assert result.denied_tool_count == 1
    assert result.control.tool_call_count == 1
    assert result.result.tool_sequence == ["db_query"]


def test_parallel_runtime_instances_keep_separate_scope(tmp_path):
    def execute(identity):
        action = Action(name="doc_read", arguments={"doc_id": identity})
        result, metadata, _ = run_case(
            tmp_path / identity,
            f"Read {identity}",
            [action_response(action), final_response()],
            level="A4",
            catalog=SourceCatalog(bindings=(binding(action, identity),)),
        )
        return result.denied_tool_count, metadata["processing_scope"]["anchors"]["documents"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(execute, ["DOC_001", "DOC_002"])) == [
            (0, ["DOC_001"]),
            (0, ["DOC_002"]),
        ]
