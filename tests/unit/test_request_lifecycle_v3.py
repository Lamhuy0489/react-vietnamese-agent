import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from react_agent.serving.quiescent_engine_v3 import EngineOutcome, QuiescentEngine
from react_agent.serving.request_lifecycle_v3 import QuiescentLifecycle
from react_agent.serving.structured_api_v1 import ServiceError

BODY = {"model": "synthetic", "request_id": "r1",
        "messages": [{"role": "user", "content": "synthetic private prompt"}]}


def service(tmp_path, engine, **kwargs):
    return QuiescentLifecycle(role="agent", model="synthetic", instance_id="boot1",
                              root=tmp_path, engine=engine, **kwargs)


def test_cancel_waits_for_cleanup_and_next_request_has_fresh_event(tmp_path):
    entered, release = threading.Event(), threading.Event()
    stops = []
    def generate(spec, stop):
        stops.append(stop)
        return {"answer": "withheld if cancelled"}
    def sync():
        entered.set()
        assert release.wait(3)
    s = service(tmp_path, QuiescentEngine(generate, sync))
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(s.complete, "boot1", BODY)
        try:
            assert entered.wait(2)
            status = s.cancel("boot1", "r1")
            assert status["state"] == "CANCEL_REQUESTED" and status["engine_active"]
            assert not status["gpu_quiescence_attested"]
            with pytest.raises(ServiceError, match="BUSY"):
                s.complete("boot1", {**BODY, "request_id": "r2"})
        finally:
            release.set()
        assert future.result(timeout=2) == ({"error": {"code": "CANCELLED"}}, 409)
    terminal = s.status("boot1", "r1")
    assert terminal["gpu_quiescence_attested"] and terminal["durable"]
    assert terminal["state"] == "CANCELLED" and not terminal["engine_active"]
    assert s.complete("boot1", BODY)[1] == 409 and len(stops) == 1
    assert s.complete("boot1", {**BODY, "request_id": "r2"})[1] == 200
    assert stops[0].is_set() and not stops[1].is_set()


def test_unknown_cleanup_retires_even_after_cancel(tmp_path):
    def engine(spec, stop):
        stop.set()
        return EngineOutcome({"secret": "private"}, 200, False, False)
    s = service(tmp_path, engine)
    result, code = s.complete("boot1", BODY)
    assert code == 503 and "secret" not in str(result)
    state = s.status("boot1", "r1")
    assert state["state"] == "QUIESCENCE_UNKNOWN" and state["instance_retired"]
    assert not state["gpu_quiescence_attested"]
    with pytest.raises(ServiceError, match="RETIRED"):
        s.complete("boot1", {**BODY, "request_id": "r2"})


def test_result_bytes_bounded_without_eviction_or_reexecution(tmp_path):
    calls = []
    def engine(spec, stop):
        calls.append(spec.request_id)
        return EngineOutcome({"answer": "x" * 2048}, 200, True, True)
    s = service(tmp_path, engine, result_limit=1024, capacity=1)
    result = s.complete("boot1", BODY)
    assert result == ({"error": {"code": "RESULT_TOO_LARGE"}}, 507)
    assert s.complete("boot1", BODY) == result and calls == ["r1"]
    with pytest.raises(ServiceError, match="CAPACITY"):
        s.complete("boot1", {**BODY, "request_id": "r2"})


def test_terminal_persistence_failure_marks_nondurable_and_retires(tmp_path, monkeypatch):
    import react_agent.serving.request_lifecycle_v3 as module
    real = module.save_new
    s = service(tmp_path, lambda spec, stop: EngineOutcome({}, 200, True, True))
    def save(path, value):
        if value.get("engine_returned"):
            raise OSError("synthetic storage failure")
        real(path, value)
    monkeypatch.setattr(module, "save_new", save)
    with pytest.raises(ServiceError, match="WRITE_FAILED"):
        s.complete("boot1", BODY)
    state = s.status("boot1", "r1")
    assert not state["durable"] and state["instance_retired"]
    assert len(list(s.root.glob("r1.*.json"))) == 1


@pytest.mark.parametrize("bad_engine", [lambda spec, stop: {},
    lambda spec, stop: EngineOutcome({"bad": float('nan')}, 200, True, True)])
def test_broken_engine_contract_retires_without_raw_result(tmp_path, bad_engine):
    s = service(tmp_path, bad_engine)
    result, code = s.complete("boot1", BODY)
    assert code >= 500 and "bad" not in result and s.retired
    for path in s.root.glob("*.json"):
        assert "private prompt" not in path.read_text()
        json.loads(path.read_text())
