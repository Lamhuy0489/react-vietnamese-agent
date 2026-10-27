"""Current closure runtime error sinks and real mock-tool network interdiction."""
from __future__ import annotations

import json
import smtplib
import socket
import urllib.request
from pathlib import Path

import pytest
from test_phase5_closure_candidate import _run

from react_agent.foundation.runtime_qa import action_response
from react_agent.schemas.agent_output import Action


@pytest.mark.parametrize("mode", ["model_error", "parse_failure", "max_steps"])
def test_closure_error_paths_release_no_unfiltered_answer(tmp_path, mode):
    read = action_response(Action(name="doc_read", arguments={"doc_id": "DOC_CLOSURE_PUBLIC"}))
    responses = {"model_error": [], "parse_failure": ["invalid observable output"],
                 "max_steps": [read] * 4}[mode]
    result, metadata = _run(tmp_path, "c1_read_public", "A6", responses)
    assert result.result.status == mode
    assert not result.result.final_answer
    events = [json.loads(s) for s in
              (tmp_path / "execution/trace_security.jsonl").read_text().splitlines()]
    assert not any(e["event"] == "released_final" for e in events)
    assert not metadata["result"]["final_answer"]


@pytest.mark.parametrize("case", ["c2_email_public", "c3_webhook_public"])
def test_closure_mock_sinks_dispatch_with_network_forbidden(tmp_path, monkeypatch, case):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from run_phase5_native_closure_cpu_admission_v1 import responses

    attempts = []

    def forbidden(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("mock tool attempted real external I/O")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(smtplib, "SMTP", forbidden)
    monkeypatch.setattr(smtplib, "SMTP_SSL", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    result, _ = _run(tmp_path, case, "A1", responses(case))
    assert result.result.status == "completed"
    assert result.result.tool_sequence[-1] == (
        "send_email_mock" if case == "c2_email_public" else "post_webhook_mock")
    assert not attempts
