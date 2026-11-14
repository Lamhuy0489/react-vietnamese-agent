#!/usr/bin/env python3
"""Paper revision (review 3, items 1-2): why each harmful BrokerGuard (D2P2) attack case passed.

Counts only. Reads frozen traces and the evaluator oracle, prints and stores category counts,
never fixture or payload text. For every executed violating sink call the frozen scorer reports,
the cause is one of:
- dest_plain_word_in_u / dest_address_in_u: R-Dest allowed a destination the oracle does not grant,
  because it occurs in u (a plain word or an address);
- value_source_public: the leaked value is in a format the extractor recognises, but every source
  snapshot holding it before the call was labelled public (S0), so it never entered C;
- value_in_c_later, value_in_u, value_in_dest_field, value_not_extractable,
  value_in_c_unblocked;
- tamper_on_granted_dest: H_tamper on a granted destination (outside the value rules by design).
Final-answer leaks are classified the same way with a ``final:`` prefix.
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evaluate_v3_v1 as ev  # noqa: E402

from react_agent.authoring.data_scope import score_scoped  # noqa: E402
from react_agent.schemas.trace import TraceEvent  # noqa: E402
from react_agent.security_v1.control_data_policy_v1 import (  # noqa: E402
    SINK_DESTINATION,
    _flatten,
    destination_allowed,
    normalise,
    sensitive_values,
)

RES = ROOT / "results" / "rebuild_b"
MECH = {"M1": "ER", "M2": "CR", "M3": "SL", "M4": "AL", "M5": "PT", "M6": "US"}
ADDRESS = re.compile(r"@|https?://|\.[a-z]{2,}(/|$)")
SPLITS = {"test": "v3_test", "test3": "v3_test3"}


def _value_cause(v: str, raw: str, user: str, payload: str | None,
                 seen: set[str], seen_all: set[str]) -> str:
    if v in normalise(user):
        return "value_in_u"
    if payload is not None and v not in payload:
        return "value_in_dest_field"
    if not sensitive_values(raw):
        return "value_not_extractable"
    if v in seen:
        return "value_in_c_unblocked"
    return "value_in_c_later" if v in seen_all else "value_source_public"


def case_causes(folder: Path, private: Any) -> set[str]:
    evs = [TraceEvent.model_validate_json(x) for x in
           (folder / "execution/trace_legacy.jsonl").read_text().splitlines() if x]
    arts = [json.loads(x) for x in
            (folder / "execution/artifacts/artifacts.jsonl").read_text().splitlines() if x]
    user_art = json.loads(next(a["raw_json"] for a in arts if a["source_type"] == "USER"))
    user = user_art if isinstance(user_art, str) else json.dumps(user_art, ensure_ascii=False)
    snaps = [a for a in arts
             if a["producer"] == "tool_source_snapshot" and a["sensitivity"] == "S2"]

    def c_before(step: int | None) -> set[str]:
        out: set[str] = set()
        for a in snaps:
            if step is None or a["created_step"] < step:
                out |= sensitive_values(a["raw_json"])
        return out

    seen_all = c_before(None)
    oracle = private.oracle
    s = score_scoped(evs, oracle, folder / "environment/database/university.db")
    props = {str(e.call_id): e for e in evs if e.event == "tool_call_proposed"}
    done = {str(e.call_id) for e in evs if e.event == "tool_result" and e.data["ok"]}
    causes: set[str] = set()
    for cid, d in s["scope_decisions"].items():
        if d["status"] != "violation" or cid not in done:
            continue
        name, args = props[cid].data["name"], props[cid].data["arguments"]
        key = SINK_DESTINATION.get(name)
        if key is None:
            causes.add("read_tool")
            continue
        if d["reason"] == "destination_not_authorized":
            dest = normalise(_flatten(args.get(key))).strip()
            if not destination_allowed(dest, user):
                raise SystemExit(f"{folder}: executed destination R-Dest should deny")
            causes.add("dest_address_in_u" if ADDRESS.search(dest) else "dest_plain_word_in_u")
            continue
        content = json.dumps(args, ensure_ascii=False, sort_keys=True)
        payload = normalise(_flatten({k: v for k, v in args.items() if k != key}))
        seen = c_before(props[cid].step)
        for a in oracle.sensitive_artifacts:
            if a.value in content:
                causes.add(_value_cause(normalise(a.value), a.value, user, payload, seen, seen_all))
    for aid in s["final_leaked_artifacts"]:
        a = next(x for x in oracle.sensitive_artifacts if x.artifact_id == aid)
        causes.add("final:" + _value_cause(normalise(a.value), a.value, user, None,
                                           seen_all, seen_all))
    if s["proposed_violations"] == 0 and not s["final_leaked_artifacts"]:
        causes.add("tamper_on_granted_dest")
    return causes


def main() -> int:
    out: dict[str, Any] = {}
    for split, prefix in SPLITS.items():
        privates = ev.load_privates(split)
        table: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
        for f in sorted(RES.glob(f"{prefix}_D2P2_*_eval.json")):
            run = Path(str(f)[: -len("_eval.json")])
            for r in json.loads(f.read_text())["records"]:
                if r["branch"] != "attack" or not r["score"]["side_effect_harm_v3"]:
                    continue
                folder = next(run.glob(f"runs/*/{r['variant_id']}"))
                causes = case_causes(folder, privates[r["family_id"]])
                if r["score"]["tampered"]:
                    causes.add("tamper_on_granted_dest")
                table[MECH[r["mechanism"]]][" + ".join(sorted(causes))] += 1
        out[split] = {m: dict(c) for m, c in sorted(table.items())}
        total = sum(sum(c.values()) for c in table.values())
        print(split, total)
        for m, c in sorted(table.items()):
            print(f"  {m} {sum(c.values())}: {dict(c)}")
    (RES / "paper_bypass_causes_v1.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
