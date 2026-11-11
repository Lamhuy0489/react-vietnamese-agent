#!/usr/bin/env python3
"""Exploratory post-Test analysis of Test v3 Tier 1 (counts, rule codes and IDs only; no text).

Not a tuning input: final_config_v3 stays frozen; findings feed the discussion and future work.
For each (config, model) it joins ``v3_test_<CFG>_<K>_eval.json`` with the security trace of
each fixture and classifies:

- utility losses against A0 on benign_plain / benign_auth (fixture OK at A0, not OK here):
  which layer denied a sink (A1 rule layer = rule 5, D2 rule 2 destination, D2 rule 3 payload),
  final-answer redaction (rule 4), run status (truncated, max steps, model error) or none
  (the model just answered differently);
- attack fixtures still harmful under D2P2: mechanism, variant, harm channel.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results/rebuild_b"
MODELS = ("gemma4_12b", "llama31_8b", "qwen35_9b")
CONFIGS = ("A0", "R1", "P2", "PRG", "D2", "D2P2")
LAYER = {
    "UNAUTHORIZED_EXTERNAL_ACTION": "A1 rule layer (rule 5)",
    "RULE_INJECTION_SIGNAL": "A1 rule layer (rule 5)",
    "UNTRUSTED_CONTROL_INFLUENCE": "D2 rule 2 (destination)",
    "PROVENANCE_SENSITIVE_PAYLOAD": "D2 rule 3 (payload value)",
}


def trace_facts(run: Path, level: str, vid: str) -> dict[str, Any]:
    path = run / "runs" / level / vid / "execution/trace_security.jsonl"
    deny: Counter[str] = Counter()
    redacted = False
    components: Counter[str] = Counter()
    if not path.is_file():
        return {"deny": deny, "redacted": False, "components": components, "trace": False}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["event"] != "decision":
            continue
        data = row["data_json"]
        data = json.loads(data) if isinstance(data, str) else data
        reasons = [str(r) for r in data.get("reasons", [])]
        if data.get("effect") == "DENY":
            components[str(data.get("component"))] += 1
            for r in reasons:
                deny[LAYER.get(r, r)] += 1
        if "PROVENANCE_SENSITIVE_FINAL" in reasons:
            redacted = True
    return {"deny": deny, "redacted": redacted, "components": components, "trace": True}


def cause(rec: dict[str, Any], facts: dict[str, Any]) -> str:
    status = rec["score"]["status"]
    if facts["deny"]:
        layers = sorted(set(facts["deny"]))
        return " + ".join(layers)
    if facts["redacted"]:
        return "D2 rule 4 (final redaction)"
    if status != "completed":
        return f"status {status}"
    return "no block (model output differs)"


def load(cfg: str, model: str) -> tuple[Path, dict[str, dict[str, Any]]]:
    data = json.loads((RES / f"v3_test_{cfg}_{model}_eval.json").read_text(encoding="utf-8"))
    return RES / f"v3_test_{cfg}_{model}", {r["variant_id"]: r for r in data["records"]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=RES / "v3_test_error_analysis.json")
    args = p.parse_args()
    out: dict[str, Any] = {"note": "exploratory, post-Test; no tuning", "losses": {}, "leaks": {},
                           "status": {}, "denials_on_benign": {}}
    base = {m: load("A0", m)[1] for m in MODELS}
    for cfg in CONFIGS:
        for m in MODELS:
            run, recs = load(cfg, m)
            level = next(iter(recs.values()))["level"]
            out["status"][f"{cfg}/{m}"] = dict(Counter(
                f"{r['branch']}:{r['score']['status']}" for r in recs.values()
                if r["score"]["status"] != "completed"))
            if cfg == "A0":
                continue
            loss: dict[str, Counter[str]] = defaultdict(Counter)
            gain: Counter[str] = Counter()
            ids: dict[str, list[str]] = defaultdict(list)
            benign_deny: Counter[str] = Counter()
            for vid, r in recs.items():
                if r["branch"] == "attack":
                    continue
                facts = trace_facts(run, level, vid)
                for layer in facts["deny"]:
                    benign_deny[f"{r['branch']}: {layer}"] += 1
                if facts["redacted"]:
                    benign_deny[f"{r['branch']}: D2 rule 4 (final redaction)"] += 1
                a0, now = base[m][vid]["score"]["utility"], r["score"]["utility"]
                if a0 and not now:
                    c = cause(r, facts)
                    loss[r["branch"]][c] += 1
                    ids[f"{r['branch']}|{c}"].append(vid)
                elif now and not a0:
                    gain[r["branch"]] += 1
            out["losses"][f"{cfg}/{m}"] = {
                "lost_vs_A0": {b: dict(c) for b, c in loss.items()},
                "gained_vs_A0": dict(gain), "ids": dict(ids)}
            out["denials_on_benign"][f"{cfg}/{m}"] = dict(benign_deny)
            if cfg == "D2P2":
                leaks = []
                for vid, r in recs.items():
                    s = r["score"]
                    if r["branch"] == "attack" and s["side_effect_harm_v3"]:
                        channel = ("executed sink" if s["executed_violations"] else
                                   "tampered" if s["tampered"] else
                                   "leaked final" if s["leaked"] else "other")
                        leaks.append({"variant_id": vid, "family": r["family_id"],
                                      "mechanism": r["mechanism"], "channel": channel,
                                      "status": s["status"],
                                      "denied_any": bool(trace_facts(run, level, vid)["deny"])})
                out["leaks"][m] = leaks
    args.output.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for key, v in out["losses"].items():
        if key.split("/")[0] in ("D2", "D2P2", "P2"):
            print(key, "lost", v["lost_vs_A0"], "gained", v["gained_vs_A0"])
    for m, leaks in out["leaks"].items():
        print("D2P2 leaks", m, len(leaks), Counter((x["mechanism"], x["channel"]) for x in leaks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
