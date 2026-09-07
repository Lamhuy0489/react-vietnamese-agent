"""Authored clause paraphrases and reviewed, protected-span Vietnamese code mixing."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from react_agent.authoring.boundary_rules import BoundaryRule
from react_agent.authoring.mechanical_variants import digest, protected_payload_literals
from react_agent.authoring.selected_runtime import (
    SELECTION_SHA256,
    Branch,
    SelectedCase,
    load_selected,
    run_reference,
)
from react_agent.authoring.surfaces import INVISIBLE, TOOL_NAMES
from react_agent.authoring.workbench_qa import file_hashes
from react_agent.schemas.adversarial_workbench import StrictRecord


class LinguisticVariant(StrictRecord):
    schema_version: Literal["linguistic_variant_v1"] = "linguistic_variant_v1"
    variant_id: str
    pair_id: str
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    family_id: str = Field(pattern=r"^CAND_[A-Z]+$")
    canonical_id: str
    group_id: str
    split: Literal["dev", "test"]
    branch: Branch
    variant_type: Literal["code_mix", "paraphrase"]
    raw_payload: str = Field(min_length=1)
    visible_debug: str = Field(min_length=1)
    canonical_payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    protected_literals: list[str]
    selection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    edits: list[dict[str, Any]] = Field(min_length=1)
    source_syllable_fraction_edited: float
    review_status: Literal["pending"] = "pending"


def literal_pattern(literal: str) -> str:
    return (
        (r"(?<!\w)" if re.match(r"\w", literal[0]) else "")
        + re.escape(literal)
        + (r"(?!\w)" if re.match(r"\w", literal[-1]) else "")
    )


def protected_spans(text: str, literals: tuple[str, ...]) -> list[tuple[int, int]]:
    return [
        (m.start(), m.end())
        for literal in literals
        for m in re.finditer(literal_pattern(literal), text)
    ]


def code_mix(
    text: str, glossary: dict[str, str], literals: tuple[str, ...]
) -> tuple[str, list[dict[str, Any]]]:
    pattern = re.compile(
        r"(?<!\w)(?:"
        + "|".join(re.escape(s) for s in sorted(glossary, key=lambda s: (-len(s), s)))
        + r")(?!\w)",
        re.I,
    )
    protected = protected_spans(text, literals)
    edits: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        if any(match.start() < end and match.end() > start for start, end in protected):
            continue
        replacement = glossary[match.group().lower()]
        if match.group()[0].isupper():
            replacement = replacement[0].upper() + replacement[1:]
        edits.append({"start": match.start(), "before": match.group(), "after": replacement})
        if len(edits) == 8:
            break
    heading = re.match(r"^[^.:]{1,60}:\s", text)
    heading_end = heading.end() if heading else 0
    if len(edits) < 2 or not any(e["start"] >= heading_end for e in edits):
        raise ValueError("code-mix requires substantive edits, not a changed heading only")
    raw, offset = "", 0
    for edit in edits:
        raw += text[offset : edit["start"]] + edit["after"]
        offset = edit["start"] + len(edit["before"])
    raw += text[offset:]
    if not re.search(r"[àáạảãăâđèéẹẻẽêìíịỉĩòóọỏõôơùúụủũưỳýỵỷỹ]", raw, re.I):
        raise ValueError("code-mix must retain Vietnamese text")
    return raw, edits


def check_literals(canonical: str, raw: str, literals: tuple[str, ...]) -> None:
    for literal in literals:
        pattern = literal_pattern(literal)
        if len(re.findall(pattern, raw)) < len(re.findall(pattern, canonical)):
            raise ValueError(f"required literal lost: {literal}")
    # New English words may equal a field name; actual endpoints/IDs must match exactly.
    pattern = r"[\w.+-]+@[\w.-]+|mock://[^\s,;]+|\b(?:AWB|AUX|CDOC)_[A-Z0-9]+\b"

    def inventory(text: str) -> Counter[str]:
        return Counter(t.rstrip(".,;:") for t in re.findall(pattern, text))

    if inventory(canonical) != inventory(raw):
        raise ValueError("source/recipient inventory changed")


def draft_linguistic(cases: dict[str, SelectedCase], inputs: Path) -> list[LinguisticVariant]:
    clauses = json.loads((inputs / "paraphrase_edits.json").read_text())
    glossary = json.loads((inputs / "code_mix_glossary.json").read_text())
    if (
        set(clauses) != set(cases)
        or not glossary
        or any(
            not isinstance(k, str) or not isinstance(v, str) or not k.strip() or not v.strip()
            for k, v in glossary.items()
        )
    ):
        raise ValueError("incomplete authoring inputs")
    rows = []
    for task, case in sorted(cases.items()):
        if set(clauses[task]) != {"attack", "benign"}:
            raise ValueError("both paired paraphrases required")
        for branch in ("attack", "benign"):
            text = getattr(case.candidate.overlay, f"{branch}_text")
            literals = tuple(
                sorted(
                    set(protected_payload_literals(case, text) + TOOL_NAMES),
                    key=lambda s: (-len(s), s),
                )
            )
            old, new = clauses[task][branch]
            if text.count(old) != 1 or old == new or min(len(old.split()), len(new.split())) < 4:
                raise ValueError("paraphrase requires one exact substantive clause")
            outputs: dict[Literal["code_mix", "paraphrase"], tuple[str, list[dict[str, Any]]]] = {
                "code_mix": code_mix(text, glossary, literals),
                "paraphrase": (
                    text.replace(old, new, 1),
                    [{"start": text.index(old), "before": old, "after": new}],
                ),
            }
            for kind, (raw, edits) in outputs.items():
                if raw == text or any(c in raw for c in INVISIBLE):
                    raise ValueError("linguistic no-op or unexpected invisible character")
                check_literals(text, raw, literals)
                family = case.selection["family_id"]
                pair = family + "_" + kind.upper()
                rows.append(
                    LinguisticVariant(
                        variant_id=("ATK_" if branch == "attack" else "BEN_") + pair,
                        pair_id=pair,
                        task_id=task,
                        family_id=family,
                        canonical_id=case.selection[f"{branch}_canonical_id"],
                        group_id=case.selection["group_id"],
                        split=case.selection["split"],
                        branch=branch,
                        variant_type=kind,
                        raw_payload=raw,
                        visible_debug=raw,
                        canonical_payload_sha256=digest(text),
                        protected_literals=[s for s in literals if s in text],
                        selection_sha256=SELECTION_SHA256,
                        edits=edits,
                        source_syllable_fraction_edited=round(
                            sum(len(e["before"].split()) for e in edits) / len(text.split()), 4
                        ),
                    )
                )
    return rows


def build_linguistic(root: Path, inputs: Path, destination: Path) -> dict[str, Any]:
    root, inputs, destination = root.resolve(), inputs.resolve(), destination.resolve()
    if (
        not inputs.is_relative_to(root / "data/adversarial")
        or destination.exists()
        or not destination.is_relative_to(root / "data/adversarial")
        or destination.is_relative_to(inputs)
    ):
        raise ValueError("linguistic output must be fresh and separate under adversarial data")
    _, cases = load_selected(root)
    rows = draft_linguistic(cases, inputs)
    if len(rows) != 280:
        raise ValueError("two linguistic variants per paired canonical required")
    destination.mkdir(parents=True)
    with (destination / "variants.jsonl").open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(row.model_dump_json() + "\n")
    inventory = {
        "schema_version": "linguistic_draft_inventory_v1",
        "selection_sha256": SELECTION_SHA256,
        "authoring_root": inputs.relative_to(root).as_posix(),
        "authoring_sha256": file_hashes(inputs),
        "variants_sha256": hashlib.sha256(
            (destination / "variants.jsonl").read_bytes()
        ).hexdigest(),
        "variants": 280,
        "attack": 140,
        "benign": 140,
        "review_status": "pending",
        "phase3_accepted": False,
        "test_sealed": False,
    }
    with (destination / "inventory.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")
    return inventory


def validate_linguistic(
    root: Path, inputs: Path, cases: dict[str, SelectedCase]
) -> list[LinguisticVariant]:
    inventory = json.loads((inputs / "inventory.json").read_text())
    authoring = (root / inventory["authoring_root"]).resolve()
    if (
        not authoring.is_relative_to(root / "data/adversarial")
        or file_hashes(authoring) != inventory["authoring_sha256"]
    ):
        raise ValueError("stale/escaping linguistic authoring inventory")
    hashes = file_hashes(inputs)
    expected_inventory = {
        "schema_version": "linguistic_draft_inventory_v1",
        "selection_sha256": SELECTION_SHA256,
        "authoring_root": authoring.relative_to(root).as_posix(),
        "authoring_sha256": file_hashes(authoring),
        "variants_sha256": hashes["variants.jsonl"],
        "variants": 280,
        "attack": 140,
        "benign": 140,
        "review_status": "pending",
        "phase3_accepted": False,
        "test_sealed": False,
    }
    if json.dumps(inventory, sort_keys=True) != json.dumps(expected_inventory, sort_keys=True):
        raise ValueError("invalid linguistic draft inventory")
    rows = [
        LinguisticVariant.model_validate_json(s)
        for s in (inputs / "variants.jsonl").read_text().splitlines()
    ]
    expected = {r.variant_id: r for r in draft_linguistic(cases, authoring)}
    index = {r.variant_id: r for r in rows}
    if len(rows) != 280 or len(index) != 280 or index != expected:
        raise ValueError("linguistic identity, mapping or payload drift")
    reviews = json.loads((inputs / "review.json").read_text())
    if (
        set(reviews) != {"schema_version", "method", "selection_sha256", "review_basis", "entries"}
        or not isinstance(reviews.get("review_basis"), str)
        or len(reviews["review_basis"]) < 80
        or reviews.get("schema_version") != "linguistic_review_v1"
        or reviews.get("method") != "assistant_self_review_owner_waiver"
        or reviews.get("selection_sha256") != SELECTION_SHA256
    ):
        raise ValueError("missing bounded semantic review")
    entries = reviews["entries"]
    reviewed = {r["variant_id"]: r for r in entries}
    if len(entries) != 280 or set(reviewed) != set(index):
        raise ValueError("all linguistic variants require individual review")
    for identity, row in index.items():
        review = reviewed[identity]
        if (
            set(review)
            != {"variant_id", "decision", "variant_sha256", "canonical_sha256", "semantic_review"}
            or review["decision"] != "approve"
            or review["variant_sha256"] != digest(row.raw_payload)
            or review["canonical_sha256"] != row.canonical_payload_sha256
            or len(review["semantic_review"]) < 50
        ):
            raise ValueError("stale or unapproved semantic review")
    for branch in ("attack", "benign"):
        for kind in ("code_mix", "paraphrase"):
            if (
                len({r.raw_payload for r in rows if r.branch == branch and r.variant_type == kind})
                != 70
            ):
                raise ValueError("duplicate linguistic family payload")
    return rows


def verify_linguistic(root: Path, inputs: Path, output: Path) -> dict[str, Any]:
    root, inputs, output = root.resolve(), inputs.resolve(), output.resolve()
    if (
        not inputs.is_relative_to(root / "data/adversarial")
        or output.exists()
        or not output.is_relative_to(root / "results")
    ):
        raise ValueError("linguistic inputs/output must be scoped, fresh and separate")
    before = file_hashes(inputs)
    _, cases = load_selected(root)
    rows = validate_linguistic(root, inputs, cases)
    output.mkdir(parents=True)
    checks = []
    for row in rows:
        case = cases[row.task_id]
        fixtures: list[Literal["safe", "negative", "alternative"]] = ["safe", "negative"]
        if isinstance(case.rule, BoundaryRule) and case.rule.mode == "shared_quota":
            fixtures.append("alternative")
        for fixture in fixtures:
            destination = output / row.variant_id / fixture
            check = run_reference(root, case, row.raw_payload, row.branch, fixture, destination)
            check.update(
                {
                    "variant_id": row.variant_id,
                    "invocation_id": row.variant_id + "/" + fixture,
                    "split": row.split,
                    "variant_type": row.variant_type,
                    "trace_path": (destination / "trace.jsonl").relative_to(output).as_posix(),
                }
            )
            checks.append(check)
    if len({c["run_id"] for c in checks}) != len(checks) or len(checks) != 564:
        raise ValueError("linguistic reference identity/count mismatch")
    if file_hashes(inputs) != before:
        raise ValueError("linguistic inputs changed during reference execution")
    load_selected(root)
    validate_linguistic(root, inputs, cases)
    stable = [{k: v for k, v in c.items() if k not in {"run_id", "trace_sha256"}} for c in checks]
    return {
        "valid": True,
        "linguistic_variants_accepted": True,
        "phase3_accepted": False,
        "test_sealed": False,
        "variant_count": len(rows),
        "attack_variants": 140,
        "benign_variants": 140,
        "semantic_variants_reviewed": 280,
        "independent_human_review": False,
        "fresh_replay_runs": len(checks),
        "variant_standard_paths": 560,
        "alternative_paths": 4,
        "test_assigned_reference_runs": sum(c["split"] == "test" for c in checks),
        "real_model_runs": 0,
        "held_out_model_runs": 0,
        "selection_sha256": SELECTION_SHA256,
        "input_sha256": before,
        "raw_output": str(output),
        "checks": checks,
        "stable_summary_sha256": digest(json.dumps(stable, ensure_ascii=False, sort_keys=True)),
        "acceptance_blockers": ["complete 700-variant release integration and immutable Test seal"],
    }
