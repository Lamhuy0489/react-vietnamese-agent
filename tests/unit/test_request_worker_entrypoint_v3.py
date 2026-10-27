"""Entrypoint failures must close the service and remain observable to its owner."""
import io
import threading
from types import SimpleNamespace

import pytest

from react_agent.serving import request_worker_entrypoint_v3 as entry
from react_agent.serving.structured_api_v1 import ServiceError, sha


@pytest.fixture
def wired(tmp_path, monkeypatch):
    events = []
    done = threading.Event()
    life = SimpleNamespace(instance_id="boot", begin_shutdown=lambda: events.append("retire"),
                           is_idle=lambda: True)
    server = SimpleNamespace(serve_forever=lambda: done.wait(2),
                             shutdown=lambda: (events.append("shutdown"), done.set()),
                             server_close=lambda: events.append("close"))
    tunnel = SimpleNamespace(stdout=io.StringIO("https://synthetic.trycloudflare.com\n"),
                             poll=lambda: None, terminate=lambda: events.append("terminate"),
                             wait=lambda timeout: 0, kill=lambda: events.append("kill"))
    monkeypatch.setattr(entry, "load_worker", lambda *a, **k: SimpleNamespace(lifecycle=life))
    monkeypatch.setattr(entry, "make_server", lambda *a: server)
    monkeypatch.setattr(entry.subprocess, "Popen", lambda *a, **k: tunnel)
    monkeypatch.setattr(entry.urllib.request, "urlretrieve", lambda u, p: p.write_bytes(b"binary"))
    monkeypatch.setattr(entry, "_publish", lambda *a: events.append("publish"))
    cfg = {"state_root": str(tmp_path / "state"), "model": "synthetic", "session_id": "s",
           "cloudflared_url": "https://synthetic.invalid", "cloudflared_sha256": sha(b"binary"),
           "lifetime_seconds": 0.02, "discovery_timeout_seconds": 0.01,
           "shutdown_timeout_seconds": 0.01}
    return cfg, events, tunnel, life


def test_success_closes_resources(wired):
    cfg, events, _, _ = wired
    entry.serve(cfg)
    assert events == ["publish", "retire", "shutdown", "close", "terminate"]


def test_publish_failure_reaches_owner_and_closes(wired, monkeypatch):
    cfg, events, _, _ = wired
    cfg["lifetime_seconds"] = 2
    def fail(*args):
        raise OSError("synthetic sensitive detail")
    monkeypatch.setattr(entry, "_publish", fail)
    with pytest.raises(ServiceError, match="DISCOVERY_FAILED"):
        entry.serve(cfg)
    assert events == ["retire", "shutdown", "close", "terminate"]


def test_dead_tunnel_cannot_wait_full_lifetime(wired):
    cfg, events, tunnel, _ = wired
    tunnel.poll = lambda: 1
    cfg["lifetime_seconds"] = 2
    with pytest.raises(ServiceError, match="TUNNEL_EXITED"):
        entry.serve(cfg)
    assert "close" in events and "terminate" not in events


def test_missing_discovery_times_out(wired):
    cfg, events, tunnel, _ = wired
    cfg["lifetime_seconds"] = 2
    tunnel.stdout = io.StringIO("no endpoint\n")
    with pytest.raises(ServiceError, match="DISCOVERY_TIMEOUT"):
        entry.serve(cfg)
    assert "close" in events


def test_shutdown_never_claims_stopped_with_active_engine(wired):
    cfg, _, _, life = wired
    life.is_idle = lambda: False
    with pytest.raises(ServiceError, match="SHUTDOWN_UNCONFIRMED"):
        entry.serve(cfg)


def test_wrong_tunnel_binary_closes_server_without_starting_tunnel(wired):
    cfg, events, _, _ = wired
    cfg["cloudflared_sha256"] = "0" * 64
    with pytest.raises(ServiceError, match="TUNNEL_BINARY_HASH"):
        entry.serve(cfg)
    assert events == ["retire", "shutdown", "close"]
