"""Offline controls for request-worker v3 host transport/journal wiring."""
from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.base import GenerationConfig
from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.request_worker_journal_v1 import RequestWorkerJournal
from react_agent.llm.request_worker_runtime_v1 import RequestWorkerBackend
from react_agent.llm.request_worker_transport_v1 import RequestWorkerHTTPS
from react_agent.serving.structured_api_v1 import AGENT_SCHEMA, PROFILE, canonical, sha

IDENTITY = {"instance_id": "boot1", "session_id": "session", "source_commit": "a" * 40,
            "worker_sha256": "b" * 64, "model_revision": "sha256:" + "c" * 64,
            "model_id": "synthetic", "role": "agent"}
EXPECTED = {key: value for key, value in IDENTITY.items() if key != "instance_id"}
PAYLOAD = {"model": "synthetic", "request_id": "r1",
           "messages": [{"role": "user", "content": "synthetic"}]}


def result() -> dict[str, Any]:
    return {"profile": PROFILE, "model": "synthetic", "model_revision": IDENTITY["model_revision"],
            "session_id": IDENTITY["session_id"],
            "choices": [{"message": {"role": "assistant",
                                       "content": '{"final_answer":{"answer":"ok"}}'},
                         "finish_reason": "stop"}],
            "execution": {"constrained_decoding": True,
                          "schema_sha256": sha(canonical(AGENT_SCHEMA).encode()), "seed": 42}}


