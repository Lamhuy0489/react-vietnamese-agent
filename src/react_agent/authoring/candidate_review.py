"""Unsplit candidate pair/group audit and typed-utility authoring checks."""

from __future__ import annotations

import hashlib
import json
from itertools import combinations
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from react_agent.authoring.candidate_qa import Candidate, load_candidates, verify_candidates
from react_agent.authoring.typed_utility import TypedUtility, normalize, score_typed
from react_agent.authoring.workbench_qa import file_hashes
from react_agent.schemas.trace import TraceEvent


def group_audit(candidates: list[Candidate]) -> dict[str, Any]:
    ids = sorted(c.public.task_id for c in candidates)
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("nonempty unique candidate IDs required")
    links: dict[str, set[str]] = {identity: set() for identity in ids}
    pairs: list[dict[str, Any]] = []
    for left, right in combinations(sorted(candidates, key=lambda c: c.public.task_id), 2):
        reasons = []
        if left.metadata.template_group == right.metadata.template_group:
            reasons.append("shared_annotated_template_group")
        if left.metadata.semantic_group == right.metadata.semantic_group:
            reasons.append("shared_annotated_semantic_group")
        if normalize(left.overlay.attack_text) == normalize(right.overlay.attack_text):
            reasons.append("identical_normalized_attack_text")
        a, b = left.public.task_id, right.public.task_id
        if reasons:
            links[a].add(b)
            links[b].add(a)
        shapes = [
            [(act.name, sorted(act.arguments)) for act in c.oracle.negative_actions]
            for c in (left, right)
        ]
        pairs.append(
            {
                "left": a,
                "right": b,
                "grouping_reasons": reasons,
                "same_negative_action_shape_hint": shapes[0] == shapes[1],
            }
        )
    unseen = set(ids)
    units: list[list[str]] = []
    while unseen:
        pending = [min(unseen)]
        component: set[str] = set()
        while pending:
            identity = pending.pop()
            if identity in component:
                continue
            component.add(identity)
            pending.extend(links[identity] - component)
        unseen -= component
        units.append(sorted(component))
    return {
        "candidate_count": len(ids),
        "pairs_examined": len(pairs),
        "review_units": units,
        "review_unit_count": len(units),
        "pairs": pairs,
        "semantic_independence_certified": False,
        "split_ready": False,
        "pair_lengths": [
            {
                "task_id": c.public.task_id,
                "attack_words": len(c.overlay.attack_text.split()),
                "benign_words": len(c.overlay.benign_text.split()),
                "benign_attack_ratio": round(
                    len(c.overlay.benign_text.split()) / max(1, len(c.overlay.attack_text.split())),
                    4,
                ),
                "semantic_pair_review": "pending",
            }
            for c in sorted(candidates, key=lambda c: c.public.task_id)
        ],
    }


def load_utilities(path: Path, candidates: list[Candidate]) -> dict[str, TypedUtility]:
    records = TypeAdapter(list[TypedUtility]).validate_json(path.read_text())
    utilities = {row.task_id: row for row in records}
    if len(utilities) != len(records) or set(utilities) != {c.public.task_id for c in candidates}:
        raise ValueError("missing, extra or duplicate utility/task IDs")
    for candidate in candidates:
        if any(
            fact.evidence_action not in candidate.oracle.safe_actions
            for fact in utilities[candidate.public.task_id].facts
        ):
            raise ValueError("utility evidence action missing from safe path")
    return utilities


def verify_review(inputs: Path, sidecars: Path, clean: Path, output: Path) -> dict[str, Any]:
    if output.resolve().is_relative_to(sidecars.resolve()) or sidecars.resolve().is_relative_to(
        output.resolve()
    ):
        raise ValueError("output must be separate from private sidecars")
    candidates = load_candidates(inputs)
    sidecar_before = file_hashes(sidecars)
    utilities = load_utilities(sidecars / "private/utility.json", candidates)
    replay = verify_candidates(inputs, clean, output)
    by_id = {c.public.task_id: c for c in candidates}
    checks: list[dict[str, Any]] = []
    for fixture in replay["checks"]:
        task = fixture["task_id"]
        directory = output / task / f"{fixture['branch']}_{fixture['fixture']}"
        trace = directory / "trace.jsonl"
        events = [TraceEvent.model_validate_json(line) for line in trace.read_text().splitlines()]
        score = score_typed(
            events,
            by_id[task].oracle,
            utilities[task],
            directory / "environment/database/university.db",
        )
        expected_safe = fixture["fixture"] == "safe"
        if bool(score["safe_utility"]) != expected_safe:
            raise ValueError("typed utility changed expected reference safe/negative outcome")
        if score["unassessed_actions"]:
            raise ValueError("reference script contains unassessed scope")
        checks.append(
            {
                "task_id": task,
                "branch": fixture["branch"],
                "fixture": fixture["fixture"],
                "score": score,
                "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
                "observable_sha256": fixture["observable_sha256"],
            }
        )
    if file_hashes(sidecars) != sidecar_before:
        raise ValueError("private sidecar bytes changed during QA")
    return {
        "valid": True,
        "scope": "candidate review tooling; not dataset acceptance",
        "replay_runs": len(checks),
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "variants_generated": 0,
        "review_status": "pending",
        "split": "unassigned",
        "input_sha256": replay["input_sha256"],
        "sidecar_sha256": sidecar_before,
        "clean_environment_sha256": replay["clean_environment_sha256"],
        "group_audit": group_audit(candidates),
        "checks": checks,
        "runtime_private_boundary": (
            "sidecars never passed to Replay; scored after runtime completes"
        ),
        "typed_presence_is_not_semantic_entailment": True,
        "raw_output": str(output),
        "stable_summary_sha256": hashlib.sha256(
            json.dumps(
                [{k: v for k, v in check.items() if k != "trace_sha256"} for check in checks],
                ensure_ascii=False,
                sort_keys=True,
            ).encode()
        ).hexdigest(),
    }
