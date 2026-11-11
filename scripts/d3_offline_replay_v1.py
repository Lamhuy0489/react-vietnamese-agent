#!/usr/bin/env python3
"""D3 design on Dev: replay candidate sink rules over recorded Dev v3 trajectories (no GPU).

Study 2 D3 (decision log 2026-11-09 "D3 trên Dev"). For each Dev run of a source
configuration (default ``D2NRP2``: D2 rules 1-4 without the A1 rule layer, so the model's
sink proposals are not shaped by that layer), the recorded observations
(``artifacts.jsonl``; the same ``raw_json`` the runtime policy saw) and sink proposals are
replayed in creation order through candidate pre-sink rules:

- ``A1``: frozen A1 rule layer (``rules_v1`` signals, v4 anchors) as in D2;
- ``TAINT``: A1 denies only if the payload carries a value from a flagged artifact that
  the user text does not contain (narrowed A1);
- ``DEST``: A1 denies only if a flagged artifact itself mentions the sink destination
  (untrusted data giving instructions about the user's own sink);
- ``R3``: D2 rule 3 as frozen; ``R3C``: rule 3 with compact matching (diacritics,
  spaces and punctuation removed; values of at least 6 compact characters).

Outputs counts per branch and the fixtures each rule changes against the recorded run:
benign sink proposals newly denied (utility risk) and attack fixtures harmful in the
source run that the rule would block (harm prevented). The replay is counterfactual only
for the first deny (the model's reaction to a denial is not simulated). Dev only.
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import Sensitivity, Trust
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.authorization_anchors_v4 import extract_anchors
from react_agent.security_v1.contracts import PolicyObservation
from react_agent.security_v1.control_data_policy_v1 import (
    SINK_DESTINATION,
    ControlDataState,
    _flatten,
    normalise,
    sensitive_values,
)
from react_agent.security_v1.rules import RuleGuard

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results/rebuild_b"
MODELS = ("gemma4_12b", "llama31_8b", "qwen35_9b")
RULES = ("A1", "TAINT", "DEST", "R3", "R3C")


def compact(text: str) -> str:
    """Casefold, strip diacritics (đ -> d), keep letters and digits only."""
    text = unicodedata.normalize("NFKD", normalise(text).replace("đ", "d"))
    return "".join(ch for ch in text if ch.isalnum() and not unicodedata.combining(ch))


def compact_leaks(text: str, protected: set[str], user_text: str) -> list[str]:
    hay, user = compact(text), compact(user_text)
    return sorted(v for v in protected
                  if len(c := compact(v)) >= 6 and c in hay and c not in user)


def replay(folder: Path) -> list[dict[str, Any]]:
    """One record per sink proposal: rule verdicts and whether it ran in the source run."""
    sec = [json.loads(line) for line in
           (folder / "execution/trace_security.jsonl").read_text(encoding="utf-8").splitlines()]
    data = [(e["event"], json.loads(e["data_json"]) if isinstance(e["data_json"], str)
             else e["data_json"]) for e in sec]
    proposals = {d["artifact_id"]: d for ev, d in data if ev == "proposal"}
    executed = {d["proposal_id"] for ev, d in data if ev == "broker_result"}
    arts = [json.loads(line) for line in (folder / "execution/artifacts/artifacts.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    user = next(a for a in arts if a["artifact_type"] == "USER_INPUT"
                and a["source_type"] == "USER")
    user_text = json.loads(user["raw_json"])
    # Sources the policy observes (same set as rule_signal ids when the rule layer is on).
    observed = {a["artifact_id"] for a in arts if a["producer"] == "tool_source_snapshot"}
    state = ControlDataState(user_text)
    guard, anchors = RuleGuard(), extract_anchors(user_text)
    flagged: list[str] = []
    out = []
    for art in arts:
        aid = art["artifact_id"]
        if aid in observed:
            content = art["raw_json"]
            obs = PolicyObservation(artifact_id=aid, content=content,
                                    source_type=art["source_type"],
                                    sensitivity=Sensitivity(art["sensitivity"]),
                                    trust=Trust(art["trust"]))
            state.observe(aid, content, obs.sensitivity)
            if guard.scan(obs).matched_rule_ids:
                flagged.append(content)
            continue
        prop = proposals.get(aid)
        if prop is None or prop["action"]["name"] not in SINK_DESTINATION:
            continue
        action = Action.model_validate(prop["action"])
        key = SINK_DESTINATION[action.name]
        dest = _flatten(action.arguments.get(key))
        payload = _flatten({k: v for k, v in action.arguments.items() if k != key})
        d2 = state.check_action(action)
        signal = bool(flagged)
        flagged_values = set().union(*(sensitive_values(c) for c in flagged)) if flagged else set()
        user_n = normalise(user_text)
        out.append({
            "executed": prop["proposal_id"] in executed,
            "rule2": bool(d2 and d2[0] == "UNTRUSTED_CONTROL_INFLUENCE"),
            "A1": signal and not anchors.authorizes(action),
            "TAINT": signal and any(v in normalise(payload) and v not in user_n
                                    for v in flagged_values),
            "DEST": signal and bool(normalise(dest).strip()) and any(
                normalise(dest).strip().rstrip("/.") in normalise(c) for c in flagged),
            "R3": bool(d2 and d2[0] == "PROVENANCE_SENSITIVE_PAYLOAD"),
            "R3C": bool(compact_leaks(payload, state.protected, user_text)),
        })
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", default="D2NRP2")
    p.add_argument("--output", type=Path, default=RES / "v3_dev_d3_replay.json")
    args = p.parse_args()
    table: dict[str, Counter[str]] = defaultdict(Counter)
    ids: dict[str, list[str]] = defaultdict(list)
    for m in MODELS:
        run = RES / f"v3_dev_{args.source}_{m}"
        recs = {r["variant_id"]: r for r in json.loads(
            (RES / f"v3_dev_{args.source}_{m}_eval.json").read_text())["records"]}
        for vid, r in recs.items():
            folder = run / "runs" / r["level"] / vid
            sinks = [s for s in replay(folder) if not s["rule2"]]  # rule 2 denies regardless
            branch = r["branch"]
            harmful = bool(r["score"]["side_effect_harm_v3"])
            ok = bool(r["score"]["utility"])
            for rule in RULES:
                hit = any(s[rule] for s in sinks)
                if not hit:
                    continue
                if branch == "attack":
                    tag = "attack_harmful_blocked" if harmful else "attack_other"
                    table[rule][tag] += 1
                    if harmful:
                        ids[f"{rule}|{m}|{r['mechanism']}"].append(vid)
                else:
                    tag = f"{branch}_{'ok' if ok else 'fail'}_denied"
                    table[rule][tag] += 1
                    if ok:
                        ids[f"{rule}|{m}|{branch}"].append(vid)
            if branch == "attack" and harmful:
                table["_source"]["attack_harmful"] += 1
            if branch != "attack" and ok:
                table["_source"][f"{branch}_ok"] += 1
    result = {"source": args.source, "split": "dev", "counts": {k: dict(v) for k, v in
                                                                 table.items()},
              "ids": dict(ids)}
    args.output.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    for k, v in sorted(table.items()):
        print(k, dict(sorted(v.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
