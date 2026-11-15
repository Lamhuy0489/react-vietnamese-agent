#!/usr/bin/env python3
"""Trace-only cost metrics for runs made before token logging (``run_v3_api_v1.py`` outputs).

Per level and branch: agent turns, tool calls proposed / denied (sinks apart), gate
decisions, confirmation requests, final redaction and the time split (tool, pre-execution
gate, wall time from trace timestamps). No token counts: the old runner did not log them.
Prints aggregates only.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from react_agent.evaluation import run_metrics_v1 as m


def collect(run: Path) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted(run.glob("runs/*/*/result.json")):
        saved = json.loads(path.read_text())
        t = m.trace_metrics(path.parent / "execution")
        groups[f"{saved['level']}:{saved['branch']}"].append(t)
    out: dict[str, Any] = {}
    for key, rows in sorted(groups.items()):
        def col(f: Any, rows: list[dict[str, Any]] = rows) -> list[float]:
            return [float(v) for r in rows if (v := f(r)) is not None]

        out[key] = {
            "executions": len(rows),
            "agent_turns": m._dist(col(lambda r: r["agent_turns"])),
            "tool_calls_proposed": m._dist(col(lambda r: r["tool_calls"]["proposed_to_gate"])),
            "sink_denied": m._dist(col(lambda r: r["tool_calls"]["sink_denied"])),
            "wall_seconds_trace": m._dist(col(lambda r: r["seconds"]["wall_trace"])),
            "tool_seconds": m._dist(col(lambda r: r["seconds"]["tool"])),
            "gate_pre_seconds": m._dist(col(lambda r: r["seconds"]["gate_pre"])),
            "executions_with_denial": sum(r["gate"]["denied_proposals"] > 0 for r in rows),
            "executions_with_final_redaction": sum(bool(r["gate"]["final_redacted"])
                                                   for r in rows),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs", type=Path, nargs="+")
    args = parser.parse_args(argv)
    print(json.dumps({str(r): collect(r) for r in args.runs}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
