"""No network/model: HTTP admission, safe errors and checkpoint recovery controls."""

import importlib
import json
import urllib.error
from pathlib import Path

import pytest

from react_agent.llm.base import GenerationConfig
from react_agent.llm.http_diagnostic_v1 import (
    HTTPSJSON,
    APIError,
    HTTPDiagnosticBackend,
    NoRedirect,
)

MESSAGES = [{"role": "user", "content": "synthetic"}]


class FakeServer:
    def __init__(self, model="model", mount="/mount", text='{"answer":"ok"}'):
        self.model, self.mount, self.text = model, mount, text
        self.requests = []
        self.change = None

    def __call__(self, method, path, payload):
        self.requests.append((method, path, payload))
        if method == "GET":
            return {"data": [{"id": self.model}], "model_path": self.mount,
                    "gpu": "2x Tesla T4", "quantization": "FP16"}
        result = {"model": self.model, "choices": [{"message": {
            "role": "assistant", "content": self.text}, "finish_reason": "stop"}],
            "usage": {"completion_tokens": 12}}
        if self.change:
            self.change(result)
        return result


def backend(server):
    value = HTTPDiagnosticBackend(server, model_id=server.model, expected_mount=server.mount)
    value.probe()
    return value


def test_legacy_contract_is_nonstream_greedy_and_explicitly_unverified():
    server = FakeServer()
    value = backend(server)
    response = value.generate(MESSAGES, GenerationConfig())
    request = server.requests[-1][2]
    assert request["stream"] is False and request["temperature"] == 0
    assert "seed" not in request
    assert response.model_revision.startswith("diagnostic-unverified:")
    assert value.calls[0]["seed_applied"] is False
    assert value.calls[0]["finish_reason_verified"] is False
    assert value.calls[0]["usage_verified"] is False
    assert "content" not in json.dumps(value.calls)


@pytest.mark.parametrize("fault", ["alias", "mount", "metadata"])
def test_model_binding_rejects_wrong_mount_or_changed_server(fault):
    server = FakeServer()
    value = backend(server)
    if fault == "alias":
        server.model = "other"
    elif fault == "mount":
        server.mount = "/other"
    else:
        value.metadata["gpu"] = "other"
    with pytest.raises(APIError):
        value.probe()


@pytest.mark.parametrize("text", [
    "<think>SYNTHETIC_REASONING</think>{}", '```json\n{}\n```',
    '{"x":1,"x":2}', '{"x":NaN}', '[]', "",
])
def test_rejected_output_never_persisted_or_retried(text):
    server = FakeServer(text=text)
    value = backend(server)
    with pytest.raises(APIError):
        value.generate(MESSAGES, GenerationConfig())
    assert len(server.requests) == 2
    assert value.calls[0]["status"] == "ERROR"
    assert "SYNTHETIC_REASONING" not in json.dumps(value.calls)


@pytest.mark.parametrize("field,new", [("model", "wrong"), ("choices", [])])
def test_wrong_response_identity_or_count(field, new):
    server = FakeServer()
    server.change = lambda result: result.update({field: new})
    with pytest.raises(APIError):
        backend(server).generate(MESSAGES, GenerationConfig())


def test_length_stop_and_reasoning_field_are_not_accepted():
    server = FakeServer()
    server.change = lambda r: r["choices"][0].update(finish_reason="length")
    with pytest.raises(APIError, match="OUTPUT_LIMIT"):
        backend(server).generate(MESSAGES, GenerationConfig())
    server.change = lambda r: r["choices"][0]["message"].update(reasoning_content="PRIVATE")
    with pytest.raises(APIError, match="UNSUPPORTED_OUTPUT"):
        backend(server).generate(MESSAGES, GenerationConfig())


def test_probe_and_generation_admission_precede_requests():
    server = FakeServer()
    value = HTTPDiagnosticBackend(server, model_id="model", expected_mount="/mount")
    with pytest.raises(APIError, match="PROBE_REQUIRED"):
        value.generate(MESSAGES, GenerationConfig())
    assert not server.requests
    value.probe()
    with pytest.raises(APIError, match="UNSUPPORTED_GENERATION"):
        value.generate(MESSAGES, GenerationConfig(temperature=0.5))
    with pytest.raises(APIError, match="INVALID_MESSAGES"):
        value.generate([{"role": "tool", "content": "x"}], GenerationConfig())
    assert len(server.requests) == 1


