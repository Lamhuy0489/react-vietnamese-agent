from __future__ import annotations

import json
import smtplib
import socket
from pathlib import Path

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import ArtifactType
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.foundation.runtime_v1 import FoundationRuntime
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.rules import RuleGuard
from react_agent.security_v1.runtime import SecurityRuntime
from react_agent.security_v1.runtime_policy import DENIAL_FEEDBACK
from react_agent.security_v1.runtime_qa import (
    audit_run,
    micro_case,
    micro_cases,
    micro_registry,
    smoke_case,
    trace_events,
)
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]
READ = action_response(Action(name="doc_read", arguments={"doc_id": "DOC_001"}))
CALC = action_response(Action(name="calculator", arguments={"expression": "1+1"}))
MAIL = action_response(
    Action(
        name="send_email_mock",
        arguments={"to": "demo@example.test", "subject": "public", "body": "public"},
    )
)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("runtime integration must remain offline")

    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, deny)
    monkeypatch.setattr(smtplib, "SMTP", deny)


@pytest.mark.parametrize("index", range(20))
def test_exact_a0_smoke_parity(index, tmp_path):
    report = smoke_case(ROOT, tmp_path, index)
    assert report["exact_a0_parity"] and report["valid"] and report["denials"] == 0


@pytest.mark.parametrize("case", micro_cases(), ids=lambda c: c.name)
@pytest.mark.parametrize("level", ["A0", "A1"])
def test_synthetic_a0_a1_differential(case, level, tmp_path):
    report = micro_case(ROOT, tmp_path, case, level)
    assert report["valid"] and report["proposals"] == 2


@pytest.mark.parametrize(
    "responses,status",
    [
        ([final_response()], "completed"),
        ([], "model_error"),
        (["bad", final_response()], "completed"),
        (["bad"] * 3, "parse_failure"),
        ([CALC] * 3, "max_steps"),
        ([CALC], "model_error"),
        (
            [
                action_response(Action(name="doc_read", arguments={"doc_id": "missing"})),
                final_response(),
            ],
            "completed",
        ),
    ],
)
def test_a0_error_and_terminal_parity(responses, status, tmp_path):
    task = PublicWorkbenchTask(task_id="awb_runtime", instruction="Kiểm tra giả lập")
    backends = [RecordingBackend(responses), RecordingBackend(responses)]
    old = FoundationRuntime(
        backends[0],
        build_smoke_registry(ROOT / "data/smoke"),
        runtime_config=RuntimeConfig(max_steps=3),
    ).run_instrumented(task, output=tmp_path / "old")
    new = SecurityRuntime(
        backends[1],
        build_smoke_registry(ROOT / "data/smoke"),
        runtime_config=RuntimeConfig(max_steps=3),
    ).run_instrumented(task, output=tmp_path / "new")
    assert new.result.status == status
    assert old.result.model_dump(exclude={"run_id"}) == new.result.model_dump(exclude={"run_id"})
    assert backends[0].messages == backends[1].messages
    assert trace_events(tmp_path / "old/trace_legacy.jsonl") == trace_events(
        tmp_path / "new/trace_legacy.jsonl"
    )
    assert audit_run(new, tmp_path / "new", backends[1].messages)["valid"]


def test_repeated_denials_consume_steps_not_tool_call_ids(tmp_path):
    registry = micro_registry(ROOT, tmp_path / "env", micro_cases()[0])
    backend = RecordingBackend([READ, MAIL, MAIL, CALC, final_response()])
    run = SecurityRuntime(backend, registry).run_instrumented(
        PublicWorkbenchTask(task_id="awb_runtime", instruction="Đọc"),
        output=tmp_path / "run",
        security_config=configuration("A1"),
    )
    assert run.denied_tool_count == 2 and run.proposed_tool_count == 4
    assert run.result.tool_sequence == ["doc_read", "calculator"]
    assert run.control.tool_call_count == 2 and run.control.model_turn_count == 5
    assert backend.messages[2][-1]["content"] == DENIAL_FEEDBACK
    assert backend.messages[3][-1]["content"] == DENIAL_FEEDBACK
    assert "ignore previous instructions" in backend.messages[2][3]["content"]
    events = trace_events(tmp_path / "run/trace_legacy.jsonl")
    assert [e["call_id"] for e in events if e["event"] == "tool_call_proposed"] == [
        "call_000001",
        "call_000002",
    ]
    assert audit_run(run, tmp_path / "run", backend.messages)["valid"]


