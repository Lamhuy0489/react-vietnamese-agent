"""CPU transport checks; only the explicit wire test binds a loopback socket."""
import http.client
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from react_agent.serving.request_http_v2 import LifecycleHTTP, make_server
from react_agent.serving.structured_api_v1 import LIMIT, ServiceError, canonical, sha

KEY = "synthetic-test-key-000000000000000000000"
AUTH = "Bearer " + KEY
PINS = {"session_id": "synthetic-session", "source_commit": "a" * 40,
        "worker_sha256": "b" * 64, "model_revision": "sha256:" + "c" * 64}
BODY = {"model": "synthetic", "request_id": "req1",
        "messages": [{"role": "user", "content": "synthetic private prompt"}]}


def app(tmp_path, engine=lambda spec, stop: {"final_answer": {"answer": "safe"}}):
    return LifecycleHTTP(api_key=KEY, identity=PINS, role="agent", model="synthetic",
                         root=tmp_path, engine=engine)


@pytest.mark.parametrize("method,path,raw", [
    ("GET", "/v1/models", b""),
    ("GET", "/v1/requests/unknown", b""),
    ("POST", "/v1/requests/unknown/cancel", b""),
    ("POST", "/v1/chat/completions", b"not json"),
])
def test_auth_precedes_all_lookup_and_parsing(tmp_path, method, path, raw):
    service = app(tmp_path)
    with pytest.raises(ServiceError, match="UNAUTHORIZED"):
        service.dispatch(method, path, "Bearer wrong", "wrong-instance", raw)
    assert not service.lifecycle.requests


def test_boot_identity_and_hashed_status_without_content(tmp_path):
    service = app(tmp_path)
    instance = service.lifecycle.instance_id
    assert instance != app(tmp_path).lifecycle.instance_id
    metadata, _ = service.dispatch("GET", "/v1/models", AUTH, None)
    assert metadata["identity"]["instance_id"] == instance
    result, code = service.dispatch("POST", "/v1/chat/completions", AUTH,
                                     instance, canonical(BODY).encode())
    assert code == 200 and result["result"]["final_answer"]["answer"] == "safe"
    status, code = service.dispatch("GET", "/v1/requests/req1", AUTH, instance)
    assert code == 200 and status["identity"] == metadata["identity"]
    assert status["request"]["request_sha256"] == sha(canonical(BODY).encode())
    assert status["request"]["state"] == "SUCCEEDED"
    assert "private prompt" not in canonical(status) and KEY not in canonical(status)
    with pytest.raises(ServiceError, match="INSTANCE_MISMATCH"):
        service.dispatch("GET", "/v1/requests/req1", AUTH, "old-boot")
    with pytest.raises(ServiceError, match="REQUEST_UNKNOWN"):
        service.dispatch("GET", "/v1/requests/missing", AUTH, instance)


@pytest.mark.parametrize("raw,code", [
    (b'{"request_id":"a","request_id":"b"}', "INVALID_JSON"),
    (b'{"n":NaN}', "INVALID_JSON"),
    (b'[]', "INVALID_JSON"),
    (b'\xff', "INVALID_JSON"),
    (b'x' * (LIMIT + 1), "BODY_TOO_LARGE"),
])
def test_invalid_bodies_never_dispatch(tmp_path, raw, code):
    service = app(tmp_path)
    with pytest.raises(ServiceError, match=code):
        service.dispatch("POST", "/v1/chat/completions", AUTH,
                         service.lifecycle.instance_id, raw)
    assert not service.lifecycle.requests


def test_wire_cancel_concurrent_with_completion_and_duplicate_delivery(tmp_path):
    entered, release = threading.Event(), threading.Event()
    calls = []
    def engine(spec, stop):
        calls.append(spec.request_id)
        entered.set()
        assert release.wait(5)
        return {"final_answer": {"answer": "discard after cancellation"}}
    service = app(tmp_path, engine)
    server = make_server(service, ("127.0.0.1", 0))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    def request(method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            conn.request(method, path, body, headers or {
                "Authorization": AUTH, "X-Instance-ID": service.lifecycle.instance_id})
            response = conn.getresponse()
            return response.status, json.loads(response.read())
        finally:
            conn.close()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(request, "POST", "/v1/chat/completions", canonical(BODY))
            try:
                assert entered.wait(2)
                code, pending = request("POST", "/v1/requests/req1/cancel")
                assert code == 202 and pending["request"]["engine_active"]
                assert pending["request"]["state"] == "CANCEL_REQUESTED"
                code, invalid = request("POST", "/v1/chat/completions", b"invalid",
                    {"Authorization": "Bearer wrong", "Content-Length": str(LIMIT + 1)})
                assert code == 401 and invalid == {"error": {"code": "UNAUTHORIZED"}}
            finally:
                release.set()
            code, terminal = future.result(timeout=5)
        assert code == 409 and terminal["request"]["state"] == "CANCELLED"
        assert "discard" not in canonical(terminal)
        assert request("POST", "/v1/chat/completions", canonical(BODY)) == (code, terminal)
        assert calls == ["req1"]
        code, terminal = request("GET", "/v1/requests/req1")
        assert code == 200 and terminal["request"]["engine_returned"]
        assert not terminal["request"]["gpu_quiescence_attested"]
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
    assert not worker.is_alive()
