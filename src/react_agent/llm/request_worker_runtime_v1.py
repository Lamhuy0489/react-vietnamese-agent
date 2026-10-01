"""Structured LLM/runtime wiring over the request-worker v3 lifecycle API.

The factory is safe to serialize: credentials and live sockets are loaded only
inside the owning process.  The backend delegates delivery to the explicit
journal, exposes status/cancel/recovery as separate lifecycle operations, and
keeps the existing structured output validation unchanged.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.http_diagnostic_v1 import APIError, strict_object
from react_agent.llm.request_worker_journal_v1 import RequestWorkerJournal
from react_agent.llm.request_worker_transport_v1 import PROFILE, RequestWorkerHTTPS
from react_agent.schemas.agent_output import ActionTurn, FinalTurn
from react_agent.security_v1.guard import parse_guard
from react_agent.serving.structured_api_v1 import AGENT_SCHEMA, GUARD_SCHEMA, canonical, sha


class RequestWorkerBackend:
    """LLMBackend-compatible facade with explicit remote lifecycle controls."""

    def __init__(self, journal: RequestWorkerJournal, *, model: str, role: str,
                 identity: dict[str, str]) -> None:
        if role not in {"agent", "guard"} or identity != journal.identity:
            raise ValueError("journal and worker identity must agree")
        self.journal, self.model_id, self.role = journal, model, role
        self.model_revision = identity["model_revision"]
        self.session_id = identity["session_id"]
        self.source_commit = identity["source_commit"]
        self.worker_sha256 = identity["worker_sha256"]
        self.instance_id = identity["instance_id"]
        self.calls: list[dict[str, Any]] = []
        self.attempts = 0

    @property
    def identity(self) -> dict[str, str]:
        return dict(self.journal.identity)

    def status(self, request_id: str) -> dict[str, Any]:
        value = self.journal.transport.exchange("GET", f"/requests/{request_id}", None)
        if value.status != 200:
            raise APIError("STATUS_UNAVAILABLE", value.status)
        if value.payload.get("identity") != self.identity:
            raise APIError("WORKER_RESPONSE_IDENTITY")
        return dict(value.payload)

    def cancel(self, request_id: str) -> dict[str, Any]:
        value = self.journal.transport.exchange("POST", f"/requests/{request_id}/cancel", None)
        if value.status >= 400 and value.payload.get("identity") != self.identity:
            raise APIError("CANCEL_FAILED", value.status)
        if value.payload.get("identity") != self.identity:
            raise APIError("WORKER_RESPONSE_IDENTITY")
        return dict(value.payload)

    def recover_cached(self, messages: list[dict[str, str]], config: GenerationConfig,
                       request_id: str) -> ModelResponse:
        payload = self._payload(messages, config, request_id)
        result = self.journal.recover_cached(payload)
        return self._parse_result(result, payload)

    def _payload(self, messages: list[dict[str, str]], config: GenerationConfig,
                 request_id: str) -> dict[str, Any]:
        if config.temperature != 0 or not 1 <= config.max_new_tokens <= 1024:
            raise APIError("UNSUPPORTED_GENERATION")
        if (not messages or any(set(message) != {"role", "content"}
                or message["role"] not in {"system", "user", "assistant"}
                or not isinstance(message["content"], str) for message in messages)):
            raise APIError("INVALID_MESSAGES")
        schema = GUARD_SCHEMA if self.role == "guard" else AGENT_SCHEMA
        return {"model": self.model_id, "messages": messages, "seed": config.seed,
                "temperature": 0, "max_tokens": config.max_new_tokens, "stream": False,
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "guard" if self.role == "guard" else "agent",
                    "strict": True, "schema": schema}}, "request_id": request_id}

    def _parse_result(self, envelope: dict[str, Any], payload: dict[str, Any]) -> ModelResponse:
        if envelope.get("identity") != self.identity:
            raise APIError("WORKER_RESPONSE_IDENTITY")
        request = envelope.get("request")
        if not isinstance(request, dict) or request.get("request_id") != payload["request_id"]:
            raise APIError("WORKER_REQUEST_IDENTITY")
        result = envelope.get("result")
        if not isinstance(result, dict) or any(result.get(key) != value for key, value in {
                "profile": "react-vn-structured-api-v1", "model": self.model_id,
                "model_revision": self.model_revision, "session_id": self.session_id,
            }.items()):
            raise APIError("STRUCTURED_RESPONSE_IDENTITY")
        execution = result.get("execution", {})
        schema = GUARD_SCHEMA if self.role == "guard" else AGENT_SCHEMA
        if (execution.get("constrained_decoding") is not True
                or execution.get("schema_sha256") != sha(canonical(schema).encode())
                or execution.get("seed") != payload["seed"]):
            raise APIError("STRUCTURED_EXECUTION_MISMATCH")
        try:
            choices = result["choices"]
            if len(choices) != 1 or choices[0]["finish_reason"] != "stop":
                raise ValueError("completion required")
            message = choices[0]["message"]
            if set(message) != {"role", "content"} or message["role"] != "assistant":
                raise ValueError("observable content only")
            text = message["content"]
            value = strict_object(text)
            if self.role == "guard":
                parse_guard(text)
            else:
                TypeAdapter(ActionTurn | FinalTurn).validate_python(value)
        except (KeyError, TypeError, ValueError, IndexError):
            raise APIError("STRUCTURED_OUTPUT_INVALID") from None
        self.calls.append({"request_id": payload["request_id"],
            "request_sha256": sha(canonical(payload).encode()),
            "response_sha256": request.get("response_sha256"),
            "model_revision": self.model_revision, "session_id": self.session_id})
        return ModelResponse(text=text, model_id=self.model_id,
                             model_revision=self.model_revision)

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        request_id = uuid.uuid4().hex
        payload = self._payload(messages, config, request_id)
        self.attempts += 1
        return self._parse_result(self.journal("POST", "/chat/completions", payload), payload)


@dataclass(frozen=True)
class RequestWorkerSessionFactory:
    """Credential-free picklable factory for one task-bound worker session."""

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
    instance_id: str

    @classmethod
    def from_directory(cls, directory: Path, journal_root: Path, task_id: str,
                       role: str, *, timeout_seconds: float = 90) -> RequestWorkerSessionFactory:
        if role not in {"agent", "guard"}:
            raise ValueError("agent or guard required")
        directory = directory.resolve()
        config_path = directory / "pair_endpoints.json"
        metadata_path = directory / f"{role}_live_metadata.json"
        if config_path.is_symlink() or metadata_path.is_symlink():
            raise ValueError("connection files must be regular files")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        rows = [row for row in config["models"] if row["role"] == role]
        if len(rows) != 1:
            raise ValueError("exactly one role required")
        row = rows[0]
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        identity = metadata.get("identity")
        expected = {"model_id": row["id"], "role": role,
                    **{key: row[key] for key in (
                        "model_revision", "session_id", "source_commit", "worker_sha256")}}
        if (config.get("profile") != PROFILE or metadata.get("profile") != PROFILE
                or metadata.get("status") != "READY" or not isinstance(identity, dict)
                or set(identity) != {*expected, "instance_id"}
                or any(identity.get(key) != value for key, value in expected.items())
                or not isinstance(identity.get("instance_id"), str)
                or not identity["instance_id"]):
            raise ValueError("v3 worker identity metadata mismatch")
        return cls(directory, journal_root.resolve(), task_id, role,
            sha(config_path.read_bytes()), sha(metadata_path.read_bytes()), timeout_seconds,
            row["id"], row["model_revision"], row["session_id"], row["source_commit"],
            row["worker_sha256"], identity["instance_id"])

    def public_identity(self) -> dict[str, str]:
        return {key: str(getattr(self, key)) for key in (
            "model_id", "model_revision", "session_id", "source_commit", "worker_sha256",
            "role", "instance_id")}

    def __call__(self) -> RequestWorkerBackend:
        config_path = self.directory / "pair_endpoints.json"
        metadata_path = self.directory / f"{self.role}_live_metadata.json"
        if (config_path.is_symlink() or metadata_path.is_symlink()
                or sha(config_path.read_bytes()) != self.connection_sha256
                or sha(metadata_path.read_bytes()) != self.metadata_sha256):
            raise APIError("CONNECTION_FILES_CHANGED")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        rows = [row for row in config["models"] if row["role"] == self.role]
        if len(rows) != 1:
            raise APIError("CONNECTION_ROLE_MISMATCH")
        row = rows[0]
        expected = {"model_id": self.model_id, "model_revision": self.model_revision,
                    "session_id": self.session_id, "source_commit": self.source_commit,
                    "worker_sha256": self.worker_sha256, "role": self.role}
        if any(row.get(key if key != "model_id" else "id") != value
               for key, value in expected.items()):
            raise APIError("CONNECTION_IDENTITY_MISMATCH")
        transport = RequestWorkerHTTPS(row["endpoint"], row["api_key"], expected,
                                       timeout=self.timeout_seconds)
        metadata = transport.probe()
        identity = transport.identity
        if identity is None:
            raise APIError("WORKER_IDENTITY_INVALID")
        if identity["instance_id"] != self.instance_id:
            raise APIError("WORKER_BOOT_CHANGED")
        journal = RequestWorkerJournal(transport, self.journal_root, self.task_id)
        if metadata.get("identity") != identity:
            raise APIError("WORKER_IDENTITY_MISMATCH")
        return RequestWorkerBackend(journal, model=self.model_id, role=self.role,
                                    identity=identity)
