"""Meta-SecAlign interface: untrusted data goes in the ``input`` role (Study 2, WP2).

The model card of ``facebook/Meta-SecAlign-8B`` requires every piece of untrusted data
to be sent in a separate ``input`` role after the trusted ``user`` instruction. In the
ReAct context (``agent/context.py``) tool observations are ``user`` messages prefixed
with ``OBSERVATION: ``; this backend moves exactly those messages to ``input`` and leaves
the system prompt, the user instruction, assistant turns and parser corrections
unchanged. It is a harness adaptation to the model's documented interface, applied
only to the SecAlign configuration (decision log 2026-11-05).
"""

from __future__ import annotations

from typing import Any

from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.openai_compat_v1 import OpenAICompatBackend

OBSERVATION_PREFIX = "OBSERVATION: "
UNTRUSTED_ROLE = "input"


def secalign_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Copy of ``messages`` with tool observations in the ``input`` role."""
    out: list[dict[str, str]] = []
    for message in messages:
        if message.get("role") == "user" and message.get("content", "").startswith(
                OBSERVATION_PREFIX):
            out.append({"role": UNTRUSTED_ROLE, "content": message["content"]})
        else:
            out.append(dict(message))
    if out and out[0].get("role") == UNTRUSTED_ROLE:
        raise ValueError("untrusted data cannot precede the trusted instruction")
    return out


class SecAlignInputRoleBackend(OpenAICompatBackend):
    """OpenAI-compatible backend that sends tool observations as ``input``."""

    untrusted_role = UNTRUSTED_ROLE

    def probe(self) -> dict[str, Any]:
        """vLLM lists the base model and the adapter; the adapter must be one of them."""
        value = self._send("GET", "/models", None)
        ids = [item.get("id") for item in value.get("data", []) if isinstance(item, dict)]
        if self.served not in ids or len(ids) != 2:
            raise APIError("MODEL_MISMATCH")
        return value

    def generate(self, messages: list[dict[str, str]], config: Any) -> Any:
        return super().generate(secalign_messages(messages), config)
