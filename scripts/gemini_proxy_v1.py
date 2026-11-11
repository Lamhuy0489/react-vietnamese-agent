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

- ``--upstream`` points the proxy at another OpenAI-compatible server (owner 2026-11-09: local
  OmniRoute pool serving ``gemini-3-flash`` through Antigravity accounts); ``--min-interval``
  spaces upstream calls (seconds, all threads) to stay under the upstream rate limit;
  ``--reasoning-effort ''`` and ``--thinking-tokens 0`` send neither field.
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


def output_shape(result: dict[str, Any]) -> str:
    """Structural class of the reply text (counted only; the text itself is never logged)."""
    try:
        choice = result["choices"][0]
        finish, text = choice.get("finish_reason"), choice["message"].get("content")
    except (KeyError, IndexError, TypeError, AttributeError):
        return "malformed"
    if finish != "stop":
        return f"finish_{finish}"
    if not isinstance(text, str) or not text.strip():
        return "empty"
    stripped = text.strip()
    try:
        return "json" if isinstance(json.loads(stripped), dict) else "json_not_object"
    except json.JSONDecodeError as exc:
        if stripped.startswith("```"):
            return "fenced"
        if exc.msg.startswith("Extra data"):
            return "extra_after_json"
        return "text_around_json" if "{" in stripped else "plain_text"


def extract_object(result: dict[str, Any]) -> bool:
    """Replace reply text by the one JSON object it wraps (format repair, no content change).

    Stands in for the server-side schema decoding the vLLM backbones get: applies only when the
    text is not a JSON object itself and the span from the first ``{`` to the last ``}`` parses
    as one. Returns whether the reply was changed.
    """
    try:
        message = result["choices"][0]["message"]
        text = message["content"]
    except (KeyError, IndexError, TypeError):
        return False
    if not isinstance(text, str):
        return False
    try:
        if isinstance(json.loads(text.strip()), dict):
            return False
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return False
    try:
        value = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return False
    if not isinstance(value, dict):
        return False
    message["content"] = text[start:end + 1]
    return True


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
        # e.g. OmniRoute's semantic cache must be bypassed: a cached answer is not a model call
        self.extra_headers = dict(h.split(":", 1) for h in args.header)
        self.extra_headers = {k.strip(): v.strip() for k, v in self.extra_headers.items()}
        self.pace = threading.Lock()
        self.last_call = 0.0

    def wait_turn(self) -> None:
        """Space upstream calls by ``--min-interval`` seconds across all handler threads."""
        if self.args.min_interval <= 0:
            return
        with self.pace:
            gap = self.last_call + self.args.min_interval - time.monotonic()
            if gap > 0:
                time.sleep(gap)
            self.last_call = time.monotonic()

    def key(self) -> str:
        with self.lock:
            self.turn += 1
            return self.keys[self.turn % len(self.keys)]

    def count(self, name: str) -> None:
        with self.lock:
            self.stats[name] = self.stats.get(name, 0) + 1

    def forward(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        body = {k: v for k, v in payload.items() if k not in (*DROP, *self.args.drop_field)}
        body["model"] = self.args.model
        body["stream"] = False  # OmniRoute streams (SSE) unless told; clients may omit it
        if self.args.tool_as_user:  # AgentDojo LocalLLM: role "tool" without tool_call_id -> 400
            body["messages"] = [{**m, "role": "user"} if m.get("role") == "tool"
                                and "tool_call_id" not in m else m for m in body["messages"]]
        body["max_tokens"] = int(body.get("max_tokens", 512)) + self.args.thinking_tokens
        if self.args.reasoning_effort:
            body["reasoning_effort"] = self.args.reasoning_effort
        data = json.dumps(body, ensure_ascii=False).encode()
        delay = 5.0
        for attempt in range(self.args.max_retries + 1):
            self.wait_turn()
            request = urllib.request.Request(  # noqa: S310 - scheme checked in main()
                self.args.upstream, data=data, method="POST", headers={
                "Authorization": "Bearer " + self.key(), "Content-Type": "application/json",
                    **self.extra_headers})
            try:
                with urllib.request.urlopen(  # noqa: S310
                        request, timeout=self.args.timeout, context=self.client_tls) as response:
                    result: dict[str, Any] = json.loads(response.read())
                result["model"] = self.served
                self.count("shape_" + output_shape(result))
                if self.args.extract_json and extract_object(result):
                    self.count("json_extracted")
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
    p.add_argument("--upstream", default=UPSTREAM)
    p.add_argument("--min-interval", type=float, default=0.0)
    p.add_argument("--drop-field", action="append", default=[],
                   help="request field not forwarded (OmniRoute/Antigravity: response_format "
                        "makes gemini-3-flash repeat its previous action; the runner still "
                        "validates every turn against the action schema)")
    p.add_argument("--header", action="append", default=[],
                   help="extra upstream header 'Name: value' (repeatable)")
    p.add_argument("--extract-json", action="store_true",
                   help="unwrap a reply whose text surrounds one JSON object (format repair)")
    p.add_argument("--tool-as-user", action="store_true",
                   help="send role-tool messages without tool_call_id as role user (AgentDojo)")
    p.add_argument("--stats-every", type=float, default=300)
    args = p.parse_args()
    if not args.upstream.startswith(("https://", "http://127.0.0.1:", "http://localhost:")):
        raise SystemExit("--upstream must be https:// or a local http server")
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
