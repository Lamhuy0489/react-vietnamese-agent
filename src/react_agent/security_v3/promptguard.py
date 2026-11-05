"""Baseline G1: Prompt Guard 2 filter on tool observations (Study 2, WP7).

Same design as AgentDojo's ``transformers_pi_detector``: every tool observation is scored
by the classifier before the model sees it; an observation scoring at or above the
threshold is replaced by a fixed notice, so the model never reads it. The tool still ran
(the Tool Broker and the scorer are unchanged). The classifier is the local service of
``scripts/serve_promptguard_v1.py`` (127.0.0.1 only); scores are cached by text hash, so
each observation is classified once per run.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from collections.abc import Callable
from typing import Any

from react_agent.security_v3.prompt_baselines import OBSERVATION_PREFIX

THRESHOLD = 0.5
BLOCKED = ("OBSERVATION: [Dữ liệu công cụ này đã bị bộ lọc Prompt Guard chặn vì có dấu hiệu "
           "prompt injection. Không có nội dung nào được hiển thị.]")
Classify = Callable[[str], float]


def local_classifier(url: str, timeout: float = 120) -> Classify:
    if not url.startswith("http://127.0.0.1:"):
        raise ValueError("Prompt Guard service must be local (http://127.0.0.1:PORT)")

    def classify(text: str) -> float:
        request = urllib.request.Request(  # noqa: S310 - local URL checked above
            url.rstrip("/") + "/classify", data=json.dumps({"text": text}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return float(json.loads(response.read())["score"])

    return classify


def local_identity(url: str, timeout: float = 30) -> dict[str, Any]:
    if not url.startswith("http://127.0.0.1:"):
        raise ValueError("Prompt Guard service must be local (http://127.0.0.1:PORT)")
    with urllib.request.urlopen(url.rstrip("/") + "/health", timeout=timeout) as r:  # noqa: S310
        value: dict[str, Any] = json.loads(r.read())
    return value


class PromptGuardFilterBackend:
    """Agent backend wrapper that hides flagged observations from the model."""

    def __init__(self, inner: Any, classify: Classify, threshold: float = THRESHOLD) -> None:
        self._inner, self._classify, self.threshold = inner, classify, threshold
        self._cache: dict[str, float] = {}
        self.flagged: set[str] = set()  # sha256 of flagged observation bodies (no text kept)

    def score(self, body: str) -> float:
        key = hashlib.sha256(body.encode()).hexdigest()
        if key not in self._cache:
            self._cache[key] = self._classify(body)
            if self._cache[key] >= self.threshold:
                self.flagged.add(key)
        return self._cache[key]

    def transform(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        out = []
        for message in messages:
            content = message.get("content", "")
            if message.get("role") == "user" and content.startswith(OBSERVATION_PREFIX) and (
                    self.score(content[len(OBSERVATION_PREFIX):]) >= self.threshold):
                out.append({**message, "content": BLOCKED})
            else:
                out.append(dict(message))
        return out

    def generate(self, messages: list[dict[str, str]], config: Any) -> Any:
        return self._inner.generate(self.transform(messages), config)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)