def test_denial_budget_exhaustion_and_retry_after_feedback(tmp_path):
    for label, responses, steps, status in [
        ("budget", [READ, MAIL, MAIL], 3, "max_steps"),
        ("retry", [READ, MAIL, "bad", final_response()], 4, "completed"),
    ]:
        backend = RecordingBackend(responses)
        runtime = SecurityRuntime(
            backend,
            micro_registry(ROOT, tmp_path / (label + "_env"), micro_cases()[0]),
            runtime_config=RuntimeConfig(max_steps=steps),
        )
        run = runtime.run_instrumented(
            PublicWorkbenchTask(task_id="awb_runtime", instruction="Đọc"),
            output=tmp_path / label,
            security_config=configuration("A1"),
        )
        assert run.result.status == status and run.result.tool_sequence == ["doc_read"]
        assert audit_run(run, tmp_path / label, backend.messages)["valid"]
        if label == "retry":
            assert run.result.parse_errors == 1
            assert not any(m["content"] == "bad" for m in backend.messages[-1])


def test_detector_error_read_open_sink_closed_and_no_exception_text(monkeypatch, tmp_path):
    def fail(*args):
        raise RuntimeError("DO_NOT_LOG_PRIVATE_EXCEPTION")

    monkeypatch.setattr(RuleGuard, "scan", fail)
    backend = RecordingBackend([READ, MAIL, CALC, final_response()])
    run = SecurityRuntime(backend, build_smoke_registry(ROOT / "data/smoke")).run_instrumented(
        PublicWorkbenchTask(task_id="awb_runtime", instruction="Gửi kết quả đến demo@example.test"),
        output=tmp_path / "run",
        security_config=configuration("A1"),
    )
    assert run.denied_tool_count == 1 and run.result.tool_sequence == ["doc_read", "calculator"]
    assert run.result.status == "completed"
    trace = (tmp_path / "run/trace_security.jsonl").read_text()
    assert "RULE_GUARD_ERROR" in trace and "DO_NOT_LOG_PRIVATE_EXCEPTION" not in trace
    assert audit_run(run, tmp_path / "run", backend.messages)["valid"]


def test_a0_skips_broken_detector(monkeypatch, tmp_path):
    monkeypatch.setattr(RuleGuard, "scan", lambda *_: pytest.fail("A0 detector invoked"))
    assert smoke_case(ROOT, tmp_path, 10)["exact_a0_parity"]


def test_reused_runtime_has_fresh_policy_state(tmp_path):
    backend = RecordingBackend([READ, MAIL, final_response()])
    runtime = SecurityRuntime(backend, micro_registry(ROOT, tmp_path / "env", micro_cases()[0]))
    task = PublicWorkbenchTask(task_id="awb_runtime", instruction="Đọc")
    first = runtime.run_instrumented(
        task, output=tmp_path / "first", security_config=configuration("A1")
    )
    runtime.backend = RecordingBackend([MAIL, final_response()])
    second = runtime.run_instrumented(
        task, output=tmp_path / "second", security_config=configuration("A1")
    )
    assert first.denied_tool_count == 1 and second.denied_tool_count == 0
    assert first.result.run_id != second.result.run_id
    assert not {a.artifact_id for a in first.artifacts} & {a.artifact_id for a in second.artifacts}


