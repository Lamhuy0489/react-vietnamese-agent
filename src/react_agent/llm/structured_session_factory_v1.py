"""Picklable HTTP factory: TLS and credential loading occur in the owning process."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.llm.http_diagnostic_v1 import HTTPSJSON, APIError
from react_agent.llm.session_journal_v1 import SessionJournal
from react_agent.llm.structured_http_v1 import StructuredHTTPBackend
from react_agent.serving.structured_api_v1 import sha


@dataclass(frozen=True)
class StructuredSessionFactory:
    directory: Path
    journal_root: Path
    task_id: str
    role: str
    connection_sha256: str
    metadata_sha256: str
    timeout_seconds: float
    model_id: str
    model_revision: str
    session_id: str
    source_commit: str
    worker_sha256: str

    @classmethod
    def from_directory(cls, directory: Path, journal_root: Path, task_id: str,
                       role: str, *, timeout_seconds: float = 150) -> StructuredSessionFactory:
        if role not in {"agent", "guard"}:
            raise ValueError("agent or guard required")
        directory = directory.resolve()
        config_path = directory / "pair_endpoints.json"
        metadata_path = directory / f"{role}_live_metadata.json"
        config = json.loads(config_path.read_text())
        rows = [r for r in config["models"] if r["role"] == role]
        if len(rows) != 1:
            raise ValueError("exactly one role required")
        row = rows[0]
        meta = json.loads(metadata_path.read_text())
        return cls(directory, journal_root.resolve(), task_id, role,
            sha(config_path.read_bytes()), sha(metadata_path.read_bytes()), timeout_seconds,
            row["id"], row["model_revision"], row["session_id"], row["source_commit"],
            meta["worker_sha256"])

    def public_identity(self) -> dict[str, str]:
        return {key: str(getattr(self, key)) for key in (
            "role", "model_id", "model_revision", "session_id", "source_commit", "worker_sha256")}

    def __call__(self) -> StructuredHTTPBackend:
        config_path = self.directory / "pair_endpoints.json"
        metadata_path = self.directory / f"{self.role}_live_metadata.json"
        if (config_path.is_symlink() or metadata_path.is_symlink()
                or sha(config_path.read_bytes()) != self.connection_sha256
                or sha(metadata_path.read_bytes()) != self.metadata_sha256):
            raise APIError("CONNECTION_FILES_CHANGED")
        rows: list[dict[str, Any]] = json.loads(config_path.read_text())["models"]
        matches = [r for r in rows if r["role"] == self.role]
        if len(matches) != 1:
            raise APIError("CONNECTION_ROLE_MISMATCH")
        row = matches[0]
        if any(row[k] != getattr(self, v) for k, v in (
            ("id", "model_id"), ("model_revision", "model_revision"),
            ("session_id", "session_id"), ("source_commit", "source_commit"))):
            raise APIError("CONNECTION_IDENTITY_MISMATCH")
        transport = SessionJournal(HTTPSJSON(row["endpoint"], row["api_key"],
            timeout=self.timeout_seconds), self.journal_root, self.public_identity(), self.task_id)
        backend = StructuredHTTPBackend(transport, model=self.model_id, role=self.role,
            session_id=self.session_id, source_commit=self.source_commit,
            model_revision=self.model_revision, worker_sha256=self.worker_sha256)
        backend.probe()
        return backend
