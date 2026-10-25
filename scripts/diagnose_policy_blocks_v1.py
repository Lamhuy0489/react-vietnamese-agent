#!/usr/bin/env python3
"""Dev-only policy diagnostic: replay reference actions through A0–A6 without a model.

Benign fixtures replay the oracle's safe actions (any block is a false block);
attack fixtures replay its negative actions (a block is a true block). The guard
always answers SAFE so only rule/session/value policy decisions are measured.
Writes one JSON line per (level, variant) with the denial reasons.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, cast

from react_agent.adversarial_release import load_split
from react_agent.authoring.selected_runtime import load_selected
from react_agent.authoring.workbench_qa import RecordingReplay
from react_agent.evaluation.adversarial_v1 import LEVELS, prepare_registry, score_execution
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.security_v1.contracts import Level, configuration
from react_agent.security_v1.phase5_closure_runtime_v1 import Phase5ClosureRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog

ROOT = Path(__file__).resolve().parents[1]


class SafeGuard:
    model_id, model_revision = "diagnostic/always-safe", "v1"

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        return ModelResponse(text='{"risk":"SAFE","labels":[],"confidence":"HIGH"}',
                             model_id=self.model_id, model_revision=self.model_revision)


class SafeGuardFactory:
    def __call__(self) -> LLMBackend:
        return SafeGuard()


def denials(execution: Path) -> list[dict[str, Any]]:
    out = []
    for line in (execution / "trace_security.jsonl").read_text().splitlines():
        event = json.loads(line)
        if event["event"] == "decision":
            data = json.loads(event["data_json"])
            if data["effect"] == "DENY":
                out.append({"component": data["component"], "stage": data["stage"],
                            "reasons": data["reasons"]})
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--levels", nargs="+", default=list(LEVELS), choices=LEVELS)
    args = parser.parse_args()
    rows = load_split(ROOT / "data/adversarial/release_v2")
    _, cases = load_selected(ROOT)
    reasons: Counter[str] = Counter()
    with args.output.open("w") as stream, tempfile.TemporaryDirectory() as tmp:
        for level in cast(list[Level], args.levels):
            config = configuration(level)
            for row in rows:
                case = cases[row.task.task_id]
                oracle = case.candidate.oracle
                actions, final = ((oracle.safe_actions, oracle.safe_final)
                                  if row.branch == "benign"
                                  else (oracle.negative_actions, oracle.negative_final))
                folder = Path(tmp) / level / row.variant_id
                runtime = Phase5ClosureRuntime(
                    RecordingReplay(actions, final),
                    prepare_registry(row, ROOT / "data/clean/v1_1/environment",
                                     folder / "environment"))
                runtime.run_instrumented(
                    row.task, output=folder / "execution", source_catalog=fixture_catalog(row),
                    security_config=config,
                    guard_factory=SafeGuardFactory() if config.llm_guard else None,
                    guard_execution=WarmGuardConfig(SafeGuard.model_id, SafeGuard.model_revision,
                                                    30) if config.llm_guard else None)
                score = score_execution(case, folder / "execution",
                                        folder / "environment/database/university.db")
                denied = denials(folder / "execution")
                for item in denied:
                    why = "+".join(item["reasons"])
                    reasons[f"{level}:{row.branch}:{item['component']}:{why}"] += 1
                stream.write(json.dumps({
                    "level": level, "variant_id": row.variant_id, "branch": row.branch,
                    "family_id": row.family_id, "task_id": row.task.task_id,
                    "category": row.overlay.attack_category, "sink": [a.name for a in actions
                                                                       if "mock" in a.name],
                    "score": score, "denials": denied}, ensure_ascii=False) + "\n")
    for key, count in reasons.most_common(40):
        print(count, key)


if __name__ == "__main__":
    main()
