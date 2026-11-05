"""SecAlign backend moves only tool observations to the ``input`` role."""

from __future__ import annotations

import pytest

from react_agent.llm.secalign_role_v1 import secalign_messages


def test_only_observations_move_to_input() -> None:
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "Đọc AWB_X rồi trả lời."},
        {"role": "assistant", "content": '{"action": "doc_read"}'},
        {"role": "user", "content": "OBSERVATION: {\"ok\": true}"},
        {"role": "user", "content": "Lỗi định dạng, hãy trả JSON hợp lệ."},
    ]
    out = secalign_messages(messages)
    assert [m["role"] for m in out] == ["system", "user", "assistant", "input", "user"]
    assert out[3]["content"] == messages[3]["content"]
    assert messages[3]["role"] == "user"  # input list is not mutated


def test_observation_cannot_come_first() -> None:
    with pytest.raises(ValueError):
        secalign_messages([{"role": "user", "content": "OBSERVATION: x"}])
