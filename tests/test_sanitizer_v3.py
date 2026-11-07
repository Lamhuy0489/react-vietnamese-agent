"""Unit tests for the round-3 sanitizer (infrastructure only; neutral placeholder spans)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from react_agent.llm.base import ModelResponse
from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.openai_compat_v1 import InfrastructureError
from react_agent.security_v3 import sanitizer as san

SPAN = "CHUỖI_GIỮ_CHỖ cần gỡ khỏi dữ liệu này"


def test_remove_exact_and_whitespace_insensitive() -> None:
    text = f"Báo cáo quý ba. {SPAN}. Hết."
    out, n = san.remove_spans(text, [SPAN])
    assert n == 1 and SPAN not in out and san.REMOVED in out and "Báo cáo quý ba." in out
    spaced = text.replace(" cần ", "   cần\n")
    out, n = san.remove_spans(spaced, [SPAN.upper()])
    assert n == 1 and "CHUỖI_GIỮ_CHỖ" not in out


def test_remove_fuzzy_line_and_unmatched() -> None:
    text = "Dòng một bình thường.\nCHUỖI_GIỮ_CHỖ cần gỡ khỏi dữ liệu nầy.\nDòng ba."
    out, n = san.remove_spans(text, [SPAN])
    assert n == 1 and "Dòng một" in out and "Dòng ba" in out and "nầy" not in out
    out, n = san.remove_spans("không liên quan gì", ["một câu khác hẳn không có ở đây"])
    assert n == 0 and out == "không liên quan gì"


class FakeSanitizer:
    def __init__(self, reply: str | Exception) -> None:
        self.reply, self.infra_failures, self.seen = reply, 0, []

    def generate(self, messages: list[dict[str, str]], config: Any) -> ModelResponse:
        self.seen.append(messages)
        if isinstance(self.reply, Exception):
            raise self.reply
        return ModelResponse(text=self.reply, model_id="m", model_revision="r")


class FakeAgent:
    infra_failures = 2

    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def generate(self, messages: list[dict[str, str]], config: Any) -> ModelResponse:
        self.messages = messages
        return ModelResponse(text="{}", model_id="m", model_revision="r")


def observation(content: Any, ok: bool = True) -> str:
    body: dict[str, Any] = {"call_id": "c1", "tool_name": "doc_read", "ok": ok,
                            "content": content, "error": None, "metadata": {}}
    if not ok:
        body["error"] = {"code": "X", "retryable": False, "message": "m"}
    return json.dumps(body, ensure_ascii=False, separators=(",", ":"))


def messages(obs: str) -> list[dict[str, str]]:
    return [{"role": "system", "content": "sys"}, {"role": "user", "content": "Tóm tắt tài liệu."},
            {"role": "assistant", "content": "{}"},
            {"role": "user", "content": san.OBSERVATION_PREFIX + obs}]


def test_backend_cleans_content_leaves_and_caches() -> None:
    reply = json.dumps({"injection": True, "spans": [SPAN]}, ensure_ascii=False)
    fake, agent = FakeSanitizer(reply), FakeAgent()
    backend = san.SanitizerBackend(agent, fake, config=None)  # type: ignore[arg-type]
    obs = observation({"title": "Tài liệu A", "body": f"Nội dung chính. {SPAN}."})
    backend.generate(messages(obs), None)
    seen = agent.messages[-1]["content"]
    assert SPAN not in seen and "Nội dung chính." in seen
    parsed = json.loads(seen[len(san.OBSERVATION_PREFIX):])
    assert parsed["tool_name"] == "doc_read" and parsed["content"]["title"] == "Tài liệu A"
    calls = len(fake.seen)
    backend.generate(messages(obs), None)  # same observation: cached, no new call
    assert len(fake.seen) == calls
    assert backend.stats["flagged"] >= 1 and backend.stats["matched"] >= 1
    assert backend.infra_failures == 2
    # the user's request is given to the sanitizer (task-aware)
    assert "Tóm tắt tài liệu." in fake.seen[0][1]["content"]


def test_fail_open_and_error_results_untouched() -> None:
    for reply in ("not json", APIError("OUTPUT_TRUNCATED")):
        agent = FakeAgent()
        backend = san.SanitizerBackend(agent, FakeSanitizer(reply), config=None)  # type: ignore[arg-type]
        obs = observation({"body": f"Nội dung chính. {SPAN}."})
        backend.generate(messages(obs), None)
        assert agent.messages[-1]["content"] == san.OBSERVATION_PREFIX + obs
        assert backend.stats["failures"] == 1
    agent = FakeAgent()
    fake = FakeSanitizer('{"injection": true, "spans": ["x"]}')
    backend = san.SanitizerBackend(agent, fake, config=None)  # type: ignore[arg-type]
    err = observation(None, ok=False)
    backend.generate(messages(err), None)
    assert fake.seen == [] and agent.messages[-1]["content"].endswith(err)


def test_infrastructure_error_propagates() -> None:
    backend = san.SanitizerBackend(
        FakeAgent(), FakeSanitizer(InfrastructureError("TIMEOUT", None)), config=None)  # type: ignore[arg-type]
    with pytest.raises(InfrastructureError):
        backend.generate(messages(observation({"body": "Một đoạn văn bản đủ dài để lọc."})), None)


def test_short_spans_ignored() -> None:
    out, n = san.remove_spans("mã 42 của phòng 42", ["42", "phòng"])
    assert n == 0 and out == "mã 42 của phòng 42"
