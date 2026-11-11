"""PRG baseline: sinks run only for destinations named in the user's instruction."""

from __future__ import annotations

from pathlib import Path

from react_agent.security_v3.progent_lite import PolicyTool, apply_progent_lite
from react_agent.tools.factory import build_clean_registry

ROOT = Path(__file__).resolve().parents[2]


def test_policy_on_clean_registry() -> None:
    registry = apply_progent_lite(
        build_clean_registry(ROOT / "data/clean/v1_1/environment"),
        "Gửi email cho Office@Example.test về lịch học.")
    email = registry.get("send_email_mock")
    assert isinstance(email, PolicyTool)
    assert not isinstance(registry.get("doc_read"), PolicyTool)
    ok = email.execute("call_000001", {"to": "office@example.test", "subject": "s", "body": "b"})
    assert ok.ok
    denied = email.execute("call_000002", {"to": "x@example.test", "subject": "s", "body": "b"})
    assert not denied.ok and denied.error is not None and denied.error.code == "POLICY_DENIED"
    hook = registry.get("post_webhook_mock")
    assert hook is not None
    assert not hook.execute("call_000003", {"endpoint": "mock://a", "payload": {}}).ok
    clean = build_clean_registry(ROOT / "data/clean/v1_1/environment")
    assert registry.definitions() == clean.definitions()  # the model sees the same tools
    assert email.denied == 1
