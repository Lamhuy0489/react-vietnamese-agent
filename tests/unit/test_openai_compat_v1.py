from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.base import GenerationConfig
from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.openai_compat_v1 import InfrastructureError, OpenAICompatBackend

REPO, REV = "Qwen/Qwen3-8B", "abcdef1234567"
SERVED = f"{REPO}@{REV}"


def completion(content: str, finish: str = "stop", model: str = SERVED) -> dict[str, Any]:
    return {"model": model, "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            "choices": [{"finish_reason": finish,
                         "message": {"role": "assistant", "content": content}}]}


class Fake:
    def __init__(self, reply: dict[str, Any] | Exception) -> None:
        self.reply, self.sent = reply, []

    def __call__(self, method: str, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        self.sent.append((method, path, payload))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def backend(reply: dict[str, Any] | Exception) -> tuple[OpenAICompatBackend, Fake]:
    fake = Fake(reply)
    return OpenAICompatBackend(fake, repo=REPO, revision=REV,
                               chat_template_kwargs={"enable_thinking": False}), fake


def test_valid_action_sends_schema_seed_and_request_id() -> None:
    text = json.dumps({"action": {"name": "calculator", "arguments": {"expression": "1+1"}}})
    model, fake = backend(completion(text))
    response = model.generate([{"role": "user", "content": "x"}], GenerationConfig())
    payload = fake.sent[0][2]
    assert payload is not None
    assert response.text == text and response.model_revision == REV
    assert payload["model"] == SERVED and payload["seed"] == 42 and payload["temperature"] == 0
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert model.calls[0]["request_id"] == payload["request_id"]


@pytest.mark.parametrize(("reply", "code"), [
    (completion('{"final_answer": {"answer": "ok"}}', finish="length"), "OUTPUT_TRUNCATED"),
    (completion("not json"), "OUTPUT_INVALID"),
    (completion('{"final_answer": {"answer": ""}}'), "OUTPUT_INVALID"),
    (completion('{"final_answer": {"answer": "ok"}}', model="other@1234567"), "RESPONSE_IDENTITY"),
])
def test_model_failures_are_not_infrastructure(reply: dict[str, Any], code: str) -> None:
    model, _ = backend(reply)
    with pytest.raises(APIError) as caught:
        model.generate([{"role": "user", "content": "x"}], GenerationConfig())
    assert caught.value.code == code and not isinstance(caught.value, InfrastructureError)
    assert model.calls[-1]["error"] == code and model.infra_failures == 0


@pytest.mark.parametrize("error", [APIError("NETWORK_ERROR"), APIError("TIMEOUT"),
                                   APIError("HTTP_ERROR", 502)])
def test_transport_failures_are_infrastructure(error: APIError) -> None:
    model, _ = backend(error)
    with pytest.raises(InfrastructureError):
        model.generate([{"role": "user", "content": "x"}], GenerationConfig())
    assert model.infra_failures == 1


def test_bad_request_is_a_model_side_error() -> None:
    model, _ = backend(APIError("HTTP_ERROR", 400))
    with pytest.raises(APIError) as caught:
        model.generate([{"role": "user", "content": "x"}], GenerationConfig())
    assert not isinstance(caught.value, InfrastructureError)


def test_probe_requires_exact_served_identity() -> None:
    model, _ = backend({"data": [{"id": SERVED}]})
    model.probe()
    other, _ = backend({"data": [{"id": "Qwen/Qwen3-8B@ffffffff"}]})
    with pytest.raises(APIError, match="MODEL_MISMATCH"):
        other.probe()


def test_sampling_and_unpinned_revision_are_rejected() -> None:
    model, _ = backend(completion("{}"))
    with pytest.raises(APIError, match="GREEDY_REQUIRED"):
        model.generate([], GenerationConfig(temperature=0.7))
    with pytest.raises(ValueError):
        OpenAICompatBackend(Fake({}), repo=REPO, revision="")


def test_per_tool_schema_binds_arguments_to_tool() -> None:
    import jsonschema

    from react_agent.llm.openai_compat_v1 import per_tool_schema
    from react_agent.tools.factory import build_smoke_registry

    root = Path(__file__).resolve().parents[2] / "data/smoke"
    schema = per_tool_schema(build_smoke_registry(root).definitions())
    validator = jsonschema.Draft202012Validator(schema)
    ok = {"action": {"arguments": {"page_id": "CACHE_001"}, "name": "cached_fetch"}}
    assert validator.is_valid(ok)
    assert validator.is_valid({"final_answer": {"answer": "x"}})
    assert not validator.is_valid({"action": {"arguments": {}, "name": "calculator"}})
    assert not validator.is_valid(
        {"action": {"arguments": {"doc_id": "CACHE_003"}, "name": "cached_fetch"}})


def test_ordered_transport_keeps_name_before_arguments() -> None:
    import io
    import json as _json

    from react_agent.llm.openai_compat_v1 import OrderedHTTPSJSON, per_tool_schema

    sent: list[bytes] = []

    class Opener:
        def open(self, request, timeout):  # noqa: ANN001, ANN202
            sent.append(request.data)
            response = io.BytesIO(b'{"ok": true}')
            response.status = 200  # type: ignore[attr-defined]
            return response

    transport = OrderedHTTPSJSON("https://example.test/v1", "k" * 40)
    transport._opener = Opener()  # type: ignore[assignment]
    schema = per_tool_schema([{"name": "calculator", "input_schema": {"type": "object"}}])
    assert transport("POST", "/chat/completions", {"schema": schema}) == {"ok": True}
    text = sent[0].decode()
    assert text.index('"name"') < text.index('"arguments"')
    assert _json.loads(text)["schema"] == schema


def test_response_schema_backend_returns_non_agent_json() -> None:
    from react_agent.evaluation.adversarial_v1 import GUARD_SCHEMA
    from react_agent.llm.base import GenerationConfig
    from react_agent.llm.openai_compat_v1 import OpenAICompatBackend

    verdict = '{"risk":"SAFE","labels":[],"confidence":"HIGH"}'

    def transport(method, path, payload):  # noqa: ANN001, ANN202
        assert payload["response_format"]["json_schema"]["name"] == "guard_verdict"
        return {"model": payload["model"], "choices": [
            {"finish_reason": "stop", "message": {"content": verdict}}]}

    backend = OpenAICompatBackend(transport, repo="org/guard", revision="abcdef1",
                                  response_schema=GUARD_SCHEMA)
    reply = backend.generate([{"role": "user", "content": "x"}],
                             GenerationConfig(temperature=0, max_new_tokens=128, seed=42))
    assert reply.text == verdict
