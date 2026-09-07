"""Deterministic selected-family mechanical variants with separate review and QA."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from react_agent.authoring.boundary_rules import BoundaryRule
from react_agent.authoring.canonical_selection import strings
from react_agent.authoring.selected_runtime import (
    SELECTION_PATH,
    SELECTION_SHA256,
    Branch,
    SelectedCase,
    load_selected,
    run_reference,
)
from react_agent.authoring.surfaces import SurfaceKind, draft_surface
from react_agent.authoring.workbench_qa import file_hashes
from react_agent.schemas.adversarial_workbench import StrictRecord

KINDS: tuple[SurfaceKind, ...] = ("no_diacritic", "word_boundary", "zero_width")


class MechanicalVariant(StrictRecord):
    schema_version: Literal["mechanical_variant_v1"] = "mechanical_variant_v1"
    variant_id: str
    pair_id: str
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    family_id: str = Field(pattern=r"^CAND_[A-Z]+$")
    canonical_id: str
    group_id: str
    split: Literal["dev", "test"]
    branch: Branch
    variant_type: SurfaceKind
    raw_payload: str = Field(min_length=1)
    visible_debug: str = Field(min_length=1)
    canonical_payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    protected_literals: list[str]
    selection_sha256: Literal[SELECTION_SHA256]  # type: ignore[valid-type]
    review_status: Literal["pending"] = "pending"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def validate_literal_spans(canonical: str, row: MechanicalVariant) -> None:
    # Vietnamese NFC stripping and one space replacement preserve character offsets.
    # Counting substrings is wrong: e.g. stripping 'tổ' creates another 'to'.
    if unicodedata.normalize("NFC", canonical) != canonical:
        raise ValueError("canonical surface must be NFC for positional literal audit")
    insertion = row.raw_payload.index("\u200b") if row.variant_type == "zero_width" else None
    if len(row.raw_payload) != len(canonical) + int(insertion is not None):
        raise ValueError("unexpected mechanical character-length change")
    for literal in row.protected_literals:
        for match in re.finditer(r"(?=" + re.escape(literal) + r")", canonical):
            offset = match.start() + int(insertion is not None and match.start() >= insertion)
            if row.raw_payload[offset : offset + len(literal)] != literal:
                raise ValueError("protected literal span changed")


def protected_payload_literals(case: SelectedCase, text: str) -> tuple[str, ...]:
    """Protect only literals already present; never insert private oracle values."""
    oracle = case.candidate.oracle
    values = {
        s
        for action in [*oracle.safe_actions, *oracle.negative_actions]
        for s in strings(action.arguments)
    }
    values.update(oracle.safe_final.splitlines())
    values.update(oracle.negative_final.splitlines())
    # NOTICE is formatting, not the Vietnamese lexical target of U+200B insertion.
    values.add("NOTICE")
    values.update(re.findall(r"\b[A-Za-z][A-Za-z0-9]*(?:[_-][A-Za-z0-9]+)+\b", text))
    values.update(re.findall(r"(?<!\w)-?\d+(?:[.:/-]\d+)*(?!\w)", text))
    if isinstance(case.rule, BoundaryRule):
        values.update(case.rule.forbidden_lines)
    return tuple(sorted((s for s in values if s.strip() and s in text), key=lambda s: (-len(s), s)))


def draft_variants(cases: dict[str, SelectedCase]) -> list[MechanicalVariant]:
    rows = []
    for task, case in sorted(cases.items()):
        for kind in KINDS:
            for branch in ("attack", "benign"):
                text = getattr(case.candidate.overlay, f"{branch}_text")
                protected = protected_payload_literals(case, text)
                draft = draft_surface(text, kind, protected_literals=protected)
                family = case.selection["family_id"]
                pair = family + "_" + kind.upper()
                rows.append(
                    MechanicalVariant(
                        variant_id=("ATK_" if branch == "attack" else "BEN_") + pair,
                        pair_id=pair,
                        task_id=task,
                        family_id=family,
                        canonical_id=case.selection[f"{branch}_canonical_id"],
                        group_id=case.selection["group_id"],
                        split=case.selection["split"],
                        branch=branch,
                        variant_type=kind,
                        raw_payload=draft.raw,
                        visible_debug=draft.visible_debug,
                        canonical_payload_sha256=digest(text),
                        protected_literals=list(protected),
                        selection_sha256=SELECTION_SHA256,
                    )
                )
    return rows


def draft_inventory(payload_hash: str) -> dict[str, Any]:
    return {
        "schema_version": "mechanical_draft_inventory_v1",
        "selection_path": SELECTION_PATH,
        "selection_sha256": SELECTION_SHA256,
        "variants": 420,
        "attack": 210,
        "benign": 210,
        "types": list(KINDS),
        "missing_types": ["code_mix", "paraphrase"],
        "variants_sha256": payload_hash,
        "review_status": "pending",
        "phase3_accepted": False,
        "test_sealed": False,
    }


def validate_inventory(inventory: dict[str, Any], payload_hash: str) -> None:
    if json.dumps(inventory, sort_keys=True) != json.dumps(
        draft_inventory(payload_hash), sort_keys=True
    ):
        raise ValueError("stale/mislabelled draft inventory")


def build_drafts(root: Path, destination: Path) -> dict[str, Any]:
    root, destination = root.resolve(), destination.resolve()
    if destination.exists() or not destination.is_relative_to(root / "data/adversarial"):
        raise ValueError("draft destination must be fresh under data/adversarial")
    _, cases = load_selected(root)
    rows = draft_variants(cases)
    if len(rows) != 420:
        raise ValueError("three variants per seventy paired canonicals required")
    destination.mkdir(parents=True)
    with (destination / "variants.jsonl").open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(row.model_dump_json() + "\n")
    inventory = draft_inventory(
        hashlib.sha256((destination / "variants.jsonl").read_bytes()).hexdigest()
    )
    with (destination / "inventory.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
    return inventory


def validate_variants(
    rows: list[MechanicalVariant],
    cases: dict[str, SelectedCase],
    review: dict[str, Any],
) -> dict[str, Any]:
    expected = {row.variant_id: row for row in draft_variants(cases)}
    by_id = {row.variant_id: row for row in rows}
    if len(rows) != 420 or len(by_id) != len(rows) or set(by_id) != set(expected):
        raise ValueError("missing/duplicate/foreign variant identity")
    for identity, row in by_id.items():
        if row != expected[identity]:
            raise ValueError(
                "variant drift in payload, protected literals, debug or canonical mapping"
            )
        validate_literal_spans(
            getattr(cases[row.task_id].candidate.overlay, f"{row.branch}_text"),
            row,
        )
    for branch in ("attack", "benign"):
        for kind in KINDS:
            texts = [r.raw_payload for r in rows if r.branch == branch and r.variant_type == kind]
            if len(texts) != len(set(texts)):
                raise ValueError("duplicate cross-family variant payload")
    boundaries = {r.variant_id: r for r in rows if r.variant_type == "word_boundary"}
    if (
        set(review)
        != {
            "schema_version",
            "method",
            "selection_sha256",
            "structural_types",
            "review_basis",
            "word_boundary_entries",
        }
        or len(review.get("review_basis", "")) < 80
    ):
        raise ValueError("unexpected or incomplete review metadata")
    if (
        review.get("schema_version") != "mechanical_review_v1"
        or review.get("method") != "assistant_self_review_owner_waiver"
    ):
        raise ValueError("missing explicit mechanical review method")
    if review.get("selection_sha256") != SELECTION_SHA256 or review.get("structural_types") != [
        "no_diacritic",
        "zero_width",
    ]:
        raise ValueError("review scope/binding mismatch")
    entries = review.get("word_boundary_entries", [])
    index = {entry["variant_id"]: entry for entry in entries}
    if len(index) != len(entries) or set(index) != set(boundaries):
        raise ValueError("word-boundary review must cover all 140 payloads")
    for identity, row in boundaries.items():
        entry = index[identity]
        if set(entry) != {
            "variant_id",
            "canonical_sha256",
            "variant_sha256",
            "decision",
            "context_review",
        }:
            raise ValueError("unexpected word-boundary review fields")
        canonical = getattr(cases[row.task_id].candidate.overlay, f"{row.branch}_text")
        if (
            entry.get("decision") != "approve"
            or entry.get("canonical_sha256") != digest(canonical)
            or entry.get("variant_sha256") != digest(row.raw_payload)
            or len(entry.get("context_review", "")) < 25
        ):
            raise ValueError("stale/incomplete word-boundary review")
        # First difference is exactly one space -> underscore, not identifier surgery.
        diffs = [
            i for i, (a, b) in enumerate(zip(canonical, row.raw_payload, strict=True)) if a != b
        ]
        if len(diffs) != 1 or canonical[diffs[0]] != " " or row.raw_payload[diffs[0]] != "_":
            raise ValueError("word-boundary edit is not the declared substitution")
    return {
        "variant_count": len(rows),
        "attack_variants": 210,
        "benign_variants": 210,
        "counts": dict(
            sorted(Counter(f"{r.split}/{r.branch}/{r.variant_type}" for r in rows).items())
        ),
        "word_boundary_reviewed": len(index),
        "structural_variants_checked": 280,
    }


def verify_mechanical(root: Path, inputs: Path, output: Path) -> dict[str, Any]:
    root, inputs, output = root.resolve(), inputs.resolve(), output.resolve()
    if (
        not inputs.is_relative_to(root / "data/adversarial")
        or output.exists()
        or not output.is_relative_to(root / "results")
    ):
        raise ValueError("inputs must be adversarial data and output fresh under results")
    before = file_hashes(inputs)
    selection, cases = load_selected(root)
    inventory = json.loads((inputs / "inventory.json").read_text())
    validate_inventory(inventory, before["variants.jsonl"])
    rows = [
        MechanicalVariant.model_validate_json(line)
        for line in (inputs / "variants.jsonl").read_text().splitlines()
    ]
    review = json.loads((inputs / "review.json").read_text())
    structure = validate_variants(rows, cases, review)
    output.mkdir(parents=True)
    checks: list[dict[str, Any]] = []

    def execute(
        case: SelectedCase, payload: str, branch: Branch, identity: str, canonical: bool
    ) -> None:
        fixtures: list[Literal["safe", "negative", "alternative"]] = ["safe", "negative"]
        if isinstance(case.rule, BoundaryRule) and case.rule.mode == "shared_quota":
            fixtures.append("alternative")
        for fixture in fixtures:
            directory = output / identity / fixture
            check = run_reference(root, case, payload, branch, fixture, directory)
            check.update(
                {
                    "invocation_id": identity + "/" + fixture,
                    "variant_id": identity,
                    "canonical_baseline": canonical,
                    "split": case.selection["split"],
                    "trace_path": (directory / "trace.jsonl").relative_to(output).as_posix(),
                }
            )
            checks.append(check)

    for case in cases.values():
        for branch in ("attack", "benign"):
            execute(
                case,
                getattr(case.candidate.overlay, f"{branch}_text"),
                branch,
                case.selection[f"{branch}_canonical_id"],
                True,
            )
    for row in rows:
        execute(cases[row.task_id], row.raw_payload, row.branch, row.variant_id, False)
    if len({check["invocation_id"] for check in checks}) != len(checks) or len(
        {check["run_id"] for check in checks}
    ) != len(checks):
        raise ValueError("duplicate invocation/run identity")
    if file_hashes(inputs) != before:
        raise ValueError("variant inputs changed during execution")
    # Re-audit frozen inputs and sidecars after execution, without assigning a new split.
    load_selected(root)
    normalized_checks = [
        {k: v for k, v in check.items() if k not in {"trace_sha256", "run_id"}} for check in checks
    ]
    return {
        "valid": True,
        "mechanical_variants_accepted": True,
        "phase3_accepted": False,
        "test_sealed": False,
        **structure,
        "fresh_replay_runs": len(checks),
        "canonical_standard_paths": sum(
            c["canonical_baseline"] and c["fixture"] != "alternative" for c in checks
        ),
        "variant_standard_paths": sum(
            not c["canonical_baseline"] and c["fixture"] != "alternative" for c in checks
        ),
        "alternative_paths": sum(c["fixture"] == "alternative" for c in checks),
        "test_assigned_reference_runs": sum(c["split"] == "test" for c in checks),
        "reused_replay_runs": 0,
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "selection_path": SELECTION_PATH,
        "selection_sha256": SELECTION_SHA256,
        "selection_source": selection["base_git_commit"],
        "input_sha256": before,
        "checks": checks,
        "raw_output": str(output),
        "stable_summary_sha256": digest(
            json.dumps(normalized_checks, ensure_ascii=False, sort_keys=True)
        ),
        "independent_human_review": False,
        "acceptance_blockers": [
            "140 reviewed code-mix variants and 140 reviewed paraphrase variants",
            "executable QA for the complete 700-variant set",
            "complete release integration and immutable Test seal",
        ],
    }
