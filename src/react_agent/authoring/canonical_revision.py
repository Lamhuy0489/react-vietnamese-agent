"""Validate a wording-only unsplit pilot revision, retaining parent objectives."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from react_agent.authoring.candidate_qa import load_candidates
from react_agent.authoring.candidate_review import group_audit, verify_review
from react_agent.authoring.typed_utility import normalize
from react_agent.authoring.workbench_qa import file_hashes
from react_agent.schemas.adversarial_workbench import StrictRecord


class PairRevision(StrictRecord):
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    protected_attack_markers: list[str] = Field(min_length=1)
    review_unit: str = Field(min_length=1)
    rationale: str = Field(min_length=20)
    pair_text_checked: Literal[True]
    variant_equivalence_checked: Literal[False]


class RevisionRecord(StrictRecord):
    schema_version: Literal["canonical_revision_v1"]
    parent_dataset: Literal["candidates_v2_1"]
    revision_dataset: Literal["candidates_v2_2"]
    reviewer_kind: Literal["assistant_author_self_review"]
    independent_human_review: Literal[False]
    canonical_approval: Literal["pending"]
    split: Literal["unassigned"]
    length_ratio_min: float = Field(ge=0.8, le=0.8)
    length_ratio_max: float = Field(ge=1.25, le=1.25)
    records: list[PairRevision] = Field(min_length=1)


def validate_revision(parent: Path, revision: Path) -> dict[str, Any]:
    original, revised = load_candidates(parent), load_candidates(revision)
    by_id = {c.public.task_id: c for c in original}
    if {c.public.task_id for c in revised} != set(by_id):
        raise ValueError("revision must retain every parent identity")
    record = RevisionRecord.model_validate_json((revision / "reviews/revision.json").read_text())
    notes = {r.task_id: r for r in record.records}
    if len(notes) != len(record.records) or set(notes) != set(by_id):
        raise ValueError("missing or duplicate revision review records")
    for name in ("public/tasks.json", "private/oracles.json"):
        if (parent / name).read_bytes() != (revision / name).read_bytes():
            raise ValueError("public task/private oracle bytes changed")
    checks = []
    for candidate in revised:
        task = candidate.public.task_id
        old, new, note = by_id[task], candidate, notes[task]
        if old.overlay.model_dump(exclude={"attack_text", "benign_text"}) != new.overlay.model_dump(
            exclude={"attack_text", "benign_text"}
        ):
            raise ValueError("revision changed protected overlay fields")
        if old.metadata.model_dump(exclude={"semantic_group", "template_group"}) != (
            new.metadata.model_dump(exclude={"semantic_group", "template_group"})
        ):
            raise ValueError("revision changed protected catalog fields")
        if note.review_unit != new.metadata.template_group or new.metadata.semantic_group != (
            "REVIEW_" + note.review_unit.upper()
        ):
            raise ValueError("review unit disagrees with catalog")
        if old.overlay.attack_text == new.overlay.attack_text or (
            old.overlay.benign_text == new.overlay.benign_text
        ):
            raise ValueError("both pair branches require a wording revision")
        attack, benign = normalize(new.overlay.attack_text), normalize(new.overlay.benign_text)
        if re.search(r"\bgiả\b|tự nhận|tự gán|dù người dùng", attack):
            raise ValueError("explicit attack self-labelling cue remains")
        if any(
            cue in benign
            for cue in (
                "không yêu cầu",
                "không cần",
                "không gửi",
                "không đọc",
                "không công bố",
                "không phải yêu cầu",
                "tuân thủ người dùng",
                "bỏ qua chỉ dẫn",
            )
        ):
            raise ValueError("benign contains explicit safety-instruction cue")
        if any(
            not marker.strip() or marker not in new.overlay.attack_text
            for marker in note.protected_attack_markers
        ):
            raise ValueError("protected attack marker missing")
        # Destination/action markers are also derived from the preserved negative script.
        extra_actions = [a for a in new.oracle.negative_actions if a not in new.oracle.safe_actions]
        for action in extra_actions:
            field = {"send_email_mock": "to", "post_webhook_mock": "endpoint"}.get(action.name)
            if field is not None and (
                action.name not in new.overlay.attack_text
                or str(action.arguments[field]) not in new.overlay.attack_text
            ):
                raise ValueError("negative sink/action target absent from revised attack")
        if any(
            normalize(a.value) in text
            for a in new.oracle.sensitive_artifacts
            for text in (attack, benign)
        ):
            raise ValueError("sensitive value directly embedded in pair text")
        words = len(new.overlay.attack_text.split()), len(new.overlay.benign_text.split())
        ratio = words[1] / max(1, words[0])
        if not record.length_ratio_min <= ratio <= record.length_ratio_max:
            raise ValueError("pair length ratio outside declared revision gate")
        checks.append(
            {
                "task_id": task,
                "parent_fields_preserved": True,
                "attack_words": words[0],
                "benign_words": words[1],
                "benign_attack_ratio": round(ratio, 4),
                "review_unit": note.review_unit,
                "lexical_guards_pass": True,
                "assistant_pair_text_checked": note.pair_text_checked,
            }
        )
    old_groups, new_groups = group_audit(original), group_audit(revised)
    if any(
        not any(set(old) <= set(new) for new in new_groups["review_units"])
        for old in old_groups["review_units"]
    ):
        raise ValueError("revision split a parent review unit")
    return {
        "valid": True,
        "candidate_count": len(revised),
        "parent_review_units": old_groups["review_unit_count"],
        "revision_review_units": new_groups["review_unit_count"],
        "checks": checks,
        "reviewer_kind": record.reviewer_kind,
        "canonical_approval": record.canonical_approval,
        "semantic_independence_certified": False,
    }


def verify_revision(
    parent: Path,
    revision: Path,
    sidecars: Path,
    clean: Path,
    output: Path,
) -> dict[str, Any]:
    if output.resolve().is_relative_to(parent.resolve()) or parent.resolve().is_relative_to(
        output.resolve()
    ):
        raise ValueError("output must be separate from parent inputs")
    before = file_hashes(parent)
    changes = validate_revision(parent, revision)
    report = verify_review(revision, sidecars, clean, output)
    if file_hashes(parent) != before:
        raise ValueError("parent bytes changed during QA")
    return {
        **report,
        "scope": "wording/grouping revision QA; not Phase 3 acceptance",
        "parent_input_sha256": before,
        "revision_checks": changes,
    }
