#!/usr/bin/env python3
"""Local Prompt Guard 2 classifier for baseline G1 (Study 2, WP7).

Runs in the guard venv (``build/venv_guard``: torch + transformers), bound to 127.0.0.1
only::

    HF_TOKEN=... build/venv_guard/bin/python scripts/serve_promptguard_v1.py --port 8765

``POST /classify`` with ``{"text": ...}`` returns ``{"score": p_malicious}``: the maximum
over 512-token windows, the same scoring as the 2026-10-26 guard bake-off
(``run_guard_bakeoff_pg2_v1.py``). ``GET /health`` returns the pinned model identity.
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

REPOS = {"86m": ("meta-llama/Llama-Prompt-Guard-2-86M",
                 "a8ded8e697ce7c355e395a0df51f94adb4a2fd27")}
WINDOW = 512
MAX_BODY = 2_000_000


class Classifier:
    def __init__(self, repo: str, revision: str) -> None:
        import torch  # type: ignore[import-not-found,unused-ignore]
        from transformers import (  # type: ignore[import-not-found,unused-ignore]
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )

        token = os.environ.get("HF_TOKEN")
        self.torch, self.repo, self.revision = torch, repo, revision
        self.tokenizer = AutoTokenizer.from_pretrained(repo, revision=revision, token=token)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            repo, revision=revision, token=token).eval()
        torch.manual_seed(42)

    def score(self, text: str) -> float:
        ids = self.tokenizer(text, add_special_tokens=False)["input_ids"]
        step = WINDOW - 2
        best = 0.0
        for i in range(0, max(len(ids), 1), step):
            window = ids[i:i + step]
            batch = self.torch.tensor(
                [[self.tokenizer.cls_token_id, *window, self.tokenizer.sep_token_id]])
            with self.torch.no_grad():
                probs = self.torch.softmax(self.model(input_ids=batch).logits[0], dim=-1)
            best = max(best, float(probs[1]))
        return best


def handler(classifier: Classifier) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _reply(self, code: int, value: dict[str, Any]) -> None:
            body = json.dumps(value).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._reply(200, {"repo": classifier.repo, "revision": classifier.revision})
            else:
                self._reply(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            if self.path != "/classify" or not 0 < length <= MAX_BODY:
                self._reply(400, {"error": "bad request"})
                return
            try:
                text = json.loads(self.rfile.read(length))["text"]
                if not isinstance(text, str):
                    raise TypeError("text must be a string")
            except (ValueError, KeyError, TypeError):
                self._reply(400, {"error": "bad json"})
                return
            self._reply(200, {"score": classifier.score(text)})

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return None  # no request logging (texts may hold fixture content)

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(REPOS), default="86m")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    classifier = Classifier(*REPOS[args.model])
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler(classifier))
    print(f"READY 127.0.0.1:{args.port} {classifier.repo}@{classifier.revision}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
