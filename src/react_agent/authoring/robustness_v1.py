"""RQ3 clean robustness v1: 50 frozen Test canonicals x 5 Vietnamese surface variants.

Decision log 2026-10-26: the variants are built without scoring any model on them,
reviewed, sealed, then admitted through ``final_config_v2``. Mechanical types come from
``draft_surface`` (deterministic); code-mix and paraphrase are authored candidates in
``data/clean/robustness_v1/authored_candidates.jsonl``. Every variant keeps the canonical
task's ground truth, so each must preserve the canonical's machine literals byte for byte
(course/student/room ids, numbers, emails, mock endpoints); authored variants must also
keep each quoted source title. Nothing here reads ground truth.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from react_agent.authoring.surfaces import INVISIBLE, draft_surface

SCHEMA = "clean_robustness_variant_v1"
MECHANICAL = ("no_diacritic", "word_boundary", "zero_width")
AUTHORED = ("code_mix", "paraphrase")
TYPES = (*MECHANICAL, *AUTHORED)
CANONICAL_IDS = Path("data/clean/v1_1/private/robustness_canonical_ids.json")
TEST_SPLIT = Path("data/clean/v1_1/splits/test.jsonl")
AUTHORED_PATH = Path("data/clean/robustness_v1/authored_candidates.jsonl")
OUTPUT = Path("data/clean/robustness_v1/variants.jsonl")

MACHINE = re.compile(
    r"mock://[^\s<>]+|[\w.+-]+@[\w.-]+\w|\b[A-Z]+_?\d+\b|\b[A-Z]{2,}\d*\b|\d+")
TITLE = re.compile(r"‘[^’]+’")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def machine_literals(text: str) -> list[str]:
    return [m.group().rstrip(".") for m in MACHINE.finditer(text)]


def titles(text: str) -> list[str]:
    return TITLE.findall(text)


def check_variant(canonical: str, variant: str, variant_type: str) -> list[str]:
    """Return QA problems (empty when the variant is admissible)."""
    problems: list[str] = []
    if variant == canonical:
        problems.append("no-op")
    if variant_type != "zero_width" and any(c in variant for c in INVISIBLE):
        problems.append("unexpected invisible character")
    if variant_type == "zero_width" and variant.replace("​", "") != canonical:
        problems.append("zero-width variant is not insertion-only")
    if Counter(machine_literals(canonical)) - Counter(machine_literals(variant)):
        problems.append("machine literal lost or changed")
    if variant_type in AUTHORED and any(t not in variant for t in titles(canonical)):
        problems.append("source title not preserved")
    return problems


def build(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ids = json.loads((root / CANONICAL_IDS).read_text(encoding="utf-8"))["task_ids"]
    tasks = {row["task_id"]: row for row in map(
        json.loads, (root / TEST_SPLIT).read_text(encoding="utf-8").splitlines())}
    authored = {row["task_id"]: row for row in map(
        json.loads, (root / AUTHORED_PATH).read_text(encoding="utf-8").splitlines())}
    if sorted(authored) != sorted(ids):
        raise ValueError("authored candidates must cover exactly the 50 canonical ids")
    rows: list[dict[str, Any]] = []
    problems: dict[str, list[str]] = {}
    for task_id in ids:
        canonical = tasks[task_id]["instruction"]
        literals = tuple(dict.fromkeys(
            lit for lit in machine_literals(canonical) if not lit.isdigit()))
        for variant_type in TYPES:
            if variant_type in MECHANICAL:
                text = draft_surface(canonical, variant_type,  # type: ignore[arg-type]
                                     protected_literals=literals).raw
            else:
                text = authored[task_id][variant_type]
            variant_id = f"rob_{task_id}_{variant_type}"
            found = check_variant(canonical, text, variant_type)
            if found:
                problems[variant_id] = found
            rows.append({
                "schema_version": SCHEMA, "variant_id": variant_id,
                "canonical_task_id": task_id, "split": "test",
                "category": tasks[task_id]["category"], "variant_type": variant_type,
                "instruction": text, "canonical_instruction_sha256": sha256(canonical),
                "protected_literals": list(literals) + (
                    titles(canonical) if variant_type in AUTHORED else []),
                "authoring": "draft_surface" if variant_type in MECHANICAL else "authored",
                "review_status": "pending",
            })
    texts = Counter(row["instruction"] for row in rows)
    report = {
        "schema": SCHEMA, "canonicals": len(ids), "variants": len(rows),
        "per_type": dict(Counter(row["variant_type"] for row in rows)),
        "duplicates": sorted(t for t, n in texts.items() if n > 1),
        "problems": problems, "ground_truth_loaded": 0, "models_scored": 0,
    }
    return rows, report
