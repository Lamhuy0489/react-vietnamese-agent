"""BrokerGuard v3 as AgentDojo pipeline elements (generalisation check, design section 5).

Built on the v1 adapter (``agentdojo_brokerguard_v1``: sink map, confidential read tools,
R-Signal, D2 rule 3, repeat_user_prompt, final redaction), changed only where v3 changes v1,
as in ``security_v3/brokerguard_v3_v1.py``:

- **C1** replaces R-Dest. A sink with a destination runs only if that destination occurs in
  the user query as a whole token (after the frozen ``intent_policy_v1`` normalisation: NFKC,
  casefold, Vietnamese marks stripped, trailing punctuation and "/" dropped) and no occurrence
  lies in a negation or exclusion scope of its clause (the frozen ``NEGATION``, ``EXCLUSION``
  and ``CONTRAST`` cue lists; a contrast cue ends the scope). Substring hits (the v1 collision)
  do not count. AgentDojo destinations are IBANs, Slack users and channels, URLs and e-mail
  addresses, which the frozen extractor (e-mail and endpoint targets of the main benchmark)
  does not recognise, so the whole-token test is done here; there is no sending-verb
  requirement and no quoted/reported-speech rule (AgentDojo queries are short imperatives).
  Destination-less sinks (``update_password``, ``update_user_info``) are outside C1, as in v1.
- **C2** adds the frozen value labels (``value_labels_v1.label_values``) of every tool output,
  independently of the source, checked with ``flows`` at every non-destination argument and
  redacted in the final answer. v1's source-based protection stays.
- **C3** pins, with the frozen ``param_pinning_v1.pins``, the literals of the clause of u that
  granted the destination; a call missing one of them is denied.

The mapping is declared in ``docs/project/decision_log.md`` (2026-11-18) before any run.
Stateless: every decision is recomputed from the query and the message list.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for extra in (ROOT / "src", ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import agentdojo_brokerguard_v1 as v1  # noqa: E402

from react_agent.security_v1.control_data_policy_v1 import (  # noqa: E402
    destination_allowed,
    leaked_values,
    redact,
)
from react_agent.security_v3 import intent_policy_v1 as ip  # noqa: E402
from react_agent.security_v3 import param_pinning_v1 as pp  # noqa: E402
from react_agent.security_v3 import value_labels_v1 as vl  # noqa: E402

ALL_COMPONENTS = frozenset({"C1", "C2", "C3"})
DENIAL_PREFIX = v1.DENIAL_PREFIX


def _target(value: str) -> str:
    return ip.strip_marks(ip.normalise_target(value))


def _segments(pattern: re.Pattern[str], text: str, start: int, end: int) -> list[tuple[int, int]]:
    out, cursor = [], start
    for m in pattern.finditer(text, start, end):
        if m.start() > cursor:
            out.append((cursor, m.start()))
        cursor = max(cursor, m.end())
    if cursor < end:
        out.append((cursor, end))
    return out


_CLAUSE_SPLIT = re.compile(rf",|{ip.CLAUSE.pattern}")


def _negated(t: Any, start: int, end: int) -> bool:
    """Does a negation/exclusion cue in [start, end) still hold at ``end``? Ambiguous Vietnamese
    words are resolved by the frozen ``_Text.word_ok`` (original spelling when u has marks)."""
    cues = []
    for pattern, kind in (
        (ip.NEGATION, "neg"),
        (ip.EXCLUSION, "neg"),
        (ip.CONTRAST, "end"),
        (ip.NOT_NEGATION, "end"),
    ):
        for m in pattern.finditer(t.plain, start, end):
            if t.word_ok(m.start(), m.end(), m.end()):
                cues.append((m.start(), kind))
    return bool(cues) and max(cues)[1] == "neg"


def grant(destination: str, query: str) -> tuple[str, str] | None | bool:
    """(sentence, clause) of an allowed occurrence; False if forbidden; None if absent."""
    target = _target(destination)
    if not target:
        return None
    t = ip._Text(query)
    token = re.compile(rf"(?<![\w@.-]){re.escape(target)}(?![\w@-])")
    found: tuple[str, str] | None = None
    for s0, s1 in _segments(ip.SENTENCE, t.plain, 0, len(t.plain)):
        for c0, c1_ in _segments(_CLAUSE_SPLIT, t.plain, s0, s1):
            for m in token.finditer(t.plain, c0, c1_):
                if _negated(t, c0, m.start()):
                    return False
                clause = t.plain[c0 : m.start()] + " " + t.plain[m.end() : c1_]
                found = found or (t.plain[s0:s1], clause)
    return found


def c1(function: str, args: dict[str, Any], query: str) -> tuple[str | None, Any]:
    key = v1.SINKS[function]
    dest = v1._flatten(args.get(key)) if key else ""
    if not key or (not dest and function == "update_scheduled_transaction"):
        return None, None
    verdict = grant(dest, query)
    if verdict is False:
        return "C1: destination excluded or negated by the user", None
    if verdict is None:
        return "C1: destination not granted by the user", None
    return None, verdict


def c2_protected(messages: Sequence[Any]) -> set[str]:
    values: set[str] = set()
    for _name, text in v1._tool_outputs(messages):
        values |= set(vl.label_values(text))
    return values


def c3(function: str, args: dict[str, Any], granted: tuple[str, str]) -> str | None:
    sentence, clause = granted
    key = v1.SINKS[function]
    pseudo = ip.Grant(
        tool=function,
        target="",
        polarity=ip.Polarity.ALLOW,
        clause=0,
        text=clause,
        sentence=sentence,
    )
    pinned = pp.pins(pseudo)
    parts = [v1._flatten(v) for k, v in args.items() if k != key]
    # AgentDojo passes amounts as numbers (98.7 for the user's "98.70"): render them both ways.
    parts += [
        f"{v:.2f}"
        for k, v in args.items()
        if k != key and isinstance(v, (int, float)) and not isinstance(v, bool)
    ]
    payload = vl.compact(" ".join(parts))
    missing = [v for v in pinned.literals if v not in payload]
    return f"C3: user-stated value changed ({len(missing)})" if missing else None


def check(
    function: str,
    args: dict[str, Any],
    query: str,
    messages: Sequence[Any],
    components: frozenset[str] = ALL_COMPONENTS,
) -> str | None:
    """Reason string to deny a sink call, or None to allow."""
    if function not in v1.SINKS:
        return None  # reads are never blocked
    key = v1.SINKS[function]
    dest = v1._flatten(args.get(key)) if key else ""
    granted = None
    if "C1" in components:
        reason, granted = c1(function, args, query)
        if reason:
            return reason
    elif key and (dest or function != "update_scheduled_transaction"):
        if not destination_allowed(dest, query):
            return "R-Dest: destination not written by the user"
    payload = v1._flatten({k: v for k, v in args.items() if k != key})
    if leaked_values(payload, v1.protected_values(messages), query):
        return "R-Flow: confidential value not written by the user"
    if "C2" in components and vl.flows(payload, c2_protected(messages), query):
        return "C2: labelled value not written by the user"
    if "C3" in components:
        if granted is None and key and dest:
            found = grant(dest, query)
            granted = found if isinstance(found, tuple) else None
        if granted is not None:
            reason = c3(function, args, granted)
            if reason:
                return reason
    if v1.flagged(messages) and not v1.grammar_allows(function, args, query):
        return "R-Signal: a tool output looked like an injected instruction"
    return None


def redact_final(
    text: str, messages: Sequence[Any], query: str, components: frozenset[str] = ALL_COMPONENTS
) -> tuple[str, int]:
    leaked = leaked_values(text, v1.protected_values(messages), query)
    out = redact(text, leaked) if leaked else text
    n = len(leaked)
    if "C2" in components:
        extra = vl.flows(out, c2_protected(messages), query)
        if extra:
            out, n = vl.redact(out, extra), n + len(extra)
    return out, n


def build_pipeline(
    llm: Any,
    system_message: str | None,
    tool_output_formatter: Any = None,
    components: frozenset[str] = ALL_COMPONENTS,
) -> Any:
    """Layout as v1: SystemMessage, InitQuery, llm, loop[Executor, InitQuery, llm], Redactor."""
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

    class BrokerGuardV3Executor(BasePipelineElement):  # type: ignore[misc]
        def __init__(self) -> None:
            self.inner = ToolsExecutor(tool_output_formatter or tool_result_to_str)

        def query(
            self,
            query: str,
            runtime: Any,
            env: Any,
            messages: Sequence[Any] = (),
            extra_args: dict[str, Any] | None = None,
        ) -> tuple[Any, ...]:
            extra = extra_args if extra_args is not None else {}
            if (
                not messages
                or messages[-1]["role"] != "assistant"
                or not messages[-1].get("tool_calls")
            ):
                return query, runtime, env, messages, extra
            allowed: list[tuple[Any, str | None]] = []
            denied: list[tuple[Any, str | None]] = []
            for call in messages[-1]["tool_calls"]:
                reason = check(call.function, dict(call.args), query, messages, components)
                (denied if reason else allowed).append((call, reason))
            last = dict(messages[-1])
            last["tool_calls"] = [c for c, _ in allowed]
            q, runtime, env, out, extra = self.inner.query(
                query, runtime, env, [*messages[:-1], last], extra
            )
            results = list(out[len(messages) :])
            for call, reason in denied:
                results.append(
                    ChatToolResultMessage(
                        role="tool",
                        content=[text_content_block_from_string("")],
                        tool_call_id=call.id,
                        tool_call=call,
                        error=f"{DENIAL_PREFIX} ({reason}). The tool was not executed. "
                        "Continue with the rest of the user's task.",
                    )
                )
            order = {c.id: i for i, c in enumerate(messages[-1]["tool_calls"])}
            results.sort(key=lambda m: order.get(m["tool_call_id"], 0))
            extra.setdefault("brokerguard_denials", []).extend((c.function, r) for c, r in denied)
            return q, runtime, env, [*messages, *results], extra

    class Redactor(BasePipelineElement):  # type: ignore[misc]
        def query(
            self,
            query: str,
            runtime: Any,
            env: Any,
            messages: Sequence[Any] = (),
            extra_args: dict[str, Any] | None = None,
        ) -> tuple[Any, ...]:
            extra = extra_args if extra_args is not None else {}
            if not messages or messages[-1]["role"] != "assistant":
                return query, runtime, env, messages, extra
            text = v1._text(messages[-1].get("content"))
            out, n = redact_final(text, messages, query, components)
            if not n:
                return query, runtime, env, messages, extra
            last = dict(messages[-1])
            last["content"] = [text_content_block_from_string(out)]
            extra["brokerguard_redacted"] = n
            return query, runtime, env, [*messages[:-1], last], extra

    loop = ToolsExecutionLoop([BrokerGuardV3Executor(), InitQuery(), llm])
    return AgentPipeline([SystemMessage(system_message), InitQuery(), llm, loop, Redactor()])
