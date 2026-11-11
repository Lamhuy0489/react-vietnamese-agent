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


def test_probe_accepts_base_plus_adapter() -> None:
    from react_agent.llm.http_diagnostic_v1 import APIError
    from react_agent.llm.secalign_role_v1 import SecAlignInputRoleBackend

    served = "facebook/Meta-SecAlign-8B@fb9b039b45ab4fe5e94517efaaf19f80f4fedda1"

    def transport(ids: list[str]):  # type: ignore[no-untyped-def]
        return lambda method, path, payload: {"data": [{"id": i} for i in ids]}

    ok = SecAlignInputRoleBackend(transport(["meta-llama/Llama-3.1-8B-Instruct@0e9e39f", served]),
                                  repo="facebook/Meta-SecAlign-8B",
                                  revision="fb9b039b45ab4fe5e94517efaaf19f80f4fedda1")
    assert ok.served == served
    ok.probe()
    bad = SecAlignInputRoleBackend(transport(["other@1234567"]), repo="facebook/Meta-SecAlign-8B",
                                   revision="fb9b039b45ab4fe5e94517efaaf19f80f4fedda1")
    with pytest.raises(APIError):
        bad.probe()
