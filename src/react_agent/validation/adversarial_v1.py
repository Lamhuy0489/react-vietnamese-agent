"""Deterministic integrity checks for the Phase 3 adversarial draft."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from typing import Any

VARIANT_TYPES = (
    "canonical",
    "no_diacritic",
    "word_boundary",
    "code_mix",
    "zero_width",
    "paraphrase",
)
MACRO_CATEGORIES = {
    "indirect_injection",
    "tool_output_poisoning",
    "data_exfiltration",
    "policy_violation",
}
SPLITS = {"dev", "test"}


def validate_records(
    attacks: Iterable[dict[str, Any]], benign: Iterable[dict[str, Any]]
) -> list[str]:
    """Return all structural failures without reading private ground truth."""
    attack_rows = list(attacks)
    benign_rows = list(benign)
    failures: list[str] = []
    if len(attack_rows) != 350:
        failures.append(f"attack_count:{len(attack_rows)}")
    if len(benign_rows) != 350:
        failures.append(f"benign_count:{len(benign_rows)}")

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    family_splits: dict[str, set[str]] = defaultdict(set)
    for row in attack_rows:
        family = row.get("family_id")
        variant = row.get("variant_type")
        if not isinstance(family, str) or not isinstance(variant, str):
            failures.append("attack_missing_identity")
            continue
        by_family[family].append(row)
        family_splits[family].add(str(row.get("split")))
        if variant not in VARIANT_TYPES:
            failures.append(f"attack_variant:{family}:{variant}")
        if row.get("attack_category") not in MACRO_CATEGORIES:
            failures.append(f"attack_category:{family}")
        if row.get("split") not in SPLITS:
            failures.append(f"attack_split:{family}")
        if not row.get("attack_success_conditions"):
            failures.append(f"missing_success_conditions:{family}:{variant}")
        if not row.get("required_safe_facts"):
            failures.append(f"missing_safe_facts:{family}:{variant}")
    if len(by_family) != 70:
        failures.append(f"family_count:{len(by_family)}")
    for family, rows in by_family.items():
        if len(rows) != 5:
            failures.append(f"family_variant_count:{family}:{len(rows)}")
        if len(family_splits[family]) != 1:
            failures.append(f"family_cross_split:{family}")
    if Counter(
        next(iter(splits)) for splits in family_splits.values() if len(splits) == 1
    ) != Counter({"dev": 40, "test": 30}):
        failures.append("family_split_quota")
    attack_by_pair = {str(row.get("pair_id")): row for row in attack_rows}
    benign_by_pair = {str(row.get("pair_id")): row for row in benign_rows}
    if set(attack_by_pair) != set(benign_by_pair):
        failures.append("pair_key_mismatch")
    for pair_id, attack in attack_by_pair.items():
        control = benign_by_pair.get(pair_id)
        if control is None:
            continue
        for field in (
            "family_id",
            "variant_type",
            "split",
            "user_instruction",
            "required_safe_facts",
        ):
            if attack.get(field) != control.get(field):
                failures.append(f"pair_mismatch:{pair_id}:{field}")
        if control.get("attack_success_conditions"):
            failures.append(f"benign_has_attack_condition:{pair_id}")
    return sorted(set(failures))
