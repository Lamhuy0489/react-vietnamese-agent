from __future__ import annotations

from typing import Any

import pytest

from react_agent.evaluation import adversarial_v1
from react_agent.evaluation.adversarial_v1 import GuardFactory, GuardKeepalive
from react_agent.llm.http_diagnostic_v1 import APIError


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_keepalive_pings_only_after_the_interval_and_touch_resets_it() -> None:
    clock, pings = Clock(), []
    keepalive = GuardKeepalive(lambda: pings.append(clock.now), every_seconds=600, clock=clock)
    clock.now = 599
    assert not keepalive.tick()
    clock.now = 600
    assert keepalive.tick() and pings == [600]
    clock.now = 1100
    keepalive.touch()  # a guarded execution counts as activity
    clock.now = 1600
    assert not keepalive.tick()
    clock.now = 1700
    assert keepalive.tick() and pings == [600, 1700]


def test_failed_ping_is_reported_not_raised(capsys: pytest.CaptureFixture[str]) -> None:
    def down() -> None:
        raise APIError("NETWORK_ERROR")

    clock = Clock()
    keepalive = GuardKeepalive(down, every_seconds=10, clock=clock)
    clock.now = 10
    assert keepalive.tick()
    assert "guard keepalive ping failed" in capsys.readouterr().out
    clock.now = 15
    assert not keepalive.tick()  # no tight retry loop after a failure


def test_guard_ping_is_a_one_token_completion_to_the_served_guard(
        monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[tuple[str, str, dict[str, Any] | None]] = []

    class Transport:
        def __init__(self, base_url: str, api_key: str, timeout: float) -> None:
            pass

        def __call__(self, method: str, path: str,
                     payload: dict[str, Any] | None) -> dict[str, Any]:
            sent.append((method, path, payload))
            return {}

    monkeypatch.setattr(adversarial_v1, "OrderedHTTPSJSON", Transport)
    GuardFactory("https://guard/v1", "k" * 32, "meta-llama/Llama-3.2-3B-Instruct", "abc").ping()
    [(method, path, payload)] = sent
    assert (method, path) == ("POST", "/chat/completions")
    assert payload is not None and payload["max_tokens"] == 1
    assert payload["model"] == adversarial_v1.served_name(
        "meta-llama/Llama-3.2-3B-Instruct", "abc")
