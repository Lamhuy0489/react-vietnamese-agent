"""Static diagnostics of the unreviewed v1 draft, never a semantic acceptance oracle.

Reads both draft splits for integrity only. Returns counts/hashes, not held-out
payloads. Does not invoke models, alter splits or modify benchmark artifacts.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from react_agent.validation.adversarial_v1 import MACRO_CATEGORIES, validate_records

UNVERIFIED_GATES = (
    "reachable_overlay_and_safe_path_execution",
    "typed_proposed_executed_and_final_violation_oracles",
    "sensitive_artifact_existence_and_authorization",
    "canonical_and_variant_semantic_equivalence_review",
    "payload_overlay_mapping_and_environment_freeze",
)


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"expected object records: {path.name}")
    return rows


def template_key(text: str) -> str:
    """Conservative candidate finder, not a proof of semantic equivalence."""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"[\w.+-]+@[\w.-]+", "<recipient>", text)
    text = re.sub(r"\d+", "<number>", text)
    return " ".join(text.split())


def no_diacritics(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def audit(root: Path) -> dict[str, Any]:
    canonical = load_rows(root / "canonical/attacks.jsonl")
    controls = load_rows(root / "canonical/benign.jsonl")
    attacks = load_rows(root / "variants/dev_attacks.jsonl") + load_rows(
        root / "variants/test_attacks.jsonl"
    )
    benign = load_rows(root / "variants/dev_benign.jsonl") + load_rows(
        root / "variants/test_benign.jsonl"
    )
    manifest = json.loads((root / "manifests/adversarial_manifest.json").read_text())
    issues: Counter[str] = Counter()
    structural = validate_records(attacks, benign)
    issues.update(f"structural:{f.split(':')[0]}" for f in structural)
    by_family = {str(row.get("family_id")): row for row in canonical}
    control_by_family = {str(row.get("family_id")): row for row in controls}
    if len(canonical) != 70 or len(by_family) != 70:
        issues["canonical_identity_or_count"] += 1
    if len(controls) != 70 or set(control_by_family) != set(by_family):
        issues["canonical_benign_identity_or_count"] += 1
    if {str(r.get("family_id")) for r in attacks} != set(by_family):
        issues["canonical_variant_family_mismatch"] += 1
    for row in controls:
        if row.get("malicious_factor") or row.get("attack_success_conditions"):
            issues["canonical_benign_contains_attack_annotation"] += 1

    families_per_split: dict[str, set[str]] = defaultdict(set)
    for row in attacks:
        families_per_split[str(row.get("split"))].add(str(row.get("family_id")))
    categories: dict[str, dict[str, int]] = {}
    for split in ("dev", "test"):
        counts = Counter(
            by_family[f]["attack_category"] for f in families_per_split[split] if f in by_family
        )
        categories[split] = {category: counts[category] for category in sorted(MACRO_CATEGORIES)}
        issues["category_absent_from_split"] += sum(c == 0 for c in categories[split].values())

    template_groups: dict[str, list[str]] = defaultdict(list)
    for family, row in by_family.items():
        template_groups[template_key(str(row.get("malicious_factor", "")))].append(family)
        if row.get("target_sink") == "post_webhook_mock" and (
            "@" in str(row.get("recipient", "")) or not row.get("endpoint")
        ):
            issues["webhook_target_not_typed_endpoint"] += 1
        if row.get("attack_category") == "data_exfiltration" and not row.get(
            "target_sensitive_artifacts"
        ):
            issues["exfiltration_without_sensitive_artifact_reference"] += 1
    overlap_groups = sum(
        bool(set(families) & families_per_split["dev"])
        and bool(set(families) & families_per_split["test"])
        for families in template_groups.values()
    )
    issues["cross_split_payload_template_candidate"] += overlap_groups

    for kind, rows in (("attack", attacks), ("benign", benign)):
        for row in rows:
            family_row = by_family.get(str(row.get("family_id")))
            if family_row is None:
                continue
            variant = str(row.get("variant_type"))
            original = family_row.get("malicious_factor" if kind == "attack" else "benign_factor")
            if not isinstance(original, str):
                issues[f"{kind}:missing_canonical_payload"] += 1
                continue
            payload = row.get("payload")
            if not isinstance(payload, str):
                continue  # Structural validator already rejects this.
            if payload == original:
                issues[f"{kind}:unchanged_payload:{variant}"] += 1
            if variant == "no_diacritic" and payload != no_diacritics(original):
                issues[f"{kind}:incorrect_no_diacritic"] += 1
            if variant == "zero_width" and payload.replace("\u200b", "") != original:
                issues[f"{kind}:zero_width_not_insertion_only"] += 1

    expected_hash = hashlib.sha256(
        "".join(json.dumps(r, sort_keys=True) for r in attacks + benign).encode()
    ).hexdigest()
    manifest_hash_matches = expected_hash == manifest.get("sha256")
    if not manifest_hash_matches:
        issues["draft_manifest_hash_mismatch"] += 1
    if manifest.get("status") != "draft_unreviewed":
        issues["unsupported_release_status_for_draft_auditor"] += 1

    files = sorted(p for p in root.rglob("*") if p.is_file())
    return {
        "scope": "static integrity audit of unreviewed v1; no model execution or data edits",
        "acceptance_ready": False,
        "acceptance_note": "This diagnostic audit cannot certify semantic or executable gates.",
        "draft_structure_valid": not structural,
        "draft_manifest_hash_matches": manifest_hash_matches,
        "canonical_families": len(canonical),
        "attack_variants": len(attacks),
        "benign_variants": len(benign),
        "model_runs": 0,
        "test_payloads_read_for_static_integrity_only": True,
        "family_categories_by_split": categories,
        "normalized_payload_template_groups": len(template_groups),
        "template_overlap_is_candidate_not_semantic_proof": True,
        "issues": dict(sorted((k, v) for k, v in issues.items() if v)),
        "unverified_acceptance_gates": list(UNVERIFIED_GATES),
        "missing_artifact_directories": [
            name
            for name in ("overlays", "payloads", "mappings", "reviews", "checksums")
            if not (root / name).is_dir()
        ],
        "input_file_sha256": {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files
        },
    }
