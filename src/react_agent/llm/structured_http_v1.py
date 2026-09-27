"""Host backend for the source/session/content-bound structured inference service."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import TypeAdapter

from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.http_diagnostic_v1 import APIError, Transport, strict_object
from react_agent.schemas.agent_output import ActionTurn, FinalTurn
from react_agent.security_v1.guard import parse_guard
from react_agent.serving.structured_api_v1 import (
    AGENT_SCHEMA,
    GUARD_SCHEMA,
    PROFILE,
    canonical,
    sha,
)


class StructuredHTTPBackend:
    def __init__(self, transport: Transport, *, model: str, role: str, session_id: str,
                 source_commit: str, model_revision: str, worker_sha256: str) -> None:
        if role not in {"agent", "guard"} or not model_revision.startswith("sha256:"):
            raise ValueError("role and content-addressed model required")
        self.transport, self.role = transport, role
        self.model_id, self.model_revision = model, model_revision
        self.session_id, self.source_commit = session_id, source_commit
        self.worker_sha256 = worker_sha256
        self.calls: list[dict[str, Any]] = []
        self.attempts = 0

    def probe(self) -> dict[str, Any]:
        value = self.transport("GET", "/models", None)
        expected = {"profile": PROFILE, "session_id": self.session_id, "role": self.role,
                    "source_commit": self.source_commit, "model_revision": self.model_revision,
                    "worker_sha256": self.worker_sha256}
        if any(value.get(k) != v for k, v in expected.items()):
            raise APIError("STRUCTURED_IDENTITY_MISMATCH")
        if value.get("data") != [{"id": self.model_id, "object": "model"}]:
            raise APIError("MODEL_MISMATCH")
        if value.get("capabilities", {}).get("json_schema") is not True:
            raise APIError("SCHEMA_CAPABILITY_MISSING")
        files = value.get("model_fingerprint", {}).get("files")
        if not isinstance(files, dict) or "sha256:" + sha(canonical(files).encode()) != (
            self.model_revision
        ):
            raise APIError("MODEL_FINGERPRINT_MISMATCH")
        return value

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if config.temperature != 0:
            raise APIError("GREEDY_REQUIRED")
        schema = GUARD_SCHEMA if self.role == "guard" else AGENT_SCHEMA
        payload = {"model": self.model_id, "messages": messages, "seed": config.seed,
                   "temperature": 0, "max_tokens": config.max_new_tokens, "stream": False,
                   "request_id": uuid.uuid4().hex}
        self.attempts += 1
        result = self.transport("POST", "/chat/completions", payload)
        if any(result.get(k) != v for k, v in {
            "profile": PROFILE, "session_id": self.session_id, "model": self.model_id,
            "model_revision": self.model_revision}.items()):
            raise APIError("STRUCTURED_RESPONSE_IDENTITY")
        execution = result.get("execution", {})
        if (execution.get("constrained_decoding") is not True
                or execution.get("schema_sha256") != sha(canonical(schema).encode())
                or execution.get("seed") != config.seed):
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
            "execution": execution, "usage": result.get("usage"),
            "model_revision": self.model_revision, "session_id": self.session_id})
        return ModelResponse(text=text, model_id=self.model_id, model_revision=self.model_revision)
