"""Hash-bound whole-pool admission and exact grouped split; no model inference."""

from __future__ import annotations

import hashlib
import json
import math
import re
from itertools import combinations
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from react_agent.authoring.admission_review import evidence_checks, verify_hash_map
from react_agent.authoring.boundary_rules import load_boundary_candidates
from react_agent.authoring.candidate_qa import Candidate, load_candidates
from react_agent.authoring.candidate_review import group_audit
from react_agent.authoring.typed_utility import normalize
from react_agent.authoring.workbench_qa import file_hashes
from react_agent.schemas.adversarial_workbench import StrictRecord


class WholePoolReview(StrictRecord):
    schema_version: Literal["whole_pool_review_v1"]
    review_method: Literal["assistant_self_review_owner_waiver"]
    receipt_path: Literal["experiments/manifests/phase3_boundary_v1_validation01.json"]
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    earlier_review_path: Literal["data/adversarial/admission_review_v1/reviews.json"]
    earlier_review_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    seed: Literal["phase3-canonical-selection-v1"]
    merges: dict[str, str]
    scenario_review: dict[str, str]


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in [*strings(k), *strings(v)]]
    if isinstance(value, list):
        return [s for v in value for s in strings(v)]
    return []


def leakage_keys(candidate: Candidate) -> set[tuple[str, str]]:
    """Internal equality keys only: never serialize private values in reports."""
    keys = {("artifact", a.value) for a in candidate.oracle.sensitive_artifacts}
    keys.add(("source", candidate.overlay.source_id))
    for action in [*candidate.oracle.safe_actions, *candidate.oracle.negative_actions]:
        for value in strings(action.arguments):
            if re.fullmatch(r"[^\s@]+@example\.test|mock://\S+", value):
                keys.add(("destination", value))
            if action.name in {"doc_read", "cached_fetch", "db_query"}:
                keys.update(
                    ("source", s) for s in re.findall(r"\b(?:AWB|AUX|CDOC)_[A-Z0-9]+\b", value)
                )
    return keys


def connected_groups(candidates: list[Candidate]) -> tuple[list[list[str]], list[dict[str, Any]]]:
    audit = group_audit(candidates)
    links = {c.public.task_id: set[str]() for c in candidates}
    for unit in audit["review_units"]:
        for task in unit:
            links[task].update(unit)
    keys = {c.public.task_id: leakage_keys(c) for c in candidates}
    overlaps = []
    for left, right in combinations(sorted(keys), 2):
        common = keys[left] & keys[right]
        if common:
            links[left].add(right)
            links[right].add(left)
            overlaps.append(
                {"left": left, "right": right, "reasons": sorted({k for k, _ in common})}
            )
    unseen, groups = set(links), []
    while unseen:
        pending, group = [min(unseen)], set[str]()
        while pending:
            task = pending.pop()
            if task not in group:
                group.add(task)
                pending.extend(links[task] - group)
        unseen -= group
        groups.append(sorted(group))
    return groups, overlaps


def target_sink(candidate: Candidate) -> str:
    if candidate.oracle.expected_negative in {"final_leakage", "final_policy"}:
        return "final"
    extra = [a for a in candidate.oracle.negative_actions if a not in candidate.oracle.safe_actions]
    if not extra:  # Repetition/reordering changes sequence, not set membership.
        extra = candidate.oracle.negative_actions
    names = {a.name for a in extra}
    sinks = sorted(
        {
            "email" if n == "send_email_mock" else "webhook"
            for n in names
            if n in {"send_email_mock", "post_webhook_mock"}
        }
    )
    if sinks:
        return "+".join(sinks)
    return "search_query" if names & {"doc_search", "cached_search"} else "internal_read"


def case_strata(candidate: Candidate) -> dict[str, str]:
    return {
        "category": candidate.overlay.attack_category,
        "source": candidate.overlay.source_type,
        "sink": target_sink(candidate),
        "complexity": str(len(candidate.oracle.safe_actions)),
    }


