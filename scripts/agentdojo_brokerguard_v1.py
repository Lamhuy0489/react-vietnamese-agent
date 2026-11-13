"""BrokerGuard (D2+P2) as AgentDojo pipeline elements (paper reviewer C10).

Reuses the frozen D2 rule code unchanged (``security_v1.control_data_policy_v1`` for R-Dest,
R-Flow, R-Redact and ``security_v1.rules`` for the R-Signal detector and the user grammar).
Only the adapter below is new: which AgentDojo tools are sinks, which argument is the
destination, and which read outputs are confidential. The mapping is declared in
``docs/project/decision_log.md`` (2026-11-13) before any defended run.

The prompt layer is AgentDojo's own ``repeat_user_prompt`` (the user query is repeated after
every tool round), so the defended run differs from the existing ``repeat_user_prompt`` run
only by the broker rules.

Stateless across tasks: every decision is recomputed from the query and the message list,
so one pipeline instance can serve the whole suite.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from react_agent.security_v1.control_data_policy_v1 import (  # noqa: E402
    destination_allowed,
    leaked_values,
    redact,
    sensitive_values,
)
from react_agent.security_v1.rules import (  # noqa: E402
    CONTROL,
    EMAIL,
    ENDPOINT,
    OVERRIDE,
    SEND,
    extract_anchors,
)

# Sink -> destination argument (None: state change without a destination, R-Dest not applied).
SINKS: dict[str, str | None] = {
    # banking
    "send_money": "recipient",
    "schedule_transaction": "recipient",
    "update_scheduled_transaction": "recipient",  # only checked when a recipient is given
    "update_password": None,
    "update_user_info": None,
    # slack
    "send_direct_message": "recipient",
    "send_channel_message": "channel",
    "post_webpage": "url",
    "invite_user_to_slack": "user_email",
    "add_user_to_channel": "user",
    "remove_user_from_slack": "user",
}
# Read tools whose output holds the user's private data (sensitivity, independent of trust).
CONFIDENTIAL = {
    "get_iban", "get_balance", "get_most_recent_transactions", "get_scheduled_transactions",
    "get_user_info", "read_inbox", "read_channel_messages",
}
# Every tool output is untrusted for the R-Signal detector (third parties write into all of
# them: files, web pages, transaction subjects, channel messages).
DENIAL_PREFIX = "BrokerGuard denied this call"


def _text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return "\n".join(str(b.get("content") or "") for b in content if isinstance(b, dict))


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(_flatten(v) for v in value)
    return "" if value is None else str(value)


def _tool_outputs(messages: Sequence[Any]) -> list[tuple[str, str]]:
    out = []
    for m in messages:
        if m.get("role") == "tool" and not m.get("error"):
            call = m.get("tool_call")
            name = getattr(call, "function", "") if call is not None else ""
            out.append((name, _text(m.get("content"))))
    return out


def protected_values(messages: Sequence[Any]) -> set[str]:
    values: set[str] = set()
    for name, text in _tool_outputs(messages):
        if name in CONFIDENTIAL:
            values |= sensitive_values(text)
    return values


def flagged(messages: Sequence[Any]) -> bool:
    """R-Signal detector of D2 (rules_v1 RuleGuard patterns), every output untrusted."""
    for _, text in _tool_outputs(messages):
        if OVERRIDE.search(text) or CONTROL.search(text):
            return True
        if SEND.search(text) and (EMAIL.search(text) or ENDPOINT.search(text)):
            return True
    return False


def grammar_allows(function: str, args: dict[str, Any], query: str) -> bool:
    """D2's strict user grammar: authorises only e-mail/endpoint destinations it can parse."""
    anchors = extract_anchors(query)
    key = SINKS.get(function)
    dest = _flatten(args.get(key)) if key else ""
    return bool(dest) and (dest in anchors.emails or dest in anchors.endpoints)


