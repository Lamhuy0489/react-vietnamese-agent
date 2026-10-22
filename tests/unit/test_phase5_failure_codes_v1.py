"""Match real worker envelopes, reject altered identities and unknown responses."""
from __future__ import annotations

import importlib
from typing import Any

import pytest

from react_agent.serving.quiescent_engine_v3 import EngineOutcome
from react_agent.serving.request_http_v3 import QuiescentHTTP
from react_agent.serving.structured_api_v1 import canonical, sha


@pytest.fixture
def classify(monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("audit_phase5_failure_codes_v1").classify


def records(tmp_path, code: str) -> tuple[dict[str, Any], dict[str, Any]]:
    def engine(spec: Any, stop: Any) -> EngineOutcome:
        return EngineOutcome({"error": {"code": code}}, 422, True, True)

    app = QuiescentHTTP(api_key="x" * 32, identity={
        "session_id": "synthetic", "source_commit": "a" * 40,
        "worker_sha256": "b" * 64, "model_revision": "sha256:" + "c" * 64,
    }, role="agent", model="synthetic", root=tmp_path, engine=engine)
    body = {"model": "synthetic", "request_id": "request-one",
            "messages": [{"role": "user", "content": "synthetic input"}]}
    identity = dict(app._identity)
    response, status = app.dispatch("POST", "/v1/chat/completions", "Bearer " + "x" * 32,
                                    identity["instance_id"], canonical(body).encode())
    started = {"state": "started", "protocol": "react-vn-request-worker-journal-v1",
               "identity": identity, "request_id": body["request_id"],
               "request_sha256": sha(canonical(body).encode()), "task_id": "synthetic-task"}
    finished = {**started, "state": "response_received", "http_status": status,
                "response_sha256": sha(canonical(response).encode())}
    return started, finished


@pytest.mark.parametrize("code", ["OUTPUT_SCHEMA_FAILED", "OUTPUT_LIMIT"])
def test_real_worker_error_envelope_matches(tmp_path, classify, code):
    started, finished = records(tmp_path, code)
    assert classify(started, finished) == code


def test_unrecognized_code_stays_unknown(tmp_path, classify):
    assert classify(*records(tmp_path, "UNREVIEWED_ERROR")) is None


def test_changed_response_hash_stays_unknown(tmp_path, classify):
    started, finished = records(tmp_path, "OUTPUT_SCHEMA_FAILED")
    finished["response_sha256"] = "0" * 64
    assert classify(started, finished) is None


@pytest.mark.parametrize("field,value", [
    ("state", "uncertain"), ("http_status", 200), ("request_id", "another"),
    ("request_sha256", "0" * 64), ("task_id", "another"), ("identity", {}),
])
def test_mismatched_or_unresolved_records_rejected(tmp_path, classify, field, value):
    started, finished = records(tmp_path, "OUTPUT_SCHEMA_FAILED")
    finished[field] = value
    with pytest.raises(ValueError, match="inconsistent"):
        classify(started, finished)