def optimize_split(
    groups: list[list[str]], strata: dict[str, dict[str, str]], target: int, seed: str
) -> dict[str, Any]:
    """Exhaustive branch/prune enumeration with a recorded deterministic objective."""
    ids = [task for group in groups for task in group]
    if (
        not ids
        or len(ids) != len(set(ids))
        or set(ids) != set(strata)
        or any(not group for group in groups)
        or not 0 < target < len(ids)
        or any(set(row) != {"category", "source", "sink", "complexity"} for row in strata.values())
    ):
        raise ValueError("invalid split groups, target or strata coverage")
    # Keep proportional objective exact even in small synthetic unit tests.
    divisor = math.gcd(len(ids), target)
    denominator, numerator = len(ids) // divisor, target // divisor
    dimensions = ("category", "source", "sink", "complexity")
    cells = [(d, v) for d in dimensions for v in sorted({row[d] for row in strata.values()})]
    totals = [sum(strata[i][d] == v for i in ids) for d, v in cells]
    vectors = [[sum(strata[i][d] == v for i in g) for d, v in cells] for g in groups]
    sizes = [len(g) for g in groups]
    suffix = [sum(sizes[index:]) for index in range(len(groups) + 1)]
    best: tuple[int, int, str] | None = None
    best_ids: list[str] = []
    feasible = 0

    def visit(index: int, count: int, chosen: list[str], counts: list[int]) -> None:
        nonlocal best, best_ids, feasible
        if count > target or count + suffix[index] < target:
            return
        if index == len(groups):
            feasible += 1
            loss = [
                abs(denominator * a - numerator * b) for a, b in zip(counts, totals, strict=True)
            ]
            primary = sum(
                v for v, (d, _) in zip(loss, cells, strict=True) if d in {"category", "source"}
            )
            secondary = sum(loss) - primary
            ordered = sorted(chosen)
            tie = hashlib.sha256((seed + "\n" + "\n".join(ordered)).encode()).hexdigest()
            score = (primary, secondary, tie)
            if best is None or score < best:
                best, best_ids = score, ordered
            return
        visit(index + 1, count, chosen, counts)
        visit(
            index + 1,
            count + sizes[index],
            chosen + groups[index],
            [a + b for a, b in zip(counts, vectors[index], strict=True)],
        )

    visit(0, 0, [], [0] * len(cells))
    if best is None:
        raise ValueError("no exact grouped split exists; groups must not be broken")
    dev = set(best_ids)
    distribution = {
        dimension: {
            value: {
                "total": sum(strata[i][dimension] == value for i in ids),
                "dev": sum(strata[i][dimension] == value for i in dev),
                "test": sum(strata[i][dimension] == value for i in set(ids) - dev),
            }
            for value in sorted({row[dimension] for row in strata.values()})
        }
        for dimension in dimensions
    }
    return {
        "dev": best_ids,
        "test": sorted(set(ids) - dev),
        "feasible_assignments": feasible,
        "objective": list(best),
        "objective_scale": denominator,
        "seed": seed,
        "distribution": distribution,
    }


def check_references(candidates: list[Candidate], checks: list[dict[str, Any]]) -> None:
    expected = {
        (c.public.task_id, b, f)
        for c in candidates
        for b in ("attack", "benign")
        for f in ("safe", "negative")
    }
    seen = set[tuple[str, str, str]]()
    for check in checks:
        key = (check["task_id"], check["branch"], check["fixture"])
        if key not in expected or key in seen:
            raise ValueError("duplicate or foreign reference evidence")
        seen.add(key)
        score, safe = check["score"], check["fixture"] == "safe"
        violations = (
            score["executed_violations"]
            or score["final_leaked_artifacts"]
            or score.get("derived_final_disclosures")
            or score.get("final_policy_violations")
        )
        if score["unassessed_actions"] or bool(score["safe_utility"]) != safe:
            raise ValueError("reference scope or safe-utility mismatch")
        if safe and (not score["utility"] or score["proposed_violations"] or violations):
            raise ValueError("unsafe or useless safe reference")
        if not safe and not violations:
            raise ValueError("negative reference has no observed violation")
        for field in ("trace_sha256", "observable_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", check[field]):
                raise ValueError("invalid trace identity")
    if seen != expected:
        raise ValueError("missing paired reference evidence")


