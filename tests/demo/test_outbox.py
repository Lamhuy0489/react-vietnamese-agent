import json
from pathlib import Path

import pytest

from react_agent.demo.gmail_sender import DryRunSender, SendError
from react_agent.demo.outbox import Outbox, single_recipient

ALLOW = frozenset({"huy@university.example", "minh@university.example"})


def make(tmp_path: Path, limit: int = 5) -> tuple[Outbox, DryRunSender]:
    sender = DryRunSender()
    outbox = Outbox(sender, ALLOW, daily_limit=limit, footer="\n--", log_path=tmp_path / "o.jsonl")
    return outbox, sender


@pytest.mark.parametrize(("raw", "expected"), [
    ("huy@university.example", "huy@university.example"),
    ("  HUY@University.Example ", "huy@university.example"),
    ("huy@university.example,evil@x.example", None),
    ("huy@university.example; evil@x.example", None),
    ('"Huy" <evil@x.example>', None),
    ("<huy@university.example>", None),
    ("huy@university.example\nBcc: evil@x.example", None),
    ("not-an-address", None),
])
def test_single_recipient(raw: str, expected: str | None) -> None:
    assert single_recipient(raw) == expected


def test_allowed_message_waits_for_confirmation(tmp_path: Path) -> None:
    outbox, sender = make(tmp_path)
    item = outbox.add("Huy@university.example", "S", "B", turn_id="t1")
    assert item.status == "pending" and sender.sent == []
    assert outbox.confirm(item.item_id).status == "sent"
    assert sender.sent == [("huy@university.example", "S", "B\n--")]
    assert outbox.confirm(item.item_id).status == "sent" and len(sender.sent) == 1  # idempotent


def test_outside_allowlist_never_sends(tmp_path: Path) -> None:
    outbox, sender = make(tmp_path)
    item = outbox.add("evil@attacker.example", "S", "B", turn_id="t1")
    assert item.status == "blocked_allowlist"
    assert outbox.confirm(item.item_id).status == "blocked_allowlist"
    assert sender.sent == []


def test_reject_and_daily_limit(tmp_path: Path) -> None:
    outbox, sender = make(tmp_path, limit=1)
    a = outbox.add("huy@university.example", "S", "B", turn_id="t1")
    b = outbox.add("minh@university.example", "S", "B", turn_id="t1")
    c = outbox.add("minh@university.example", "S", "B", turn_id="t1")
    assert outbox.reject(a.item_id).status == "rejected"
    assert outbox.confirm(a.item_id).status == "rejected"
    assert outbox.confirm(b.item_id).status == "sent"
    assert outbox.confirm(c.item_id).status == "over_limit"
    assert len(sender.sent) == 1
    log = [json.loads(line) for line in (tmp_path / "o.jsonl").read_text().splitlines()]
    assert {entry["status"] for entry in log} >= {"pending", "rejected", "sent", "over_limit"}


def test_send_failure_is_recorded(tmp_path: Path) -> None:
    class Failing(DryRunSender):
        def send(self, to: str, subject: str, body: str) -> str:
            raise SendError("Gửi thất bại: OSError")

    outbox = Outbox(Failing(), ALLOW, daily_limit=5)
    item = outbox.add("huy@university.example", "S", "B", turn_id="t1")
    assert outbox.confirm(item.item_id).status == "failed"
