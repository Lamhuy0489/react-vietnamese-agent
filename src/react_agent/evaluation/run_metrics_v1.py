"""Per-execution cost and behaviour metrics (BrokerGuard v3 protocol, design doc §5).

Two sources, both observable (no hidden reasoning, no private ground truth):

1. **LLM calls** recorded by every ``OpenAICompatBackend`` in the backend stack
   (``calls``: usage, seconds, finish_reason, error). :class:`CallWindow` snapshots the
   stack before an execution and returns only the calls made during it, split by role:
   ``agent`` (the model reached through the wrapper chain) and one role per auxiliary
   backend (sanitizer, guard, ...). Extra agent calls made by a defense (MELON re-runs)
   show up as agent calls beyond the agent's own turns.
2. **Traces** written by the runtime: ``trace_legacy.jsonl`` (timestamped model, tool and
   final events) and ``trace_security.jsonl`` (gate decisions). :func:`trace_metrics`
   derives steps, tool calls by outcome, gate decisions by component/effect/reason,
   denials, redaction of the final answer and a time split into model, tool, gate and
   other runtime time.

Everything is computed after the execution from saved files plus the call window, so
the agent's behaviour is unchanged by measurement.
"""

from __future__ import annotations

import json
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

METRICS_VERSION = "run_metrics_v1"
SINK_TOOLS = frozenset({"send_email_mock", "post_webhook_mock"})
CONFIRM_REASONS = frozenset({"CONFIRMATION_REQUIRED", "INTENT_UNCLEAR"})
_LINK_NAMES = ("inner", "_inner", "backend", "_backend", "sanitizer", "_sanitizer",
               "guard", "_guard")


def recorded_backends(backend: Any) -> list[tuple[str, Any]]:
    """(role, backend) for every object with a ``calls`` list in the stack.

    The role is ``agent`` for the chain of wrappers reached through ``inner``-like
    attributes, otherwise the attribute name that leads to it (``sanitizer``, ...).
    """
    found: list[tuple[str, Any]] = []
    seen: set[int] = set()
    lists: set[int] = set()  # wrappers forward ``calls`` to their inner backend: count once

    def walk(obj: Any, role: str) -> None:
        if obj is None or id(obj) in seen:
            return
        seen.add(id(obj))
        calls = getattr(obj, "calls", None)
        if isinstance(calls, list) and id(calls) not in lists:
            lists.add(id(calls))
            found.append((role, obj))
        for name in _LINK_NAMES:
            child = getattr(obj, name, None)
            if child is not None and hasattr(child, "generate"):
                walk(child, role if name in ("inner", "_inner", "backend", "_backend")
                     else name.lstrip("_"))

    walk(backend, "agent")
    return found


class CallWindow:
    """Calls made by the backend stack between :meth:`open` and :meth:`close`."""

    def __init__(self, backend: Any) -> None:
        self.backends = recorded_backends(backend)
        self._start: list[int] = []

    def open(self) -> None:
        self._start = [len(b.calls) for _, b in self.backends]

    def close(self) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        for (role, b), start in zip(self.backends, self._start, strict=True):
            out.setdefault(role, []).extend(dict(c) for c in b.calls[start:])
        return out


