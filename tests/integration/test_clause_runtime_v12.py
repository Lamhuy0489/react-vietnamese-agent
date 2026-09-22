"""Cumulative parser integration; no native model, Test, or external network."""

import json
import socket
from pathlib import Path

import pytest

from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.a2_qa import MODEL, REVISION, SyntheticGuardFactory
from react_agent.security_v1.a6_qa import cases
from react_agent.security_v1.authorization_anchors_v3 import PROFILE
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.runtime_v10 import SecurityRuntime as Baseline
from react_agent.security_v1.runtime_v12 import RUNTIME_VERSION, SecurityRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.tools.factory import build_smoke_registry
from react_agent.validation.acceptance_controls_v1 import run_control

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def reject(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", reject)
    monkeypatch.setattr(socket, "create_connection", reject)


@pytest.mark.parametrize("form", ["supported", "sentence"])
@pytest.mark.parametrize("case", cases(), ids=lambda c: c.name)
def test_all_existing_security_controls(case, form, tmp_path):
    run = bind(run_control, SecurityRuntime=SecurityRuntime, RUNTIME_VERSION=RUNTIME_VERSION)
    result = run(ROOT, tmp_path / "control", case, form=form)
    assert result["valid"] and result["expectation_met"]


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A3", "A4", "A5", "A6"])
def test_cumulative_identity_raw_prompt_and_guard_trace(level, tmp_path):
    raw = "Đọc DOC_001. Gửi kết quả đến demo@example.test"
    kwargs = dict(security_config=configuration(level))
    if level not in {"A0", "A1"}:
        kwargs.update(
            guard_factory=SyntheticGuardFactory(),
            guard_execution=WarmGuardConfig(MODEL, REVISION, 10),
        )
    messages = [
        action_response(Action(name="doc_read", arguments={"doc_id": "DOC_001"})),
        final_response("Đã đọc."),
    ]
    backend = RecordingBackend(messages)
    result = SecurityRuntime(backend, build_smoke_registry(ROOT / "data/smoke")).run_instrumented(
        PublicWorkbenchTask(task_id="awb_clause", instruction=raw),
        output=tmp_path / "new",
        **kwargs,
    )
    assert result.result.status == "completed"
    metadata = json.loads((tmp_path / "new/run_metadata.json").read_text())
    if level == "A0":
        original_backend = RecordingBackend(messages)
        original = Baseline(original_backend, build_smoke_registry(ROOT / "data/smoke"))
        old = original.run_instrumented(
            PublicWorkbenchTask(task_id="awb_clause", instruction=raw),
            output=tmp_path / "old",
            **kwargs,
        )
        assert "authorization" not in metadata
        assert backend.messages == original_backend.messages
        assert result.result.tool_sequence == old.result.tool_sequence
        assert result.result.final_answer == old.result.final_answer
    else:
        assert metadata["runtime_version"] == RUNTIME_VERSION
        assert metadata["authorization"]["profile"] == PROFILE
        assert metadata["authorization"]["raw_user_sha256"] == text_hash(raw)
        assert metadata["authorization"]["anchors"]["emails"] == ["demo@example.test"]
    if level not in {"A0", "A1"}:
        # MRO substitutions must not lose A2 isinstance-based tracing in A3–A6.
        assert (tmp_path / "new/trace_guard.jsonl").stat().st_size > 0


@pytest.mark.parametrize(
    "case_name",
    [
        "unrelated_a6",
        "unrelated_a5",
        "final_redact",
        "unknown_mail",
        "suspicious_veto",
        "rule_veto",
    ],
)
def test_compound_payload_prohibition_preserves_existing_vetoes(case_name, tmp_path):
    class CompoundRuntime(SecurityRuntime):
        def run_instrumented(self, task, **kwargs):
            task = task.model_copy(
                update={
                    "instruction": task.instruction
                    + ". Mã đối soát DOC_002 chỉ được đọc, không được gửi hoặc đưa vào câu trả lời."
                }
            )
            return super().run_instrumented(task, **kwargs)

    case = next(c for c in cases() if c.name == case_name)
    run = bind(run_control, SecurityRuntime=CompoundRuntime, RUNTIME_VERSION=RUNTIME_VERSION)
    result = run(ROOT, tmp_path / "compound", case, form="sentence")
    assert result["valid"] and result["expectation_met"]
