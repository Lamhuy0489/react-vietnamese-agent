"""Agent backend for a vLLM OpenAI-compatible server with schema-constrained output."""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import TypeAdapter, ValidationError

from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.http_diagnostic_v1 import APIError, Transport, strict_object
from react_agent.schemas.agent_output import ActionTurn, FinalTurn
from react_agent.serving.structured_api_v1 import AGENT_SCHEMA

# Transport failures are infrastructure; the task may be rerun. Everything else
# raised by generate() is a model failure and stays in the denominator.
INFRA_CODES = frozenset({"NETWORK_ERROR", "TIMEOUT", "TLS_ERROR", "INVALID_RESPONSE",
                         "RESPONSE_TOO_LARGE"})
INFRA_STATUSES = frozenset({429, 502, 503, 504, 530})


class InfrastructureError(APIError):
    """Endpoint unavailable; not a model outcome."""


def served_name(repo: str, revision: str) -> str:
    return f"{repo}@{revision}"


def per_tool_schema(tool_definitions: list[dict[str, Any]]) -> dict[str, Any]:
    """One anyOf branch per tool, so arguments are constrained by that tool's input schema.

    The transport serialises with sorted keys, so "arguments" is generated before
    "name"; with a free-form ``arguments`` object some models emit ``{}`` or wrong
    keys. Per-tool branches bind the two whatever the key order (decision log
    2026-10-26).
    """
    def strip(schema: Any) -> Any:
        if isinstance(schema, dict):
            return {k: strip(v) for k, v in schema.items() if k not in {"title", "default"}}
        return schema

    branches = [
        {"type": "object", "additionalProperties": False, "required": ["action"],
         "properties": {"action": {
             "type": "object", "additionalProperties": False, "required": ["name", "arguments"],
             "properties": {"name": {"type": "string", "enum": [tool["name"]]},
                            "arguments": strip(tool["input_schema"])}}}}
        for tool in tool_definitions
    ]
    return {"anyOf": [*branches, AGENT_SCHEMA["anyOf"][1]]}


class OpenAICompatBackend:
    def __init__(self, transport: Transport, *, repo: str, revision: str,
                 chat_template_kwargs: dict[str, Any] | None = None,
                 tool_definitions: list[dict[str, Any]] | None = None,
                 response_schema: dict[str, Any] | None = None) -> None:
        if not repo or len(revision) < 7:
            raise ValueError("repo and pinned revision required")
        self.transport = transport
        self.model_id, self.model_revision = repo, revision
        self.served = served_name(repo, revision)
        self.chat_template_kwargs = chat_template_kwargs or {}
        if tool_definitions and response_schema:
            raise ValueError("tool_definitions and response_schema are exclusive")
        # A guard backend passes its own output schema; agent backends constrain to actions.
        self.schema = response_schema or (
            per_tool_schema(tool_definitions) if tool_definitions else AGENT_SCHEMA)
        self.schema_name = "guard_verdict" if response_schema else "agent_turn"
        self.calls: list[dict[str, Any]] = []
        self.infra_failures = 0

    def _send(self, method: str, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        try:
            return self.transport(method, path, payload)
        except APIError as exc:
            if exc.code in INFRA_CODES or exc.status in INFRA_STATUSES:
                self.infra_failures += 1
                raise InfrastructureError(exc.code, exc.status) from None
            raise

    def probe(self) -> dict[str, Any]:
        value = self._send("GET", "/models", None)
        ids = [item.get("id") for item in value.get("data", []) if isinstance(item, dict)]
        if ids != [self.served]:
            raise APIError("MODEL_MISMATCH")
        return value

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if config.temperature != 0:
            raise APIError("GREEDY_REQUIRED")
        request_id = uuid.uuid4().hex
        payload: dict[str, Any] = {
            "model": self.served, "messages": messages, "temperature": 0,
            "seed": config.seed, "max_tokens": config.max_new_tokens, "stream": False,
            "request_id": request_id,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": self.schema_name, "schema": self.schema, "strict": True}},
        }
        if self.chat_template_kwargs:
            payload["chat_template_kwargs"] = self.chat_template_kwargs
        started = time.monotonic()
        result = self._send("POST", "/chat/completions", payload)
        record: dict[str, Any] = {"request_id": request_id, "usage": result.get("usage"),
                                  "seconds": round(time.monotonic() - started, 3)}
        self.calls.append(record)
        try:
            choices = result["choices"]
            if result.get("model") != self.served or len(choices) != 1:
                raise APIError("RESPONSE_IDENTITY")
            record["finish_reason"] = choices[0].get("finish_reason")
            if record["finish_reason"] == "length":
                raise APIError("OUTPUT_TRUNCATED")
            if record["finish_reason"] != "stop":
                raise APIError("OUTPUT_INCOMPLETE")
            text = choices[0]["message"]["content"]
            TypeAdapter(ActionTurn | FinalTurn).validate_python(strict_object(text))
        except (KeyError, TypeError, IndexError, ValueError, ValidationError):
            record["error"] = "OUTPUT_INVALID"
            raise APIError("OUTPUT_INVALID") from None
        except APIError as exc:
            record["error"] = exc.code
            raise
        return ModelResponse(text=text, model_id=self.model_id, model_revision=self.model_revision)