def _usage(calls: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = completion = 0
    missing = 0
    for c in calls:
        u = c.get("usage") or {}
        if not u:
            missing += 1
        prompt += int(u.get("prompt_tokens") or 0)
        completion += int(u.get("completion_tokens") or 0)
    return {"calls": len(calls), "prompt_tokens": prompt, "completion_tokens": completion,
            "total_tokens": prompt + completion, "calls_without_usage": missing,
            "seconds": round(sum(float(c.get("seconds") or 0) for c in calls), 3),
            "finish_reasons": dict(Counter(str(c.get("finish_reason")) for c in calls)),
            "errors": dict(Counter(str(c["error"]) for c in calls if c.get("error")))}


def _ts(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def _lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def trace_metrics(execution: Path) -> dict[str, Any]:
    """Steps, tool outcomes, gate decisions and a time split from one execution's traces."""
    legacy = _lines(execution / "trace_legacy.jsonl")
    security = [e | {"data": json.loads(e["data_json"])}
                for e in _lines(execution / "trace_security.jsonl")]
    kinds = Counter(e["event"] for e in legacy)
    proposed = {e["call_id"]: e for e in legacy if e["event"] == "tool_call_proposed"}
    executed = {e["call_id"]: e for e in legacy if e["event"] == "tool_call_executed"}
    results = {e["call_id"]: e for e in legacy if e["event"] == "tool_result"}
    ok = {c for c, e in results.items() if e["data"].get("ok")}
    names = {c: e["data"]["name"] for c, e in proposed.items()}

    gate_s = tool_s = 0.0
    for call, e in proposed.items():  # proposed -> executed: PRE gate; executed -> result: tool
        if call in executed:
            gate_s += _ts(executed[call]["timestamp"]) - _ts(e["timestamp"])
            if call in results:
                tool_s += _ts(results[call]["timestamp"]) - _ts(executed[call]["timestamp"])
        elif call in results:  # denied before execution: the whole span is gate time
            gate_s += _ts(results[call]["timestamp"]) - _ts(e["timestamp"])
    start = next((e for e in legacy if e["event"] == "run_start"), None)
    end = next((e for e in reversed(legacy) if e["event"] == "run_end"), None)
    wall = _ts(end["timestamp"]) - _ts(start["timestamp"]) if start and end else None

    decisions = [e["data"] for e in security if e["event"] == "decision"]
    non_allow = [d for d in decisions if d.get("effect") != "ALLOW"]
    reasons = Counter(r for d in non_allow for r in d.get("reasons", []))
    denied_calls = {d.get("proposal_id") for d in decisions
                    if d.get("effect") == "DENY" and d.get("stage") == "PRE"}
    proposed_final = [e["data"] for e in security if e["event"] == "proposed_final"]
    released_final = [e["data"] for e in security if e["event"] == "released_final"]
    final_redacted = any(d.get("effect") == "REDACT" for d in decisions
                         if d.get("stage") == "FINAL")
    rule_hits = sum(bool(e["data"].get("matched_rule_ids")) for e in security
                    if e["event"] == "rule_signal")
    status = (end or {}).get("data", {}).get("status")
    gate_props = {e["data"].get("proposal_id"): e["data"].get("action", {}).get("name")
                  for e in security if e["event"] == "proposal"}
    denied_names = [gate_props.get(p) for p in denied_calls - {None}]
    return {
        "status": status,
        "agent_turns": kinds["model_output"],
        "tool_calls": {
            "proposed_to_gate": len(gate_props) if security else len(proposed),
            "passed_gate": len(proposed), "executed_ok": len(ok),
            "failed_or_denied": len(proposed) - len(ok),
            "by_tool": dict(Counter(names.values())),
            "sink_proposed": sum(n in SINK_TOOLS for n in names.values()),
            "sink_executed": sum(names[c] in SINK_TOOLS for c in ok if c in names),
            "denied_by_tool": dict(Counter(str(n) for n in denied_names)),
            "sink_denied": sum(n in SINK_TOOLS for n in denied_names)},
        "gate": {
            "decisions": len(decisions),
            "by_component_effect": dict(Counter(
                f"{d.get('component')}:{d.get('stage')}:{d.get('effect')}" for d in decisions)),
            "non_allow": len(non_allow), "non_allow_reasons": dict(reasons),
            "denied_proposals": len(denied_calls - {None}),
            "confirmation_required": sum(reasons[r] for r in CONFIRM_REASONS),
            "rule_signal_hits": rule_hits,
            "final_proposed": len(proposed_final), "final_released": len(released_final),
            "final_redacted": final_redacted},
        "seconds": {
            "wall_trace": None if wall is None else round(wall, 3),
            "gate_pre": round(gate_s, 3), "tool": round(tool_s, 3)},
    }


def execution_metrics(execution: Path, calls: dict[str, list[dict[str, Any]]],
                      wall_seconds: float) -> dict[str, Any]:
    """Full metrics record for one execution (written next to ``result.json``)."""
    trace = trace_metrics(execution)
    llm = {role: _usage(items) for role, items in sorted(calls.items())}
    all_calls = [c for items in calls.values() for c in items]
    total = _usage(all_calls)
    agent_calls = llm.get("agent", {}).get("calls", 0)
    llm_s = total["seconds"]
    other = wall_seconds - llm_s - trace["seconds"]["tool"]
    return {
        "metrics_version": METRICS_VERSION,
        "wall_seconds": round(wall_seconds, 3),
        "llm": llm, "llm_total": total,
        # None when the backend records no calls (dry run): no claim about extra calls
        "defense_extra_llm_calls": total["calls"] - trace["agent_turns"] if all_calls else None,
        "agent_calls_beyond_turns": agent_calls - trace["agent_turns"] if all_calls else None,
        **trace,
        "seconds_split": {"llm": llm_s, "tool": trace["seconds"]["tool"],
                          "gate_pre": trace["seconds"]["gate_pre"],
                          "runtime_other": round(other, 3)},
    }


def _dist(values: list[float]) -> dict[str, float | int]:
    if not values:
        return {"n": 0}
    ordered = sorted(values)

    def q(p: float) -> float:
        return round(ordered[min(len(ordered) - 1, int(p * (len(ordered) - 1) + 0.5))], 3)

    return {"n": len(values), "mean": round(statistics.fmean(values), 3),
            "median": q(0.5), "p90": q(0.9), "p95": q(0.95), "max": round(ordered[-1], 3),
            "sum": round(sum(values), 3)}


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Distributions over executions of one group (e.g. one level and branch)."""
    def col(f: Any) -> list[float]:
        return [float(v) for r in records if (v := f(r)) is not None]

    return {
        "executions": len(records),
        "prompt_tokens": _dist(col(lambda r: r["llm_total"]["prompt_tokens"])),
        "completion_tokens": _dist(col(lambda r: r["llm_total"]["completion_tokens"])),
        "total_tokens": _dist(col(lambda r: r["llm_total"]["total_tokens"])),
        "llm_calls": _dist(col(lambda r: r["llm_total"]["calls"])),
        "defense_extra_llm_calls": _dist(col(lambda r: r["defense_extra_llm_calls"])),
        "agent_turns": _dist(col(lambda r: r["agent_turns"])),
        "tool_calls_proposed": _dist(col(lambda r: r["tool_calls"]["proposed_to_gate"])),
        "sink_denied": _dist(col(lambda r: r["tool_calls"]["sink_denied"])),
        "wall_seconds": _dist(col(lambda r: r["wall_seconds"])),
        "llm_seconds": _dist(col(lambda r: r["seconds_split"]["llm"])),
        "tool_seconds": _dist(col(lambda r: r["seconds_split"]["tool"])),
        "gate_pre_seconds": _dist(col(lambda r: r["seconds_split"]["gate_pre"])),
        "runtime_other_seconds": _dist(col(lambda r: r["seconds_split"]["runtime_other"])),
        "executions_with_denial": sum(r["gate"]["denied_proposals"] > 0 for r in records),
        "executions_with_confirmation": sum(r["gate"]["confirmation_required"] > 0
                                            for r in records),
        "executions_with_final_redaction": sum(bool(r["gate"]["final_redacted"])
                                               for r in records),
        "non_allow_reasons": dict(sum((Counter(r["gate"]["non_allow_reasons"])
                                       for r in records), Counter())),
        "calls_without_usage": sum(r["llm_total"]["calls_without_usage"] for r in records),
        "statuses": dict(Counter(str(r["status"]) for r in records)),
    }
