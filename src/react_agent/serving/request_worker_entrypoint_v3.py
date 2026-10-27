"""Kaggle-only entrypoint for the versioned request-worker v3 package.

The lifecycle/HTTP implementation remains importable and testable without a
tunnel.  This module owns the deployment-only actions: dependency admission,
local server binding, cloudflared process lifetime and encrypted discovery.
No benchmark data or agent tools are loaded here.
"""

from __future__ import annotations

import base64
import importlib
import re
import secrets
import subprocess
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

from react_agent.serving.request_http_v3 import PROFILE, make_server
from react_agent.serving.request_worker_v3 import load_worker
from react_agent.serving.structured_api_v1 import PINS, ServiceError, canonical, sha


def _publish(cfg: dict[str, Any], endpoint: str, api_key: str) -> None:
    """Send only encrypted connection material to the fixed discovery topic."""
    serialization = importlib.import_module("cryptography.hazmat.primitives.serialization")
    padding = importlib.import_module("cryptography.hazmat.primitives.asymmetric.padding")
    hashes = importlib.import_module("cryptography.hazmat.primitives.hashes")
    public = serialization.load_pem_public_key(cfg["public_key_pem"].encode())
    plaintext = canonical({
        "endpoint": endpoint + "/v1",
        "api_key": api_key,
        "session_id": cfg["session_id"],
        "profile": PROFILE,
    }).encode()
    encrypted = public.encrypt(plaintext, padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(), label=None,
    ))
    request = urllib.request.Request(
        "https://ntfy.sh/" + cfg["topic"],
        data=canonical({
            "session_id": cfg["session_id"],
            "profile": PROFILE,
            "ciphertext": base64.b64encode(encrypted).decode(),
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=15):  # noqa: S310 - fixed discovery host
        pass


def serve(cfg: dict[str, Any]) -> None:
    """Warm the model, bind v3 routes, and own the tunnel lifetime."""
    stop = threading.Event()
    api_key = secrets.token_urlsafe(32)
    state_root = Path(cfg.get("state_root", "/kaggle/working/react-vn-request-state"))
    state_root.mkdir(parents=True, exist_ok=True)
    app = load_worker(cfg, api_key=api_key, state_root=state_root)
    server = make_server(app, ("127.0.0.1", 8000))
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    temporary = tempfile.TemporaryDirectory(prefix="react-vn-tunnel-v3-")
    binary = Path(temporary.name) / "cloudflared"
    tunnel: subprocess.Popen[str] | None = None
    try:
        urllib.request.urlretrieve(cfg["cloudflared_url"], binary)  # noqa: S310 - pinned URL
        if sha(binary.read_bytes()) != cfg["cloudflared_sha256"]:
            raise ServiceError("TUNNEL_BINARY_HASH", 503)
        binary.chmod(0o700)
        tunnel = subprocess.Popen(  # noqa: S603 - fixed cloudflared argv
            [str(binary), "tunnel", "--url", "http://127.0.0.1:8000", "--no-autoupdate"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        def discover() -> None:
            assert tunnel is not None and tunnel.stdout is not None  # noqa: S101
            try:
                for line in tunnel.stdout:
                    match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
                    if not match or ready.is_set():
                        continue
                    _publish(cfg, match.group(0), api_key)
                    ready.set()
                    print("READY " + cfg["model"] + " session=" + cfg["session_id"]
                          + " instance=" + app.lifecycle.instance_id, flush=True)
            except Exception:
                # Thread failures must reach the owner without exposing connection material.
                discovery_failed.set()
                stop.set()

        ready, discovery_failed = threading.Event(), threading.Event()
        discovery_thread = threading.Thread(target=discover, daemon=True)
        discovery_thread.start()
        started = time.monotonic()
        while time.monotonic() - started < cfg.get("lifetime_seconds", 28800):
            if discovery_failed.is_set():
                raise ServiceError("DISCOVERY_FAILED", 503)
            if tunnel.poll() is not None:
                raise ServiceError("TUNNEL_EXITED", 503)
            if not ready.is_set() and time.monotonic() - started >= cfg.get(
                    "discovery_timeout_seconds", 120):
                raise ServiceError("DISCOVERY_TIMEOUT", 503)
            stop.wait(0.2)
    finally:
        stop.set()
        try:
            app.lifecycle.begin_shutdown()
        finally:
            server.shutdown()
            server.server_close()
            if tunnel is not None:
                if tunnel.poll() is None:
                    tunnel.terminate()
                try:
                    tunnel.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    tunnel.kill()
                    tunnel.wait(timeout=10)
                if tunnel.stdout is not None:
                    tunnel.stdout.close()
            server_thread.join(timeout=10)
            temporary.cleanup()
        deadline = time.monotonic() + cfg.get("shutdown_timeout_seconds", 15)
        while not app.lifecycle.is_idle() and time.monotonic() < deadline:
            time.sleep(0.05)
        if not app.lifecycle.is_idle():
            raise ServiceError("SHUTDOWN_UNCONFIRMED", 503)
        print("STOPPED " + cfg["model"], flush=True)


def install_and_serve(cfg: dict[str, Any]) -> None:
    """Install exact worker pins, then enter the deployment lifetime."""
    import sys

    subprocess.run(  # noqa: S603 - exact dependency pins, no shell
        [sys.executable, "-m", "pip", "install", "--quiet",
         *(f"{name}=={version}" for name, version in PINS.items())],
        check=True,
    )
    print("LOADING " + cfg["model"], flush=True)
    serve(cfg)