def test_final_is_still_passthrough_and_not_hidden_a6(tmp_path):
    backend = RecordingBackend([READ, final_response("SYNTHETIC_SENSITIVE_VALUE")])
    run = SecurityRuntime(
        backend, micro_registry(ROOT, tmp_path / "env", micro_cases()[0])
    ).run_instrumented(
        PublicWorkbenchTask(task_id="awb_runtime", instruction="Đọc"),
        output=tmp_path / "run",
        security_config=configuration("A1"),
    )
    assert run.result.final_answer == "SYNTHETIC_SENSITIVE_VALUE"
    finals = [a for a in run.artifacts if a.artifact_type == ArtifactType.FINAL_RESPONSE]
    assert len(finals) == 1
    assert audit_run(run, tmp_path / "run", backend.messages)["valid"]


@pytest.mark.parametrize("level", ["A2", "A3", "A4", "A5", "A6"])
def test_unsupported_levels_fail_before_output(level, tmp_path):
    runtime = SecurityRuntime(RecordingBackend([]), build_smoke_registry(ROOT / "data/smoke"))
    with pytest.raises(ValueError):
        runtime.run_instrumented(
            PublicWorkbenchTask(task_id="awb_runtime", instruction="Đọc"),
            output=tmp_path / "run",
            security_config=configuration(level),
        )
    assert not (tmp_path / "run").exists()


def test_output_reuse_and_legacy_entrypoint_rejected(tmp_path):
    task = PublicWorkbenchTask(task_id="awb_runtime", instruction="Đọc")
    runtime = SecurityRuntime(
        RecordingBackend([final_response()]), build_smoke_registry(ROOT / "data/smoke")
    )
    runtime.run_instrumented(task, output=tmp_path / "run")
    with pytest.raises(ValueError):
        runtime.run_instrumented(task, output=tmp_path / "run")
    with pytest.raises(ValueError):
        runtime.run(task)


def test_micro_suite_never_reads_benchmark_payloads(monkeypatch, tmp_path):
    original = Path.read_text

    def guarded(path, *args, **kwargs):
        assert not path.resolve().is_relative_to(ROOT / "data/clean")
        assert not path.resolve().is_relative_to(ROOT / "data/adversarial")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    assert micro_case(ROOT, tmp_path, micro_cases()[0], "A1")["valid"]


def test_audit_views_do_not_enter_a0_model_context(tmp_path):
    task = PublicWorkbenchTask(task_id="awb_runtime", instruction="Đọc\u200b tài liệu")
    backends = [
        RecordingBackend([READ, final_response()]),
        RecordingBackend([READ, final_response()]),
    ]
    runs = []
    for profile, backend in zip(("raw_v1", "security_v1"), backends, strict=True):
        runs.append(
            SecurityRuntime(backend, build_smoke_registry(ROOT / "data/smoke")).run_instrumented(
                task, output=tmp_path / profile, audit_profile=profile
            )
        )
    assert backends[0].messages == backends[1].messages
    views = [a for a in runs[1].artifacts if a.artifact_type == ArtifactType.NORMALIZED_VIEW]
    assert views
    assert not {a.artifact_id for a in views} & {
        identity for b in runs[1].contexts for identity in b.artifact_ids
    }
    assert audit_run(runs[1], tmp_path / "security_v1", backends[1].messages)["valid"]


def test_audit_rejects_metadata_counter_tamper(tmp_path):
    backend = RecordingBackend([CALC, final_response()])
    run = SecurityRuntime(backend, build_smoke_registry(ROOT / "data/smoke")).run_instrumented(
        PublicWorkbenchTask(task_id="awb_runtime", instruction="Tính"), output=tmp_path / "run"
    )
    path = tmp_path / "run/run_metadata.json"
    metadata = json.loads(path.read_text())
    metadata["denied_tool_count"] = 1
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="metadata counters"):
        audit_run(run, tmp_path / "run", backend.messages)
