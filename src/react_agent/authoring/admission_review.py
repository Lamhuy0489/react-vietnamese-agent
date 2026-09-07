"""Hash-bound author review register; not a human-review or release certificate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import Field, model_validator

from react_agent.authoring.candidate_qa import Candidate, load_candidates
from react_agent.authoring.candidate_review import group_audit
from react_agent.authoring.workbench_qa import file_hashes
from react_agent.schemas.adversarial_workbench import StrictRecord

Batch = Literal[
    "candidates_v2_2",
    "mechanism_batch_v2",
    "linked_scope_v1",
    "transaction_batch_v1",
    "flow_batch_v1",
]


class ReviewEntry(StrictRecord):
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    family_id: str = Field(pattern=r"^CAND_[A-Z]+$")
    batch: Batch
    template_group: str = Field(min_length=1)
    decision: Literal["retain", "merge"]
    representative: str = Field(pattern=r"^awb_[a-z]+$")
    distinction: str = Field(min_length=30)
    benign_review: str = Field(min_length=30)
    review_method: Literal["assistant_self_review_owner_waiver"] = (
        "assistant_self_review_owner_waiver"
    )

    @model_validator(mode="after")
    def check_representative(self) -> Self:
        if (self.representative == self.task_id) != (self.decision == "retain"):
            raise ValueError("retain must represent itself; merge must target another candidate")
        return self


class AdmissionRegister(StrictRecord):
    schema_version: Literal["canonical_admission_review_v1"]
    scope: Literal["bounded_candidate_selection_not_release"]
    previous_receipt: Literal["experiments/manifests/phase3_pool_v3_validation01.json"]
    previous_receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    input_sha256: dict[Batch, dict[str, str]]
    entries: list[ReviewEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_snapshot(self) -> Self:
        if (
            set(self.input_sha256)
            != {
                "candidates_v2_2",
                "mechanism_batch_v2",
                "linked_scope_v1",
                "transaction_batch_v1",
                "flow_batch_v1",
            }
            or len(self.entries) != 48
        ):
            raise ValueError("review v1 requires all five batches and 48 entries")
        return self


def verify_hash_map(root: Path, hashes: dict[str, str]) -> None:
    root = root.resolve()
    if not hashes:
        raise ValueError("empty evidence hash map")
    for relative, expected in hashes.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("invalid or missing evidence path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("stale evidence/input hash")


def load_bound_previous(root: Path, register: AdmissionRegister) -> dict[str, Any]:
    verify_hash_map(root, {register.previous_receipt: register.previous_receipt_sha256})
    report: dict[str, Any] = json.loads((root / register.previous_receipt).read_text())
    verify_hash_map(root, report["source_sha256"])
    pool1 = report["prior_pool"]["prior_pool"]
    for relative, hashes in pool1["input_sets_sha256"].items():
        if not (root / relative).resolve().is_relative_to(root.resolve()):
            raise ValueError("input root outside repository")
        verify_hash_map(root / relative, hashes)
    verify_hash_map(
        root / "data/adversarial/transaction_batch_v1",
        report["prior_pool"]["transaction_batch"]["input_sha256"],
    )
    verify_hash_map(root / "data/adversarial/flow_batch_v1", report["flow_batch"]["input_sha256"])
    if not report["qa_valid"] or report["candidate_count"] != 48 or report["replay_runs"] != 192:
        raise ValueError("unexpected prior evidence scope")
    return report


def evidence_checks(previous: dict[str, Any], revision: dict[str, Any]) -> list[dict[str, Any]]:
    pool1 = previous["prior_pool"]["prior_pool"]
    batches = [
        pool1["batches"]["pilot"],
        pool1["batches"]["linked"],
        previous["prior_pool"]["transaction_batch"],
        previous["flow_batch"],
        revision["standard"],
    ]
    return [check for batch in batches for check in batch["checks"]]


def validate_admission(
    root: Path, register: AdmissionRegister, checks: list[dict[str, Any]]
) -> dict[str, Any]:
    candidates: dict[str, Candidate] = {}
    batch_for: dict[str, str] = {}
    for batch, hashes in register.input_sha256.items():
        source = root / "data/adversarial" / batch
        if hashes != file_hashes(source):
            raise ValueError("register input inventory/hash mismatch")
        for candidate in load_candidates(source):
            identity = candidate.public.task_id
            if identity in candidates:
                raise ValueError("duplicate cross-batch task identity")
            candidates[identity], batch_for[identity] = candidate, batch
    entries = {e.task_id: e for e in register.entries}
    if len(entries) != len(register.entries) or set(entries) != set(candidates):
        raise ValueError("review must cover every candidate exactly once")
    audit = group_audit(list(candidates.values()))
    units = {task: index for index, unit in enumerate(audit["review_units"]) for task in unit}
    for identity, entry in entries.items():
        candidate = candidates[identity]
        if (
            entry.family_id != candidate.metadata.family_id
            or entry.batch != batch_for[identity]
            or entry.template_group != candidate.metadata.template_group
        ):
            raise ValueError("review identity/group differs from source")
        target = entries.get(entry.representative)
        if (
            target is None
            or target.decision != "retain"
            or units[target.task_id] != units[identity]
        ):
            raise ValueError("merge target must be retained in the same conservative group")
    combinations = {
        (branch, fixture) for branch in ("attack", "benign") for fixture in ("safe", "negative")
    }
    seen: dict[str, set[tuple[str, str]]] = {identity: set() for identity in candidates}
    for check in checks:
        identity = check["task_id"]
        pair = (check["branch"], check["fixture"])
        if identity not in seen or pair not in combinations or pair in seen[identity]:
            raise ValueError("unexpected/duplicate fixture evidence identity")
        seen[identity].add(pair)
        score = check["score"]
        safe = pair[1] == "safe"
        if score["unassessed_actions"] or bool(score["safe_utility"]) != safe:
            raise ValueError("reference evidence outcome mismatch")
        if safe and (
            not score["utility"]
            or score["proposed_violations"]
            or score["executed_violations"]
            or score["final_leaked_artifacts"]
        ):
            raise ValueError("safe evidence lacks utility or has violations")
        if not safe and not (score["executed_violations"] or score["final_leaked_artifacts"]):
            raise ValueError("negative evidence lacks an observed security outcome")
        for key in ("trace_sha256", "observable_sha256"):
            value = check[key]
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(c not in "0123456789abcdef" for c in value)
            ):
                raise ValueError("invalid evidence trace hash")
    if any(pairs != combinations for pairs in seen.values()):
        raise ValueError("missing paired reference evidence")
    retained = sorted(e.task_id for e in entries.values() if e.decision == "retain")
    return {
        "valid": True,
        "phase3_accepted": False,
        "split_ready": False,
        "scope": "bounded candidate-selection review under owner waiver",
        "working_candidates": len(candidates),
        "retained_representatives": len(retained),
        "retained_task_ids": retained,
        "merges": {e.task_id: e.representative for e in entries.values() if e.decision == "merge"},
        "remaining_to_target": 70 - len(retained),
        "standard_reference_paths": len(checks),
        "independent_human_review": False,
        "semantic_independence_certified": False,
        "review_unit_count": audit["review_unit_count"],
        "pairs_examined": audit["pairs_examined"],
        "review_units": audit["review_units"],
    }