class FakeWorker:
    def __init__(self, *, fail_post: bool = False, bad_status: bool = False) -> None:
        self.identity = dict(IDENTITY)
        self.fail_post, self.bad_status = fail_post, bad_status
        self.posts = 0
        self.status_calls = 0
        self.cached = result()

    def _envelope(self, payload: dict[str, Any]) -> dict[str, Any]:
        digest = sha(canonical(payload).encode())
        code = 200
        status = {"instance_id": "boot1", "request_id": payload["request_id"],
                  "request_sha256": digest, "state": "SUCCEEDED", "engine_returned": True,
                  "engine_active": False, "gpu_quiescence_attested": True,
                  "quiescence_basis": "device_synchronize", "durable": True,
                  "instance_retired": False, "http_status": code,
                  "cancel_requested": False,
                  "response_sha256": sha(canonical(self.cached).encode())}
        return {"identity": dict(IDENTITY), "result": dict(self.cached), "request": status}

    def exchange(self, method: str, path: str, payload: dict[str, Any] | None) -> Any:
        if method == "POST" and path == "/chat/completions":
            self.posts += 1
            if self.fail_post and self.posts == 1:
                raise APIError("NETWORK_ERROR")
            assert payload is not None
            return type("Exchange", (), {"status": 200, "payload": self._envelope(payload)})()
        if method == "GET" and path == "/requests/r1":
            self.status_calls += 1
            envelope = self._envelope(PAYLOAD)
            if self.bad_status:
                envelope["request"]["request_sha256"] = "f" * 64
            return type("Exchange", (), {"status": 200,
                "payload": {"identity": dict(IDENTITY), "request": envelope["request"]}})()
        raise AssertionError((method, path, payload))

    def __call__(self, method: str, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        value = self.exchange(method, path, payload).payload
        assert isinstance(value, dict)
        return value


def test_journal_success_is_immutable_and_duplicate_uses_cached_memory(tmp_path: Path) -> None:
    worker = FakeWorker()
    journal = RequestWorkerJournal(worker, tmp_path, "task")
    first = journal("POST", "/chat/completions", PAYLOAD)
    second = journal("POST", "/chat/completions", PAYLOAD)
    assert first == second and worker.posts == 1
    finished = next(journal.root.glob("*.finished.json"))
    saved = json.loads(finished.read_text())
    assert saved["state"] == "response_received"
    assert "messages" not in finished.read_text() and "content" not in finished.read_text()


def test_uncertain_attempt_requires_explicit_terminal_cached_recovery(tmp_path: Path) -> None:
    worker = FakeWorker(fail_post=True)
    journal = RequestWorkerJournal(worker, tmp_path, "task")
    with pytest.raises(APIError, match="NETWORK_ERROR"):
        journal("POST", "/chat/completions", PAYLOAD)
    with pytest.raises(APIError, match="SESSION_UNCERTAIN"):
        RequestWorkerJournal(worker, tmp_path, "next")("POST", "/chat/completions", PAYLOAD)
    worker.fail_post = False
    recovered = RequestWorkerJournal(worker, tmp_path, "recover").recover_cached(PAYLOAD)
    assert recovered["request"]["request_sha256"] == sha(canonical(PAYLOAD).encode())
    assert worker.status_calls == 1 and worker.posts == 2


def test_recovery_rejects_status_hash_mismatch_without_post(tmp_path: Path) -> None:
    worker = FakeWorker(fail_post=True, bad_status=True)
    journal = RequestWorkerJournal(worker, tmp_path, "task")
    with pytest.raises(APIError):
        journal("POST", "/chat/completions", PAYLOAD)
    worker.fail_post = False
    with pytest.raises(APIError, match="REQUEST_UNRESOLVED"):
        RequestWorkerJournal(worker, tmp_path, "recover").recover_cached(PAYLOAD)
    assert worker.posts == 1


def test_new_boot_cannot_bypass_old_uncertain_static_scope(tmp_path: Path) -> None:
    old = FakeWorker(fail_post=True)
    with pytest.raises(APIError):
        RequestWorkerJournal(old, tmp_path, "old")("POST", "/chat/completions", PAYLOAD)
    fresh = FakeWorker()
    fresh.identity["instance_id"] = "boot2"
    with pytest.raises(APIError, match="SESSION_UNCERTAIN"):
        RequestWorkerJournal(fresh, tmp_path, "fresh")("POST", "/chat/completions", PAYLOAD)
    assert fresh.posts == 0


def test_backend_validates_structured_result_and_recovery_payload(tmp_path: Path) -> None:
    worker = FakeWorker()
    journal = RequestWorkerJournal(worker, tmp_path, "task")
    backend = RequestWorkerBackend(journal, model="synthetic", role="agent", identity=IDENTITY)
    response = backend.generate([{"role": "user", "content": "synthetic"}],
                                GenerationConfig(max_new_tokens=64))
    assert response.text == '{"final_answer":{"answer":"ok"}}'
    assert backend.attempts == 1 and backend.calls[0]["request_id"]


class _Response:
    def __init__(self, value: dict[str, Any], status: int = 200) -> None:
        self.status, self._raw = status, canonical(value).encode()

    def read(self, limit: int) -> bytes:
        return self._raw

    def close(self) -> None:
        return None

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class _Opener:
    def open(self, request: Any, timeout: float) -> _Response:
        assert request.full_url == "https://worker.example/v1/models"
        assert request.get_header("Authorization") == "Bearer synthetic-key"
        return _Response({"profile": "react-vn-request-lifecycle-v3-candidate",
            "identity": dict(IDENTITY), "status": "READY",
            "gpu_quiescence_attested": False})


def test_transport_probe_pins_boot_and_rejects_unprobed_exchange() -> None:
    transport = RequestWorkerHTTPS("https://worker.example/v1", "synthetic-key", EXPECTED,
                                  opener=_Opener())
    with pytest.raises(APIError, match="PROBE_REQUIRED"):
        transport.exchange("GET", "/requests/r1", None)
    metadata = transport.probe()
    assert metadata["identity"] == IDENTITY and transport.instance_id == "boot1"


def test_transport_classifies_non_json_530_as_delivery_error_without_body() -> None:
    class HTML530Opener:
        def open(self, request: Any, timeout: float) -> Any:
            raise urllib.error.HTTPError(
                request.full_url, 530, "origin unavailable", {}, io.BytesIO(b"<html>edge</html>"),
            )

    transport = RequestWorkerHTTPS("https://worker.example/v1", "synthetic-key", EXPECTED,
                                  opener=HTML530Opener())
    transport.identity = dict(IDENTITY)
    with pytest.raises(APIError, match="HTTP_ERROR") as caught:
        transport.exchange("POST", "/chat/completions", PAYLOAD)
    assert caught.value.status == 530
