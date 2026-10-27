"""Controlled CPU substitutes check ordering; these tests do not attest CUDA hardware."""
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from react_agent.serving.quiescent_engine_v3 import QuiescentEngine, load_hf_engine
from react_agent.serving.structured_api_v1 import ServiceError, Spec

SPEC = Spec("r1", [], {}, 32, 42)


def test_cancel_during_synchronization_keeps_engine_busy():
    entered, release = threading.Event(), threading.Event()
    events = []
    def sync():
        events.append("sync")
        entered.set()
        assert release.wait(3)
    engine = QuiescentEngine(lambda spec, stop: events.append("generate") or {}, sync)
    stop = threading.Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(engine, SPEC, stop)
        try:
            assert entered.wait(2)
            stop.set()
            assert not future.done()
            with pytest.raises(ServiceError, match="ENGINE_BUSY"):
                engine(SPEC, threading.Event())
        finally:
            release.set()
        assert future.result(timeout=2).quiescent
    assert events == ["generate", "sync"]


@pytest.mark.parametrize("error,reusable", [(ServiceError("OUTPUT_LIMIT", 422), True),
                                             (RuntimeError("private detail"), False)])
def test_error_still_synchronizes_and_sanitizes(error, reusable):
    events = []
    def generate(spec, stop):
        events.append("generate")
        raise error
    engine = QuiescentEngine(generate, lambda: events.append("sync"))
    result = engine(SPEC, threading.Event())
    assert result.quiescent and result.reusable == reusable
    assert events == ["generate", "sync"] and "private detail" not in str(result)
    if not reusable:
        assert not engine(SPEC, threading.Event()).quiescent
        assert len(events) == 2


def test_sync_failure_never_claims_quiescence_or_reuses_engine():
    calls = []
    def sync():
        calls.append("sync")
        raise RuntimeError("private cuda error")
    engine = QuiescentEngine(lambda spec, stop: {"secret": "withhold"}, sync)
    result = engine(SPEC, threading.Event())
    assert not result.quiescent and not result.reusable
    assert result.result == {"error": {"code": "QUIESCENCE_UNKNOWN"}}
    engine(SPEC, threading.Event())
    assert calls == ["sync"]


def test_interrupt_still_synchronizes_then_retires():
    calls = []
    def generate(spec, stop):
        raise KeyboardInterrupt
    engine = QuiescentEngine(generate, lambda: calls.append("sync"))
    with pytest.raises(KeyboardInterrupt):
        engine(SPEC, threading.Event())
    assert calls == ["sync"] and engine.retired


def test_precancel_skips_generate_but_checks_cleanup():
    events = []
    stop = threading.Event()
    stop.set()
    engine = QuiescentEngine(lambda spec, event: events.append("generate") or {},
                             lambda: events.append("sync"))
    outcome = engine(SPEC, stop)
    assert outcome.quiescent and outcome.result == {"error": {"code": "CANCELLED"}}
    assert events == ["sync"]


@pytest.mark.parametrize("failed_device", [None, 0, 1])
def test_native_bridge_assigns_fresh_stop_and_synchronizes_both_devices(monkeypatch, failed_device):
    import react_agent.serving.quiescent_engine_v3 as module
    events, instances = [], []
    class FakeHF:
        def __init__(self, cfg, stop):
            self.stop = stop
            self.metadata = {"synthetic": True}
            instances.append(self)
        def generate(self, spec):
            events.append(self.stop)
            return {}
    active_failure = []
    def synchronize(device):
        events.append(device)
        if active_failure and device == failed_device:
            raise RuntimeError("synthetic sync error")
    monkeypatch.setattr(module, "HFEngine", FakeHF)
    monkeypatch.setattr(module.importlib, "import_module",
        lambda name: SimpleNamespace(cuda=SimpleNamespace(synchronize=synchronize)))
    engine, metadata = load_hf_engine({})
    assert metadata == {"synthetic": True} and events == [0, 1]
    stop1, stop2 = threading.Event(), threading.Event()
    assert engine(SPEC, stop1).quiescent
    active_failure.append(True)
    outcome = engine(SPEC, stop2)
    assert events == [0, 1, stop1, 0, 1, stop2, 0, 1]
    assert instances[0].stop is stop2 and outcome.quiescent == (failed_device is None)
