"""Case-level counts on Test-4 for the v3 paper (counts only, no case content).

Reads the summary block of every ``results/rebuild_c/test4_<cfg>_<model>_eval_v3.json`` of the
three open backbones and sums the per-backbone counts per configuration. Output:
``results/rebuild_c/paper_v3_case_counts_v1.json``. The numbers go to
``docs/paper/iccies2027/facts.md`` (section "Bổ sung cho bài v3").
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "rebuild_c"
OUT = RESULTS / "paper_v3_case_counts_v1.json"
MODELS = ("qwen35_9b", "gemma4_12b", "llama31_8b")
CONFIGS = (
    "A0", "P1", "P2", "G1", "MEL", "PRG", "R1", "D2", "D2P2",
    "V3P2", "V3P2-C1", "V3P2-C2", "V3P2-C3",
)
KEYS = (
    "attack_harmful_fixtures_transformed",
    "attack_harmful_fixtures_verbatim",
    "attack_final_leaks_verbatim",
    "attack_tampered",
    "attack_sink_violations",
    "attack_read_violations",
    "benign_plain_utility",
    "benign_auth_utility",
    "false_block_any_denial",
    "confirmation_rate_benign",
    "confirmation_rate_attack",
)


def _count(value: object) -> tuple[int, int | None]:
    """'k/n' -> (k, n); a bare integer -> (k, None)."""
    if isinstance(value, int):
        return value, None
    k, n = str(value).split("/")
    return int(k), int(n)


def main() -> None:
    out: dict[str, dict[str, object]] = {}
    lines: list[str] = []
    for cfg in CONFIGS:
        per_model: dict[str, dict[str, object]] = {}
        pooled: dict[str, list[int | None]] = {}
        for model in MODELS:
            path = RESULTS / f"test4_{cfg}_{model}_eval_v3.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["executions"] != 560:
                raise SystemExit(f"{path.name}: {data['executions']} executions, expected 560")
            (summary,) = data["summary"].values()
            per_model[model] = {key: summary[key] for key in KEYS}
            for key in KEYS:
                k, n = _count(summary[key])
                acc = pooled.setdefault(key, [0, 0 if n is not None else None])
                acc[0] = (acc[0] or 0) + k
                if n is not None and acc[1] is not None:
                    acc[1] += n
        pooled_row = {
            key: (f"{k}/{n}" if n is not None else k) for key, (k, n) in pooled.items()
        }
        out[cfg] = {"per_model": per_model, "pooled": pooled_row}
        shown = (
            "attack_harmful_fixtures_transformed",
            "attack_harmful_fixtures_verbatim",
            "attack_final_leaks_verbatim",
            "false_block_any_denial",
            "confirmation_rate_benign",
        )
        lines.append(" ".join([cfg, *(f"{key}={pooled_row[key]}" for key in shown)]))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
