"""Durable session admission for HTTP inference, with conservative uncertainty."""
from __future__ import annotations

import fcntl
import json
import os
import re
from pathlib import Path
from typing import Any

from react_agent.llm.http_diagnostic_v1 import APIError, Transport
from react_agent.serving.structured_api_v1 import canonical, sha


def save_new(path: Path, value: dict[str, Any]) -> None:
    # Partial files are deliberately never treated as successful records.
    with path.open("x", encoding="utf-8") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(canonical(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class SessionJournal:
    """No recovery operation clears an uncertain request; a fresh session is distinct."""

    def __init__(self, transport: Transport, root: Path, identity: dict[str, str],
                 task_id: str) -> None:
        if not task_id or len(task_id) > 256 or not identity.get("session_id"):
            raise ValueError("explicit task and session identity required")
        self.transport, self.identity, self.task_id = transport, dict(identity), task_id
        self.root = root.resolve() / sha(canonical(identity).encode())
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise ValueError("journal directory must not be a link")

    def __call__(self, method: str, path: str,
                 payload: dict[str, Any] | None) -> dict[str, Any]:
        if (method, path, payload) == ("GET", "/models", None):
            return self.transport(method, path, payload)
        if method != "POST" or path != "/chat/completions" or payload is None:
            raise APIError("JOURNAL_ROUTE_REFUSED")
        request_id = payload.get("request_id")
        if not isinstance(request_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", request_id):
            raise APIError("JOURNAL_REQUEST_ID_REQUIRED")
        descriptor = os.open(self.root / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise APIError("SESSION_BUSY") from None
            for started in self.root.glob("*.started.json"):
                finished = started.with_name(started.name.replace(".started.", ".finished."))
                try:
                    if started.is_symlink() or finished.is_symlink():
                        raise ValueError("journal records must not be links")
                    record = json.loads(started.read_text())
                    terminal = json.loads(finished.read_text())
                    if (record["identity"] != self.identity
                            or terminal["request_sha256"] != record["request_sha256"]
                            or terminal["request_id"] != record["request_id"]
                            or terminal["state"] != "response_received"):
                        raise ValueError("uncertain or changed history")
                except (OSError, ValueError, KeyError, TypeError):
                    raise APIError("SESSION_UNCERTAIN") from None
            started = self.root / (request_id + ".started.json")
            finished = self.root / (request_id + ".finished.json")
            if started.exists() or finished.exists():
                raise APIError("REQUEST_ALREADY_ATTEMPTED")
            common = {"request_id": request_id, "request_sha256": sha(canonical(payload).encode())}
            save_new(started, {**common, "identity": self.identity, "task_id": self.task_id,
                               "state": "started", "remote_cancellation_supported": False})
            try:
                result = self.transport(method, path, payload)
            except BaseException:
                # Preserve delivery uncertainty on every boundary failure, including interrupts.
                # Bare re-raise retains caller exception semantics; no error text is persisted.
                save_new(finished, {**common, "state": "uncertain"})
                raise
            save_new(finished, {**common, "state": "response_received",
                                "response_sha256": sha(canonical(result).encode())})
            return result
        finally:
            os.close(descriptor)
