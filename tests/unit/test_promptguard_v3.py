"""G1 Prompt Guard filter: flagged observations are hidden, others pass unchanged."""

from __future__ import annotations

from typing import Any

import pytest

from react_agent.security_v3 import promptguard as pg

MESSAGES = [
    {"role": "system", "content": "sys"},
    {"role": "user", "content": "task"},
    {"role": "assistant", "content": "a1"},
    {"role": "user", "content": "OBSERVATION: SAFE_TEXT"},
    {"role": "assistant", "content": "a2"},
    {"role": "user", "content": "OBSERVATION: FLAGGED_TEXT"},
]


def test_flagged_observation_is_replaced_and_cached() -> None:
    calls: list[str] = []

    def classify(text: str) -> float:
        calls.append(text)
        return 0.9 if "FLAGGED" in text else 0.1

    class Inner:
        infra_failures = 0
        sent: list[Any] = []

        def generate(self, messages: list[dict[str, str]], config: Any) -> str:
            self.sent.append(messages)
            return "ok"

    inner = Inner()
    backend = pg.PromptGuardFilterBackend(inner, classify)
    assert backend.generate(MESSAGES, None) == "ok"
    backend.generate(MESSAGES, None)
    sent = inner.sent[0]
    assert sent[3]["content"] == "OBSERVATION: SAFE_TEXT"
    assert sent[5]["content"] == pg.BLOCKED
    assert sent[1]["content"] == "task"  # the user task is never classified
    assert calls == ["SAFE_TEXT", "FLAGGED_TEXT"]  # cached on the second call
    assert len(backend.flagged) == 1 and backend.infra_failures == 0


def test_service_must_be_local() -> None:
    with pytest.raises(ValueError):
        pg.local_classifier("http://example.test:8765")
    with pytest.raises(ValueError):
        pg.local_identity("https://127.0.0.1.example.test")
