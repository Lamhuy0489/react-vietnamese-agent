"""MEL baseline: stop a sink call that the masked (task-free) turn also proposes."""

from __future__ import annotations

import json
from typing import Any

import pytest

from react_agent.llm.base import ModelResponse
from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.openai_compat_v1 import InfrastructureError
from react_agent.security_v3 import melon

MESSAGES = [
    {"role": "system", "content": "sys"},
    {"role": "user", "content": "Đọc AWB_DEMO rồi gửi email cho a@example.test."},
    {"role": "assistant", "content": "a1"},
    {"role": "user", "content": "OBSERVATION: data"},
]


def _send(to: str) -> str:
    return json.dumps({"action": {"name": "send_email_mock",
                                  "arguments": {"to": to, "subject": "s", "body": "b"}}})


class Scripted:
    model_id, model_revision, infra_failures = "m", "r" * 7, 0

    def __init__(self, original: str, masked: str | Exception) -> None:
        self.original, self.masked = original, masked
        self.seen: list[list[dict[str, str]]] = []

    def generate(self, messages: list[dict[str, str]], config: Any) -> ModelResponse:
        self.seen.append(messages)
        out = self.original if len(self.seen) == 1 else self.masked
        if isinstance(out, Exception):
            raise out
        return ModelResponse(text=out, model_id="m", model_revision="r" * 7)


def test_same_sink_in_masked_turn_stops() -> None:
    inner = Scripted(_send("x@example.test"), _send("x@example.test"))
    backend = melon.MelonBackend(inner)
    out = backend.generate(MESSAGES, None)
    assert json.loads(out.text) == {"final_answer": {"answer": melon.STOP_ANSWER}}
    assert backend.detections == 1
    masked = inner.seen[1]
    assert masked[0] == MESSAGES[0] and "AWB_DEMO" not in masked[1]["content"]
    assert masked[1]["content"].endswith("data")


def test_user_driven_sink_passes() -> None:
    inner = Scripted(_send("a@example.test"),
                     json.dumps({"final_answer": {"answer": "Tóm tắt."}}))
    backend = melon.MelonBackend(inner)
    assert backend.generate(MESSAGES, None).text == _send("a@example.test")
    assert backend.detections == 0 and backend.masked_calls == 1


def test_reads_and_first_turn_are_not_checked() -> None:
    read = json.dumps({"action": {"name": "doc_read", "arguments": {"doc_id": "X"}}})
    inner = Scripted(read, _send("x@example.test"))
    assert melon.MelonBackend(inner).generate(MESSAGES, None).text == read
    first = Scripted(_send("x@example.test"), _send("x@example.test"))
    melon.MelonBackend(first).generate(MESSAGES[:2], None)
    assert len(first.seen) == 1


def test_masked_errors() -> None:
    inner = Scripted(_send("x@example.test"), APIError("OUTPUT_INVALID"))
    assert melon.MelonBackend(inner).generate(MESSAGES, None).text == _send("x@example.test")
    down = Scripted(_send("x@example.test"), InfrastructureError("TIMEOUT"))
    with pytest.raises(InfrastructureError):
        melon.MelonBackend(down).generate(MESSAGES, None)