@pytest.mark.parametrize("url", ["http://example.test/v1", "https://u:p@example.test/v1",
    "https://example.test/v1?key=secret", "https://example.test/other"])
def test_bad_urls_and_redirects_are_rejected(url):
    with pytest.raises(ValueError):
        HTTPSJSON(url, "secret")
    with pytest.raises(APIError, match="REDIRECT_REFUSED"):
        NoRedirect().redirect_request(None)


def test_transport_does_not_leak_http_error_body_or_key(monkeypatch):
    client = HTTPSJSON("https://example.test/v1", "PRIVATE_API_KEY")
    def failed(*args, **kwargs):
        raise urllib.error.HTTPError("SECRET_URL", 401, "SECRET_BODY", {}, None)
    monkeypatch.setattr(client._opener, "open", failed)
    with pytest.raises(APIError) as caught:
        client("POST", "/chat/completions", {})
    assert caught.value.status == 401 and str(caught.value) == "HTTP_ERROR"
    assert "PRIVATE" not in repr(client)


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("run_kaggle_http_diagnostic_v1")


def backends(runner):
    values = {}
    for model, mount in runner.MODELS.items():
        server = FakeServer(model, "/kaggle/input/models/" + mount)
        def reply(method, path, payload, server=server, model=model):
            if method == "POST":
                if model == runner.GUARD:
                    content = payload["messages"][1]["content"]
                    risk = "MALICIOUS" if "collector@" in content else "SAFE"
                    server.text = json.dumps({"risk": risk, "labels": [], "confidence": "HIGH"})
                elif len(payload["messages"]) == 2:
                    server.text = '{"action":{"name":"calculator",' \
                                  '"arguments":{"expression":"(17+25)*3"}}}'
                else:
                    server.text = '{"final_answer":{"answer":"126"}}'
            return server(method, path, payload)
        values[model] = HTTPDiagnosticBackend(reply, model_id=model, expected_mount=server.mount)
    return values


def test_real_broker_smoke_and_completed_resume_make_no_new_calls(runner, tmp_path):
    output = tmp_path / "run"
    values = backends(runner)
    first = runner.execute(output, {"source": "v1"}, values, resume=False)
    assert first["diagnostic_passes"] == 5 and first["model_calls"] == 8
    assert all(r["broker_events"] == 3 for r in first["results"][:3])
    untouched = backends(runner)
    assert runner.execute(output, {"source": "v1"}, untouched, resume=True) == first
    assert all(not b.calls and b.metadata is None for b in untouched.values())


def test_resume_rejects_changed_inputs_and_tampered_artifacts(runner, tmp_path):
    output = tmp_path / "run"
    runner.execute(output, {"source": "v1"}, backends(runner), resume=False)
    with pytest.raises(ValueError, match="identity mismatch"):
        runner.execute(output, {"source": "v2"}, backends(runner), resume=True)
    (output / runner.TASKS[0][0] / "result.json").write_text("{}")
    with pytest.raises(ValueError, match="artifact mismatch"):
        runner.execute(output, {"source": "v1"}, backends(runner), resume=True)


def test_partial_started_task_is_not_automatically_replayed(runner, tmp_path):
    output = tmp_path / "run"
    output.mkdir()
    runner.save(output / "declaration.json", {"identity": {}})
    (output / runner.TASKS[0][0]).mkdir()
    values = backends(runner)
    with pytest.raises(ValueError, match="partial started task"):
        runner.execute(output, {}, values, resume=True)
    assert all(b.metadata is None for b in values.values())


def test_semantic_guard_failure_is_completed_and_never_retried(runner, tmp_path):
    output = tmp_path / "run"
    values = backends(runner)
    server = FakeServer(runner.GUARD, "/kaggle/input/models/" + runner.MODELS[runner.GUARD],
                        '{"risk":"SAFE","labels":[],"confidence":"HIGH"}')
    values[runner.GUARD] = backend(server)
    first = runner.execute(output, {}, values, resume=False)
    assert first["diagnostic_passes"] == 4
    assert runner.execute(output, {}, backends(runner), resume=True) == first
