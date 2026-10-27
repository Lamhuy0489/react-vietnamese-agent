"""Opt-in Plan transport for the field bridge; frozen action client stays intact."""

from __future__ import annotations

import json
import uuid
from typing import Any

from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.http_diagnostic_v1 import APIError, strict_object
from react_agent.llm.structured_http_v1 import StructuredHTTPBackend
from react_agent.prototypes.field_reference_v1 import Plan
from react_agent.serving.structured_api_v1 import PROFILE, canonical, sha


def plan_schema() -> dict[str, Any]:
    """Inline the finite Plan schema for the existing worker's no-$ref contract."""
    raw = Plan.model_json_schema()
    definitions = raw.pop("$defs", {})

    def expand(value: Any, active: tuple[str, ...] = ()) -> Any:
        if isinstance(value, list):
            return [expand(item, active) for item in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            ref = value["$ref"]
            if not isinstance(ref, str) or not ref.startswith("#/$defs/") or ref in active:
                raise ValueError("finite local schema required")
            name = ref.removeprefix("#/$defs/")
            if name not in definitions:
                raise ValueError("unknown schema reference")
            return expand({**definitions[name], **{k: v for k, v in value.items()
                                                  if k != "$ref"}}, (*active, ref))
        return {key: expand(item, active) for key, item in value.items()}

    schema: dict[str, Any] = expand(raw)
    if len(canonical(schema).encode()) > 32768:
        raise ValueError("inline schema budget exceeded")
    return schema


class StructuredPlanHTTPBackend(StructuredHTTPBackend):
    """Untrusted typed proposals only; this adapter never grants release authority."""

    _probed = False

    def probe(self) -> dict[str, Any]:
        self._probed = False
        if self.role != "agent":
            raise APIError("PLAN_AGENT_REQUIRED")
        result = super().probe()
        self._probed = True
        return result

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        if not self._probed or self.role != "agent":
            raise APIError("PLAN_PROBE_REQUIRED")
        if config.temperature != 0 or not 1 <= config.max_new_tokens <= 1024:
            raise APIError("PLAN_GENERATION_BOUNDS")
        schema = plan_schema()
        payload = {"model": self.model_id, "messages": messages, "seed": config.seed,
                   "temperature": 0, "max_tokens": config.max_new_tokens, "stream": False,
                   "request_id": uuid.uuid4().hex, "response_format": {
                       "type": "json_schema", "json_schema": {
                           "name": "field_plan_v1", "strict": True, "schema": schema}}}
        self.attempts += 1
        result = self.transport("POST", "/chat/completions", payload)
        if any(result.get(k) != v for k, v in {
            "profile": PROFILE, "session_id": self.session_id, "model": self.model_id,
            "model_revision": self.model_revision}.items()):
            raise APIError("STRUCTURED_RESPONSE_IDENTITY")
        execution = result.get("execution", {})
        if (not isinstance(execution, dict) or execution.get("constrained_decoding") is not True
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
            # JSON-mode validation accepts arrays for tuple fields without Python coercions.
            value = strict_object(text)
            Plan.model_validate_json(json.dumps(value))
        except (KeyError, TypeError, ValueError, IndexError):
            raise APIError("STRUCTURED_PLAN_INVALID") from None
        self.calls.append({"request_id": payload["request_id"],
            "request_sha256": sha(canonical(payload).encode()),
            "execution": execution, "usage": result.get("usage"),
            "model_revision": self.model_revision, "session_id": self.session_id})
        return ModelResponse(text=text, model_id=self.model_id, model_revision=self.model_revision)
