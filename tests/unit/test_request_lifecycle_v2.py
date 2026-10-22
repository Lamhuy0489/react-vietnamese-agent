"""Status/cancel race and persistence tests with controlled CPU engines, no network/GPU."""
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from react_agent.serving.request_lifecycle_v2 import RequestLifecycle
from react_agent.serving.structured_api_v1 import ServiceError


def body(request_id="r1"):
    return {"model": "synthetic", "request_id": request_id,
            "messages": [{"role": "user", "content": "SYNTHETIC_PRIVATE_PROMPT"}]}


def service(tmp_path, engine, **kwargs):
    return RequestLifecycle(role="agent", model="synthetic", instance_id="instance1",
                            root=tmp_path, engine=engine, **kwargs)


def test_success_duplicate_and_completed_cancel_do_not_generate_again(tmp_path):
    calls = []
    result = {"content": "SYNTHETIC_PRIVATE_RESPONSE"}
    def engine(spec, stop):
        calls.append(spec.request_id)
        return result
    s = service(tmp_path, engine)
    first, status = s.complete("instance1", body())
    assert status == 200
    first["content"] = "mutated caller"
    result["content"] = "mutated engine"
    again, _ = s.complete("instance1", body())
    assert again["content"] == "SYNTHETIC_PRIVATE_RESPONSE" and calls == ["r1"]
    assert s.cancel("instance1", "r1")["state"] == "SUCCEEDED"
    assert not s.status("instance1", "r1")["cancel_requested"]
    assert s.status("instance1", "r1")["engine_returned"]
    for path in s.root.glob("*.json"):
        text = path.read_text()
        assert "SYNTHETIC_PRIVATE_PROMPT" not in text and "SYNTHETIC_PRIVATE_RESPONSE" not in text


def test_pending_cancel_does_not_claim_engine_stopped(tmp_path):
    entered, release = threading.Event(), threading.Event()
    def engine(spec, stop):
        entered.set()
        assert release.wait(3)
        return {"content": "must be discarded after cancel"}
    s = service(tmp_path, engine)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(s.complete, "instance1", body())
        try:
            assert entered.wait(2)
            pending = s.cancel("instance1", "r1")
            assert pending["state"] == "CANCEL_REQUESTED" and pending["engine_active"]
            assert not pending["engine_returned"] and not pending["gpu_quiescence_attested"]
            assert s.cancel("instance1", "r1") == pending
            with pytest.raises(ServiceError, match="BUSY"):
                s.complete("instance1", body("r2"))
            with pytest.raises(ServiceError, match="IN_PROGRESS"):
                s.complete("instance1", body())
        finally:
            release.set()
        value, status = future.result(timeout=3)
    assert status == 409 and value == {"error": {"code": "CANCELLED"}}
    terminal = s.status("instance1", "r1")
    assert terminal["state"] == "CANCELLED" and terminal["engine_returned"]
    assert not terminal["engine_active"] and not terminal["gpu_quiescence_attested"]
    assert s.complete("instance1", body()) == (value, status)


def test_event_cooperates_and_next_request_not_cancelled(tmp_path):
    entered = threading.Event()
    def engine(spec, stop):
        if spec.request_id == "r1":
            entered.set()
            assert stop.wait(3)
            raise ServiceError("CANCELLED", 409)
        assert not stop.is_set()
        return {"done": True}
    s = service(tmp_path, engine)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(s.complete, "instance1", body())
        assert entered.wait(2)
        s.cancel("instance1", "r1")
        future.result(timeout=3)
    assert s.complete("instance1", body("r2")) == ({"done": True}, 200)


@pytest.mark.parametrize("failure", [RuntimeError("SYNTHETIC_EXCEPTION"),
                                      ServiceError("OUTPUT_LIMIT", 422)])
def test_failures_cached_without_raw_exception(tmp_path, failure):
    calls = []
    def engine(spec, stop):
        calls.append(spec.request_id)
        raise failure
    s = service(tmp_path, engine)
    result = s.complete("instance1", body())
    assert result == s.complete("instance1", body()) and len(calls) == 1
    assert "SYNTHETIC_EXCEPTION" not in json.dumps(result)
    assert s.status("instance1", "r1")["state"] == "FAILED"


def test_identity_unknown_conflict_capacity_and_restart(tmp_path):
    s = service(tmp_path, lambda spec, stop: {}, capacity=1)
    with pytest.raises(ServiceError, match="INSTANCE_MISMATCH"):
        s.complete("old", body())
    with pytest.raises(ServiceError, match="REQUEST_UNKNOWN"):
        s.cancel("instance1", "unknown")
    with pytest.raises(ServiceError, match="REQUEST_ID_REQUIRED"):
        s.complete("instance1", {"model":"synthetic"})
    s.complete("instance1", body())
    with pytest.raises(ServiceError, match="CONFLICT"):
        s.complete("instance1", {**body(), "seed": 7})
    with pytest.raises(ServiceError, match="CAPACITY"):
        s.complete("instance1", body("r2"))
    with pytest.raises(FileExistsError):
        service(tmp_path, lambda spec, stop: {})


def test_persist_failure_before_dispatch_retires_instance(tmp_path, monkeypatch):
    calls = []
    s = service(tmp_path, lambda spec, stop: calls.append(spec))
    def broken(*args):
        raise OSError("SYNTHETIC_DISK_ERROR")
    monkeypatch.setattr("react_agent.serving.request_lifecycle_v2.save_new", broken)
    with pytest.raises(ServiceError, match="WRITE_FAILED"):
        s.complete("instance1", body())
    assert not calls and s.retired
    with pytest.raises(ServiceError, match="RETIRED"):
        s.complete("instance1", body("r2"))
