#!/usr/bin/env python3
"""Local HTTPS proxy that serves a Gemini model to the v3 runner as if it were a vLLM endpoint.

The runner's transport (pinned by ``final_config_v3``) admits only ``https://host/v1`` with
``GET /models`` and ``POST /chat/completions``. This proxy listens on 127.0.0.1 with a
self-signed certificate (``--cert``/``--cert-key``; add the certificate to ``SSL_CERT_FILE``)
and forwards each chat request to the Gemini OpenAI-compatible endpoint:

- ``model`` becomes the Gemini model id; the response's ``model`` is set back to the served
  name ``<repo>@<revision>`` that the runner checks;
- vLLM-only fields (``request_id``, ``chat_template_kwargs``) and ``seed`` (HTTP 400 on this
  API, so Gemini runs are not seeded) are dropped;
  temperature 0 and the JSON schema (``response_format``) are passed through;
- ``reasoning_effort`` is fixed by ``--reasoning-effort`` and ``--thinking-tokens`` is added to
  ``max_tokens`` (thinking counts against it on this API); both are recorded in the run notes;
- HTTP 429/5xx and network errors are retried with backoff, rotating over the keys in
  ``--keys-file`` (one per line, outside the repo); after ``--max-retries`` the proxy answers
  503, which the runner records as an infrastructure error and resumes later.

Logs counts only (no message text). No key is printed or written anywhere.
"""

from __future__ import annotations

import argparse
import json
import secrets
import ssl
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import certifi

UPSTREAM = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DROP = ("request_id", "chat_template_kwargs", "seed")  # seed: rejected by this API (400)


class Proxy:
    def __init__(self, args: argparse.Namespace) -> None:
        self.keys = [k.strip() for k in Path(args.keys_file).expanduser().read_text().split()
                     if k.strip()]
        if not self.keys:
            raise SystemExit("no keys in --keys-file")
        self.args = args
        self.served = f"{args.repo}@{args.revision}"
        self.local_key = Path(args.local_key_file).read_text().strip()
        self.lock = threading.Lock()
        self.turn = 0
        self.client_tls = ssl.create_default_context(cafile=certifi.where())
        self.stats: dict[str, int] = {"requests": 0, "ok": 0, "retries": 0, "failed": 0}

    def key(self) -> str:
        with self.lock:
            self.turn += 1
            return self.keys[self.turn % len(self.keys)]

    def count(self, name: str) -> None:
        with self.lock:
            self.stats[name] = self.stats.get(name, 0) + 1

    def forward(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        body = {k: v for k, v in payload.items() if k not in DROP}
        body["model"] = self.args.model
        body["max_tokens"] = int(body.get("max_tokens", 512)) + self.args.thinking_tokens
        if self.args.reasoning_effort:
            body["reasoning_effort"] = self.args.reasoning_effort
        data = json.dumps(body, ensure_ascii=False).encode()
        delay = 5.0
        for attempt in range(self.args.max_retries + 1):
            request = urllib.request.Request(UPSTREAM, data=data, method="POST", headers={
                "Authorization": "Bearer " + self.key(), "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(  # noqa: S310
                        request, timeout=self.args.timeout, context=self.client_tls) as response:
                    result: dict[str, Any] = json.loads(response.read())
                result["model"] = self.served
                return 200, result
            except urllib.error.HTTPError as exc:
                self.count(f"http_{exc.code}")
                if exc.code != 429 and exc.code < 500:
                    self.count("client_error")
                    return 400, {"error": {"code": exc.code}}
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                self.count("network")
            if attempt < self.args.max_retries:
                self.count("retries")
                time.sleep(delay)
                delay = min(delay * 2, 120.0)
        self.count("failed")
        return 503, {"error": {"code": 503}}


def handler(proxy: Proxy) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def reply(self, status: int, value: dict[str, Any]) -> None:
            raw = json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def authorised(self) -> bool:
            sent = self.headers.get("Authorization", "")
            if secrets.compare_digest(sent, "Bearer " + proxy.local_key):
                return True
            self.reply(401, {"error": {"code": 401}})
            return False

        def do_GET(self) -> None:  # noqa: N802
            if not self.authorised():
                return
            if self.path != "/v1/models":
                self.reply(404, {"error": {"code": 404}})
                return
            self.reply(200, {"object": "list", "data": [{"id": proxy.served, "object": "model"}]})

        def do_POST(self) -> None:  # noqa: N802
            if not self.authorised():
                return
            if self.path != "/v1/chat/completions":
                self.reply(404, {"error": {"code": 404}})
                return
            proxy.count("requests")
            length = int(self.headers.get("Content-Length", "0"))
            status, value = proxy.forward(json.loads(self.rfile.read(length)))
            if status == 200:
                proxy.count("ok")
            self.reply(status, value)

    return Handler


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="gemini-3.5-flash")
    p.add_argument("--repo", default="google/gemini-3.5-flash")
    p.add_argument("--revision", default="3.5-flash-05-2026")
    p.add_argument("--keys-file", default="~/.gemini_keys")
    p.add_argument("--local-key-file", required=True)
    p.add_argument("--cert", required=True)
    p.add_argument("--cert-key", required=True)
    p.add_argument("--port", type=int, default=8443)
    p.add_argument("--reasoning-effort", default="low")
    p.add_argument("--thinking-tokens", type=int, default=2048)
    p.add_argument("--max-retries", type=int, default=8)
    p.add_argument("--timeout", type=float, default=120)
    p.add_argument("--stats-every", type=float, default=300)
    args = p.parse_args()
    proxy = Proxy(args)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler(proxy))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(args.cert, args.cert_key)
    server.socket = context.wrap_socket(server.socket, server_side=True)

    def report() -> None:
        while True:
            time.sleep(args.stats_every)
            print(time.strftime("%H:%M"), json.dumps(proxy.stats), flush=True)

    threading.Thread(target=report, daemon=True).start()
    print(f"serving {proxy.served} on https://127.0.0.1:{args.port}/v1", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
