"""P1 spotlighting and P2 sandwich message transforms."""

from __future__ import annotations

from typing import Any

import pytest

from react_agent.security_v3 import prompt_baselines as pb

MESSAGES = [
    {"role": "system", "content": "sys"},
    {"role": "user", "content": "Đọc AWB_DEMO rồi trả lời."},
    {"role": "assistant", "content": '{"action": "doc_read"}'},
    {"role": "user", "content": 'OBSERVATION: {"ok": true, "content": "a b\n c"}'},
    {"role": "user", "content": "Lỗi định dạng, hãy trả JSON hợp lệ."},
]


def test_datamark_marks_only_observations() -> None:
    out = pb.spotlight(MESSAGES, "datamark")
    assert out[0]["content"].startswith("sys") and pb.DATAMARK in out[0]["content"]
    assert out[3]["content"] == 'OBSERVATION: {"ok":ˆtrue,ˆ"content":ˆ"aˆbˆc"}'
    assert out[1] == MESSAGES[1] and out[4] == MESSAGES[4]
    assert MESSAGES[3]["content"].startswith('OBSERVATION: {"ok": true')  # not mutated


def test_delimit_wraps_observation() -> None:
    out = pb.spotlight(MESSAGES, "delimit")
    assert out[3]["content"].startswith(f"OBSERVATION: {pb.OPEN}\n")
    assert out[3]["content"].endswith(f"\n{pb.CLOSE}")


def test_sandwich_repeats_task_after_each_observation() -> None:
    out = pb.sandwich(MESSAGES)
    assert out[3]["content"].endswith("Đọc AWB_DEMO rồi trả lời.")
    assert out[4] == MESSAGES[4] and [m["role"] for m in out] == [m["role"] for m in MESSAGES]


def test_bad_shapes_raise() -> None:
    with pytest.raises(ValueError):
        pb.spotlight(MESSAGES[1:], "datamark")
    with pytest.raises(ValueError):
        pb.sandwich([MESSAGES[0], MESSAGES[3]])
    with pytest.raises(ValueError):
        pb.PromptBaselineBackend(object())


def test_backend_wrapper_delegates() -> None:
    class Inner:
        infra_failures = 2
        seen: list[Any] = []

        def generate(self, messages: list[dict[str, str]], config: Any) -> str:
            self.seen.append(messages)
            return "r"

    inner = Inner()
    backend = pb.PromptBaselineBackend(inner, spotlight_mode="delimit", sandwich=True)
    assert backend.generate(MESSAGES, None) == "r"
    assert backend.infra_failures == 2
    sent = inner.seen[0][3]["content"]
    assert sent.startswith(f"OBSERVATION: {pb.OPEN}") and "Đọc AWB_DEMO" in sent
    assert sent.index(pb.CLOSE) < sent.index("Đọc AWB_DEMO")  # reminder outside the data
    marked = pb.PromptBaselineBackend(inner, spotlight_mode="datamark", sandwich=True)
    marked.generate(MESSAGES, None)
    assert "Đọc AWB_DEMO rồi trả lời." in inner.seen[1][3]["content"]  # reminder unmarked
