#!/usr/bin/env python3
"""Audit AgentDojo BrokerGuard runs: denials per rule, redactions, API errors (tool names only).

Reads ``results/rebuild_b/agentdojo_*_brokerguard_<K>/logs`` transcripts; prints counts, never
message text. Usage: python scripts/agentdojo_bg_audit_v1.py [--model-key llama31_8b]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-key", default="llama31_8b")
    args = ap.parse_args()
    out = {}
    for d in sorted((ROOT / "results/rebuild_b").glob(f"agentdojo_*_brokerguard_{args.model_key}")):
        files = [p for p in (d / "logs").rglob("*.json")]
        rules: Counter[str] = Counter()
        tools: Counter[str] = Counter()
        runs_with_denial = errors = 0
        for p in files:
            data = json.loads(p.read_text())
            if data.get("error"):
                errors += 1
            denied = False
            for m in data.get("messages") or []:
                err = (m.get("error") or "") if m.get("role") == "tool" else ""
                if "BrokerGuard denied" in err:
                    denied = True
                    rules[err.split("(", 1)[1].split(":", 1)[0]] += 1
                    tools[(m.get("tool_call") or {}).get("function", "?")] += 1
            runs_with_denial += denied
        sfile = d / "summary.json"
        summary = json.loads(sfile.read_text()) if sfile.exists() else {}
        out[d.name] = {"transcripts": len(files), "with_denial": runs_with_denial,
                       "denials_by_rule": dict(rules), "denied_tools": dict(tools),
                       "run_errors": errors, "utility": summary.get("utility"),
                       "attack_success": summary.get("attack_success")}
        print(d.name.replace("agentdojo_", "").replace(f"_brokerguard_{args.model_key}", ""),
              json.dumps(out[d.name], ensure_ascii=False))
    (ROOT / "results/rebuild_b" / f"agentdojo_brokerguard_audit_{args.model_key}.json").write_text(
        json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
