"""Offline transport controls; no benchmark input or inference."""
import json

import pytest

from react_agent.llm.base import GenerationConfig
from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.structured_plan_http_v1 import StructuredPlanHTTPBackend, plan_schema
from react_agent.serving.structured_api_v1 import PROFILE, admit, canonical, sha

validate = pytest.importorskip("jsonschema").validate

PLAN = {"refs": [{"run_id": "synthetic", "grant_sha256": "0" * 64,
                 "artifact_id": "public", "source_sha256": "1" * 64, "path": "/content"}]}


def client(fault=None, role="agent", from_messages=False):
    files = {"config.json": {"sha256": "0" * 64, "size": 10}}
    revision = "sha256:" + sha(canonical(files).encode())
    requests = []
    def transport(method, path, payload):
        common = {"profile": PROFILE, "session_id": "session", "model_revision": revision}
        if method == "GET":
            return {**common, "source_commit": "commit", "worker_sha256": "worker",
                    "role": role, "data": [{"id": "model", "object": "model"}],
                    "capabilities": {"json_schema": True}, "model_fingerprint": {"files": files}}
        requests.append(payload)
        spec = admit(payload, role, "model")
        value = PLAN
        if from_messages:
            envelope = json.loads(payload["messages"][1]["content"])
            value = {"refs": [envelope["untrusted_observations"][0]["references"][0]]}
        validate(value, spec.schema)
        result = {**common, "model": "model", "execution": {"constrained_decoding": True,
                  "schema_sha256": sha(canonical(spec.schema).encode()), "seed": spec.seed},
                  "choices": [{"finish_reason": "stop", "message": {
                      "role": "assistant", "content": json.dumps(value)}}]}
        if fault:
            fault(result)
        return result
    return StructuredPlanHTTPBackend(transport, model="model", role=role, session_id="session",
        source_commit="commit", worker_sha256="worker", model_revision=revision), requests


def test_worker_admits_inline_plan_and_records_schema_identity():
    backend, requests = client()
    backend.probe()
    result = backend.generate([{"role": "user", "content": "synthetic"}], GenerationConfig())
    assert json.loads(result.text) == PLAN
    assert '"$ref"' not in canonical(plan_schema())
    assert len(requests) == len(backend.calls) == backend.attempts == 1
    assert backend.calls[0]["execution"]["schema_sha256"] == sha(canonical(plan_schema()).encode())


@pytest.mark.parametrize("fault", [
    lambda r: r.update(session_id="wrong"),
    lambda r: r["execution"].update(schema_sha256="wrong"),
    lambda r: r["execution"].update(seed=0),
    lambda r: r["choices"][0].update(finish_reason="length"),
    lambda r: r["choices"][0]["message"].update(reasoning="do not save"),
    lambda r: r["choices"][0]["message"].update(content='{"refs":[],"refs":[]}'),
    lambda r: r["choices"][0]["message"].update(content='{"final_answer":{"answer":"x"}}'),
    lambda r: r["choices"][0]["message"].update(content=json.dumps({**PLAN,"allowed":True})),
])
def test_invalid_proposal_is_terminal_without_retry(fault):
    backend, requests = client(fault)
    backend.probe()
    with pytest.raises(APIError):
        backend.generate([{"role": "user", "content": "synthetic"}], GenerationConfig())
    assert len(requests) == backend.attempts == 1 and backend.calls == []


def test_probe_role_and_budget_before_post():
    backend, requests = client()
    with pytest.raises(APIError, match="PROBE_REQUIRED"):
        backend.generate([], GenerationConfig())
    backend.probe()
    for config in (GenerationConfig(temperature=1), GenerationConfig(max_new_tokens=1025)):
        with pytest.raises(APIError, match="BOUNDS"):
            backend.generate([], config)
    assert not requests and backend.attempts == 0
    guard, _ = client(role="guard")
    with pytest.raises(APIError, match="AGENT_REQUIRED"):
        guard.probe()


@pytest.mark.parametrize("risk,allowed", [("SAFE", True), ("MALICIOUS", False)])
def test_diagnostic_uses_broker_and_host_veto(tmp_path, monkeypatch, risk, allowed):
    from pathlib import Path

    from react_agent.llm.base import ModelResponse
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from run_structured_plan_diagnostic_v1 import run

    class Guard:
        model_id = "synthetic-guard"
        model_revision = "synthetic-revision"
        attempts = 0
        calls = []
        def generate(self, messages, config):
            self.attempts += 1
            assert config.max_new_tokens == 128
            return ModelResponse(text=json.dumps({"risk": risk, "labels": [], "confidence": "LOW"}),
                                 model_id=self.model_id, model_revision=self.model_revision)
    agent, _ = client(from_messages=True)
    agent.probe()
    result = run(agent, Guard(), tmp_path)
    assert result["bridge"]["decision"]["allowed"] is allowed
    assert result["agent_attempts"] == result["guard_attempts"] == 1
    assert result["broker_event_count"] == 9
    assert (tmp_path / "started.json").exists() and (tmp_path / "result.json").exists()
    assert not result["phase5_accepted"]
