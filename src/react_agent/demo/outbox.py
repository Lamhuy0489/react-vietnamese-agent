"""Outbox: e-mails the guard allowed, waiting for the user's confirmation.

A message reaches the real sender only if (1) the broker executed the ``send_email_mock``
call after every gate allowed it, (2) its single recipient is on the allowlist, (3) the
user confirmed it, and (4) the daily limit is not reached.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from email.utils import parseaddr
from pathlib import Path
from typing import Literal
from uuid import uuid4

from react_agent.demo.config import normalize_address
from react_agent.demo.gmail_sender import Sender, SendError

Status = Literal["pending", "sent", "rejected", "blocked_allowlist", "over_limit", "failed"]


def single_recipient(raw: str) -> str | None:
    """The bare address if ``raw`` names exactly one plain address, else ``None``."""
    if any(c in raw for c in ",;\r\n"):
        return None
    name, address = parseaddr(raw)
    address = normalize_address(address)
    if name or address != normalize_address(raw) or address.count("@") != 1:
        return None
    return address


@dataclass
class OutboxItem:
    to: str
    subject: str
    body: str
    turn_id: str
    status: Status = "pending"
    item_id: str = field(default_factory=lambda: uuid4().hex[:10])
    created: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"))
    note: str = ""


class Outbox:
    def __init__(self, sender: Sender, allowlist: frozenset[str], *, daily_limit: int,
                 footer: str = "", log_path: Path | None = None) -> None:
        self.sender = sender
        self.allowlist = allowlist
        self.daily_limit = daily_limit
        self.footer = footer
        self.log_path = log_path
        self.items: list[OutboxItem] = []
        self._lock = threading.Lock()

    def add(self, to: str, subject: str, body: str, *, turn_id: str) -> OutboxItem:
        item = OutboxItem(to=to, subject=subject, body=body, turn_id=turn_id)
        address = single_recipient(to)
        if address is None or address not in self.allowlist:
            item.status = "blocked_allowlist"
            item.note = "Địa chỉ không nằm trong danh sách cho phép, thư không được gửi."
        with self._lock:
            self.items.append(item)
        self._log(item)
        return item

    def pending(self) -> list[OutboxItem]:
        return [i for i in self.items if i.status == "pending"]

    def sent_today(self) -> int:
        today = datetime.now(UTC).date().isoformat()
        return sum(1 for i in self.items if i.status == "sent" and i.created.startswith(today))

    def _get(self, item_id: str) -> OutboxItem:
        for item in self.items:
            if item.item_id == item_id:
                return item
        raise KeyError(item_id)

    def confirm(self, item_id: str) -> OutboxItem:
        with self._lock:
            item = self._get(item_id)
            if item.status != "pending":
                return item
            address = single_recipient(item.to)
            if address is None or address not in self.allowlist:  # allowlist may have changed
                item.status, item.note = "blocked_allowlist", "Địa chỉ không còn được phép."
            elif self.sent_today() >= self.daily_limit:
                item.status, item.note = "over_limit", "Đã hết hạn mức thư trong ngày."
            else:
                try:
                    item.note = self.sender.send(address, item.subject, item.body + self.footer)
                    item.status = "sent"
                except SendError as exc:
                    item.status, item.note = "failed", str(exc)
        self._log(item)
        return item

    def reject(self, item_id: str) -> OutboxItem:
        with self._lock:
            item = self._get(item_id)
            if item.status == "pending":
                item.status, item.note = "rejected", "Người dùng hủy."
        self._log(item)
        return item

    def _log(self, item: OutboxItem) -> None:
        if self.log_path is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