def check(function: str, args: dict[str, Any], query: str,
          messages: Sequence[Any]) -> str | None:
    """Reason string to deny a sink call, or None to allow."""
    if function not in SINKS:
        return None  # reads are never blocked
    key = SINKS[function]
    dest = _flatten(args.get(key)) if key else ""
    if key and (dest or function != "update_scheduled_transaction"):
        if not destination_allowed(dest, query):
            return "R-Dest: destination not written by the user"
    payload = _flatten({k: v for k, v in args.items() if k != key})
    if leaked_values(payload, protected_values(messages), query):
        return "R-Flow: confidential value not written by the user"
    if flagged(messages) and not grammar_allows(function, args, query):
        return "R-Signal: a tool output looked like an injected instruction"
    return None


def build_pipeline(llm: Any, system_message: str | None, tool_output_formatter: Any = None) -> Any:
    """SystemMessage, InitQuery, llm, loop[BrokerGuardExecutor, InitQuery, llm], Redactor."""
    from agentdojo.agent_pipeline.agent_pipeline import (  # type: ignore[import-not-found]
        AgentPipeline,
    )
    from agentdojo.agent_pipeline.base_pipeline_element import (  # type: ignore[import-not-found]
        BasePipelineElement,
    )
    from agentdojo.agent_pipeline.basic_elements import (  # type: ignore[import-not-found]
        InitQuery,
        SystemMessage,
    )
    from agentdojo.agent_pipeline.tool_execution import (  # type: ignore[import-not-found]
        ToolsExecutionLoop,
        ToolsExecutor,
        tool_result_to_str,
    )
    from agentdojo.types import (  # type: ignore[import-not-found]
        ChatToolResultMessage,
        text_content_block_from_string,
    )

    class BrokerGuardExecutor(BasePipelineElement):  # type: ignore[misc]
        def __init__(self) -> None:
            self.inner = ToolsExecutor(tool_output_formatter or tool_result_to_str)

        def query(self, query: str, runtime: Any, env: Any, messages: Sequence[Any] = (),
                  extra_args: dict[str, Any] | None = None) -> tuple[Any, ...]:
            extra = extra_args if extra_args is not None else {}
            if not messages or messages[-1]["role"] != "assistant" or not messages[-1].get(
                    "tool_calls"):
                return query, runtime, env, messages, extra
            allowed: list[tuple[Any, str | None]] = []
            denied: list[tuple[Any, str | None]] = []
            for call in messages[-1]["tool_calls"]:
                reason = check(call.function, dict(call.args), query, messages)
                (denied if reason else allowed).append((call, reason))
            last = dict(messages[-1])
            last["tool_calls"] = [c for c, _ in allowed]
            q, runtime, env, out, extra = self.inner.query(
                query, runtime, env, [*messages[:-1], last], extra)
            results = list(out[len(messages):])
            for call, reason in denied:
                results.append(ChatToolResultMessage(
                    role="tool", content=[text_content_block_from_string("")],
                    tool_call_id=call.id, tool_call=call,
                    error=f"{DENIAL_PREFIX} ({reason}). The tool was not executed. "
                          "Continue with the rest of the user's task."))
            # keep the original assistant message (all calls) in the transcript
            order = {c.id: i for i, c in enumerate(messages[-1]["tool_calls"])}
            results.sort(key=lambda m: order.get(m["tool_call_id"], 0))
            extra.setdefault("brokerguard_denials", []).extend(
                (c.function, r) for c, r in denied)
            return q, runtime, env, [*messages, *results], extra

    class Redactor(BasePipelineElement):  # type: ignore[misc]
        """R-Redact: replace confidential values the user did not write in the final answer."""

        def query(self, query: str, runtime: Any, env: Any, messages: Sequence[Any] = (),
                  extra_args: dict[str, Any] | None = None) -> tuple[Any, ...]:
            extra = extra_args if extra_args is not None else {}
            if not messages or messages[-1]["role"] != "assistant":
                return query, runtime, env, messages, extra
            text = _text(messages[-1].get("content"))
            leaked = leaked_values(text, protected_values(messages), query)
            if not leaked:
                return query, runtime, env, messages, extra
            last = dict(messages[-1])
            last["content"] = [text_content_block_from_string(redact(text, leaked))]
            extra["brokerguard_redacted"] = len(leaked)
            return query, runtime, env, [*messages[:-1], last], extra

    loop = ToolsExecutionLoop([BrokerGuardExecutor(), InitQuery(), llm])
    return AgentPipeline([SystemMessage(system_message), InitQuery(), llm, loop, Redactor()])
