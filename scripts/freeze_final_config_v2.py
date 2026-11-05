#!/usr/bin/env python3
"""Write ``configs/final/final_config_v2.json`` (rebuild A freeze for Test-2 and clean Test).

Run only after the owner approves the decisions below; print them with ``--show``.
Refuses to overwrite an existing manifest: a later change needs a new, recorded version.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import react_agent.evaluation.final_config_v2 as final_config_v2

ROOT = Path(__file__).resolve().parents[1]

DECISIONS: dict[str, Any] = {
    "date": "2026-11-05",
    "agent": "configs/agent/A0.yaml",
    "generation": "configs/runtime/default.yaml",
    "models_config": "configs/models/backbones_v2.yaml (repo + revision pinned)",
    "prompt": "a0_rebuild v3",
    "decoding_schema": "per_tool_v2_name_first",
    "test2": {
        "inputs": "data/adversarial/release_test2 (seal 1576b89a..., 100 attack + 100 benign)",
        "environment": "E2 (doc_search_v2) for every configuration",
        "backbone": "qwen3_8b",
        "guard": "guard_candidates.llama32_3b_prompted, frozen A2 risk-to-action mapping",
        "matrix": {"A0": "phase5_closure_runtime_v1",
                   "A1": "phase5_closure_runtime_v1",
                   "A6": "phase5_closure_runtime_v1 + a6_provenance_v3",
                   "D2": "runtime_d2_v1 + control_data_policy_v1 (Dev round 1, A1 config)",
                   "D2+G": "D2 with the guard on (A2 config)"},
        "runs": "5 x 200 = 1,000, once; runner run_adversarial_e2_api_v1.py --release test2",
        "evaluator": "evaluate_adversarial_test2_v1.py (test2_eval_v1: score_scoped security, "
                     "tolerant typed utility, side_effect_harm_v1)",
        "primary": ["D2 vs A0: paired side-effect ASR (expect lower)",
                    "D2 vs A6: benign utility (expect higher) and paired side-effect ASR "
                    "(expect not higher; failed on Dev, reported as is)"],
        "secondary": ["v1 paired ASR", "false-block rate", "utility under attack",
                      "D2 vs D2+G", "A0 vs A1", "A1 vs A6"],
    },
    "clean": {
        "backbones": ["qwen3_8b", "llama31_8b", "gemma4_12b"],
        "canonical": "data/clean/v1_1 test split (100) + configs/clean/test_fault_plans_v1.json; "
                     "run_clean_robustness_api_v1.py --set canonical --split test (RQ1)",
        "robustness": "data/clean/robustness_v1 (seal 942b69bb..., 250 = 50 x 5 types); "
                      "run_clean_robustness_api_v1.py --set robustness --split test (RQ3)",
        "evaluator": "evaluate_clean_robustness_v1.py (clean_rebuild_v1 numfix; "
                     "variant scored with its canonical ground truth; paired lost/gained)",
    },
    "unchanged": "final_config_v1 and its R4 Test v1 results stay as frozen and reported",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approved-by")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    if args.show or not args.approved_by:
        print(json.dumps(DECISIONS, ensure_ascii=False, indent=1))
        return 0
    path = ROOT / final_config_v2.MANIFEST
    if path.exists():
        raise SystemExit(f"{final_config_v2.MANIFEST} exists; a change needs a new version")
    manifest = final_config_v2.build(ROOT, DECISIONS | {"approved_by": args.approved_by})
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(len(manifest["files"]), "files pinned; sha256", final_config_v2.manifest_sha256(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