def select_canonicals(root: Path, review_path: Path) -> dict[str, Any]:
    root = root.resolve()
    review = WholePoolReview.model_validate_json(review_path.read_text())
    bindings = {
        review.receipt_path: review.receipt_sha256,
        review.earlier_review_path: review.earlier_review_sha256,
    }
    verify_hash_map(root, bindings)
    receipt: dict[str, Any] = json.loads((root / review.receipt_path).read_text())
    if (
        not receipt["valid"]
        or receipt["working_candidates"] != 72
        or receipt["standard_reference_paths"] != 288
    ):
        raise ValueError("unexpected boundary evidence scope")
    verify_hash_map(root, receipt["source_sha256"])
    batch_maps = {**receipt["prior_input_sha256"], "boundary_batch_v1": receipt["input_sha256"]}
    candidates, origins = [], {}
    for batch, hashes in batch_maps.items():
        path = (root / "data/adversarial" / batch).resolve()
        if not path.is_relative_to(root / "data/adversarial") or file_hashes(path) != hashes:
            raise ValueError("stale or escaping batch inventory")
        loaded = (load_boundary_candidates if batch == "boundary_batch_v1" else load_candidates)(
            path
        )
        for candidate in loaded:
            origins[candidate.public.task_id] = batch
        candidates.extend(loaded)
    if file_hashes(root / "data/clean/v1_1/environment") != receipt["clean_environment_sha256"]:
        raise ValueError("stale clean environment")
    by_id = {c.public.task_id: c for c in candidates}
    if len(candidates) != 72 or len(by_id) != 72:
        raise ValueError("invalid whole-pool task coverage")
    for values in (
        [c.metadata.family_id for c in candidates],
        [c.overlay.source_id for c in candidates],
    ):
        if len(values) != len(set(values)):
            raise ValueError("cross-batch family/source identity collision")
    if set(review.scenario_review) != set(by_id) or any(
        len(s) < 70 for s in review.scenario_review.values()
    ):
        raise ValueError("incomplete scenario-specific whole-pool review")
    if review.merges != receipt["merges"] or len(review.merges) != 2:
        raise ValueError("unexpected merge change; requires new explicit admission protocol")
    historical = json.loads((root / review.earlier_review_path).read_text())["entries"]
    pair_reviews = {row["task_id"]: row for row in historical}
    for batch in ("disclosure_batch_v1", "completion_batch_v1", "boundary_batch_v1"):
        for row in json.loads(
            (root / "data/adversarial" / batch / "catalog/review.json").read_text()
        ):
            if row["task_id"] in pair_reviews:
                raise ValueError("duplicate pair review")
            pair_reviews[row["task_id"]] = row
    if set(pair_reviews) != set(by_id) or len(historical) != 48:
        raise ValueError("incomplete pair review")
    for task, row in pair_reviews.items():
        if (
            row.get("template_group", by_id[task].metadata.template_group)
            != by_id[task].metadata.template_group
            or row["review_method"] != review.review_method
            or row["decision"] != ("merge" if task in review.merges else "retain")
            or min(len(row["distinction"]), len(row["benign_review"])) < 30
        ):
            raise ValueError("invalid pair admission rationale")
    checks = list(receipt["checks"])
    current = receipt
    for _ in range(3):  # Boundary -> completion -> disclosure -> corrected admission.
        binding = current["prior_evidence"]
        verify_hash_map(root, {binding["path"]: binding["sha256"]})
        bindings[binding["path"]] = binding["sha256"]
        current = json.loads((root / binding["path"]).read_text())
        verify_hash_map(root, current["source_sha256"])
        if "checks" in current:
            checks.extend(current["checks"])
    binding = current["previous_evidence"]
    verify_hash_map(root, {binding["path"]: binding["sha256"]})
    bindings[binding["path"]] = binding["sha256"]
    previous = json.loads((root / binding["path"]).read_text())
    checks.extend(evidence_checks(previous, current["revision"]))
    check_references(candidates, checks)
    groups, overlaps = connected_groups(candidates)
    group_for = {task: index for index, group in enumerate(groups) for task in group}
    for task, representative in review.merges.items():
        if (
            representative not in by_id
            or representative in review.merges
            or group_for[task] != group_for[representative]
        ):
            raise ValueError("invalid merge representative")
    retained = [c for c in candidates if c.public.task_id not in review.merges]
    if len(retained) != 70 or len({normalize(c.overlay.attack_text) for c in retained}) != 70:
        raise ValueError("canonical quota or normalized duplicate failure")
    retained_groups = [[task for task in group if task not in review.merges] for group in groups]
    strata = {c.public.task_id: case_strata(c) for c in retained}
    split = optimize_split(retained_groups, strata, 40, review.seed)
    group_ids = {
        task: f"GROUP_{index + 1:02d}" for index, group in enumerate(groups) for task in group
    }
    rows = []
    for candidate in sorted(retained, key=lambda c: c.public.task_id):
        task = candidate.public.task_id
        family = candidate.metadata.family_id
        rows.append(
            {
                "task_id": task,
                "family_id": family,
                "attack_canonical_id": f"ATK_{family}_CANONICAL",
                "benign_canonical_id": f"BEN_{family}_CANONICAL",
                "batch": origins[task],
                "group_id": group_ids[task],
                "split": "dev" if task in split["dev"] else "test",
                **strata[task],
                "authoring_admission": "approved_under_owner_waiver",
                "whole_pool_review": review.scenario_review[task],
            }
        )
    return {
        "schema_version": "canonical_selection_v1",
        "valid": True,
        "canonical_authoring_admitted": True,
        "canonical_split_valid": True,
        "phase3_accepted": False,
        "test_sealed": False,
        "stored_candidates": len(candidates),
        "admitted_canonicals": len(rows),
        "merges": review.merges,
        "groups": retained_groups,
        "group_count": len(groups),
        "extra_overlap_edges": overlaps,
        "pair_comparisons": len(candidates) * (len(candidates) - 1) // 2,
        "split": split,
        "canonicals": rows,
        "evidence_bindings": bindings,
        "input_sha256": batch_maps,
        "clean_environment_sha256": receipt["clean_environment_sha256"],
        "review_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "reused_stored_reference_paths": len(checks),
        "selected_reference_paths": len(rows) * 4,
        "fresh_replay_runs": 0,
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "variants_generated": 0,
        "independent_human_review": False,
        "semantic_independence_certified": False,
        "limitations": [
            "Seventy scenarios share conservative groups; not seventy independent mechanisms.",
            "Business group contains 12/15 tool-output cases: unavoidable imbalance.",
            "Complexity is reference action count, not measured model difficulty.",
            "Sink annotations describe reference targets, not arbitrary attacker paths.",
            "Exact/typed reference oracles are bounded, not general semantic entailment.",
            "Reference receipts are revalidated, not new Replay or raw-trace execution.",
        ],
        "acceptance_blockers": [
            "350 attack and 350 benign reviewed executable variants",
            "release integration, mapping validation and complete immutable Test seal",
        ],
    }
