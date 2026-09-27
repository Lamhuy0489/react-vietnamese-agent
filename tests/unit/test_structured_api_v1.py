"""Serving contract checks use no GPU, credentials or remote model."""

import importlib
import json
from pathlib import Path

import pytest

from react_agent.llm.base import GenerationConfig
from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.structured_http_v1 import StructuredHTTPBackend
from react_agent.serving.structured_api_v1 import (
    AGENT_SCHEMA,
    GUARD_SCHEMA,
    PROFILE,
    Service,
    ServiceError,
    admit,
    canonical,
    json_object,
    sha,
)


def body(**updates):
    return {"model": "test", "messages": [{"role": "user", "content": "synthetic"}],
            "request_id": "once", **updates}


@pytest.mark.parametrize("role,expected,budget", [("agent", AGENT_SCHEMA, 512),
                                                ("guard", GUARD_SCHEMA, 128)])
def test_role_defaults(role, expected, budget):
    spec = admit(body(), role, "test")
    assert spec.schema == expected and spec.max_tokens == budget and spec.seed == 42


@pytest.mark.parametrize("update", [
    {"model": "wrong"}, {"stream": True}, {"temperature": 0.7}, {"max_tokens": 0},
    {"max_tokens": True}, {"max_tokens": 1025}, {"seed": -1}, {"seed": True},
    {"messages": []}, {"messages": [{"role": "tool", "content": "x"}]},
    {"request_id": "../x"}, {"top_p": 0.9},
])
def test_no_silent_parameter_ignoring(update):
    with pytest.raises(ServiceError):
        admit(body(**update), "agent", "test")


@pytest.mark.parametrize("raw", ['{"x":1,"x":2}', '{"x":NaN}', '[]'])
def test_ambiguous_json_rejected(raw):
    with pytest.raises(ValueError):
        json_object(raw)


class Fake:
    def __init__(self, fail=False):
        self.calls, self.fail = 0, fail

    def generate(self, spec):
        self.calls += 1
        if self.fail:
            raise RuntimeError("SYNTHETIC_PRIVATE_ERROR")
        return {"request": spec.request_id}


@pytest.mark.parametrize("fail", [False, True])
def test_idempotency_including_failed_generation(fail):
    engine = Fake(fail)
    service = Service({"role": "agent", "model": "test"}, engine, "synthetic-key")
    first = service.complete(body())
    assert service.complete(body()) == first and engine.calls == 1
    assert "SYNTHETIC_PRIVATE_ERROR" not in json.dumps(first)
    with pytest.raises(ServiceError, match="REQUEST_ID_CONFLICT"):
        service.complete(body(seed=7))


def test_busy_request_does_not_start_generation():
    engine = Fake()
    service = Service({"role": "guard", "model": "test"}, engine, "synthetic-key")
    service.lock.acquire()
    try:
        with pytest.raises(ServiceError, match="BUSY"):
            service.complete(body())
    finally:
        service.lock.release()
    assert engine.calls == 0


def test_authentication_and_guard_budget():
    service = Service({"role": "guard", "model": "test"}, Fake(), "synthetic-key")
    assert service.authorized("Bearer synthetic-key")
    assert not service.authorized("Bearer other")
    with pytest.raises(ServiceError):
        admit(body(max_tokens=129), "guard", "test")


def client(role, fault=None):
    files = {"config.json": {"sha256": "0" * 64, "size": 10}}
    revision = "sha256:" + sha(canonical(files).encode())
    common = {"profile": PROFILE, "session_id": "session", "model_revision": revision}
    def transport(method, path, payload):
        if method == "GET":
            return {**common, "source_commit": "commit", "worker_sha256": "worker",
                "role": role, "data": [{"id": role, "object": "model"}],
                "capabilities": {"json_schema": True}, "model_fingerprint": {"files": files}}
        schema = GUARD_SCHEMA if role == "guard" else AGENT_SCHEMA
        if role == "guard":
            value = {"risk": "SAFE", "labels": [], "confidence": "HIGH"}
        elif len(payload["messages"]) == 2:
            value = {"action": {"name": "calculator", "arguments": {"expression": "23*7+5"}}}
        else:
            value = {"final_answer": {"answer": "166"}}
        result = {**common, "model": role, "execution": {"constrained_decoding": True,
            "schema_sha256": sha(canonical(schema).encode()), "seed": payload["seed"]},
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant",
                                                                   "content": json.dumps(value)}}]}
        if fault:
            fault(result)
        return result
    return StructuredHTTPBackend(transport, model=role, role=role, session_id="session",
        source_commit="commit", worker_sha256="worker", model_revision=revision)


@pytest.mark.parametrize("fault", [
    lambda r: r.update(session_id="wrong"),
    lambda r: r["execution"].update(constrained_decoding=False),
    lambda r: r["choices"][0]["message"].update(content='{"final_answer":{"answer":166}}'),
    lambda r: r["choices"][0]["message"].update(reasoning="SYNTHETIC_REASONING"),
])
def test_client_rejects_false_server_claims_and_schema(fault):
    backend = client("agent", fault)
    backend.probe()
    with pytest.raises(APIError):
        backend.generate([{"role": "user", "content": "test"}], GenerationConfig())
    assert backend.attempts == 1 and not backend.calls


def test_paired_host_flow_with_actual_broker(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    runner = importlib.import_module("run_structured_pair_smoke_v1")
    agent, guard = client("agent"), client("guard")
    agent.probe()
    guard.probe()
    result = runner.run(agent, guard, tmp_path)
    assert result["diagnostic_pass"] and result["final_answer"] == "166"
    assert result["agent_attempts"] == result["guard_attempts"] == 2
    assert len(result["broker_events"]) == 3
