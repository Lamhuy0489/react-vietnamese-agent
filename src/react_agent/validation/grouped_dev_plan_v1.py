"""Outcome-independent grouped Dev scheduling metadata, never a worker prompt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links

SELECTION_SEED = "phase5-grouped-dev-structured-output-v1"
# From accepted release_v2 seal 431b81118026bef6c60e33306e51df71160504579e76ea08fb4648005fa1cb6b.
# Fixed Dev pins avoid opening any Test payload or copying evaluator annotations.
DEV_SHA256 = {
    "dev_attack.jsonl": "764cf63ac986d89c747c9baa9019d7025a3bc38c5b9cf9c8cf151edfb7d4beba",
    "dev_benign.jsonl": "93c9e7a70758ed8d5f8a8fa35c5c605edf4d05d57432fa86c6d1872c6a7de739",
}


def plan(release: Path) -> dict[str, Any]:
    """Read only the two explicit Dev files; never traverse the release directory."""
    sources: dict[str, str] = {}
    pairs: dict[str, dict[str, dict[str, str]]] = {}
    variant_ids: set[str] = set()
    families: dict[str, str] = {}
    for branch in ("attack", "benign"):
        path = release / f"dev_{branch}.jsonl"
        no_links(path)
        raw = path.read_bytes()
        sources[path.name] = hashlib.sha256(raw).hexdigest()
        if sources[path.name] != DEV_SHA256[path.name]:
            raise ValueError("accepted Dev source hash mismatch")
        rows = [json.loads(line) for line in raw.splitlines()]
        if len(rows) != 200:
            raise ValueError("exact frozen Dev branch count required")
        for row in rows:
            if row["split"] != "dev" or row["branch"] != branch:
                raise ValueError("Dev branch identity mismatch")
            keys = ("variant_id", "pair_id", "family_id", "group_id", "variant_type")
            if any(type(row[k]) is not str or not row[k] for k in keys):
                raise ValueError("string scheduling identities required")
            meta = {k: row[k] for k in keys}
            identity, family, group = meta["variant_id"], meta["family_id"], meta["group_id"]
            if identity in variant_ids or families.get(family, group) != group:
                raise ValueError("duplicate identity or family crosses groups")
            variant_ids.add(identity)
            families[family] = group
            pair = pairs.setdefault(meta["pair_id"], {})
            if branch in pair:
                raise ValueError("duplicate pair branch")
            pair[branch] = meta
    variants: dict[str, set[str]] = {}
    for pair in pairs.values():
        if set(pair) != {"attack", "benign"}:
            raise ValueError("matched benign branch required")
        attack, benign = pair["attack"], pair["benign"]
        if any(
            attack[k] != benign[k] for k in ("family_id", "group_id", "variant_type", "pair_id")
        ):
            raise ValueError("paired family/group/variant mismatch")
        observed = variants.setdefault(attack["family_id"], set())
        if attack["variant_type"] in observed:
            raise ValueError("duplicate family variant")
        observed.add(attack["variant_type"])
    expected = {"paraphrase", "code_mix", "no_diacritic", "word_boundary", "zero_width"}
    if (
        len(families) != 40
        or len(set(families.values())) != 8
        or any(v != expected for v in variants.values())
    ):
        raise ValueError("frozen grouped Dev geometry required")
    selected_families = []
    for group in sorted(set(families.values())):
        candidates = [family for family, member in families.items() if member == group]
        selected_families.append(
            min(
                candidates,
                key=lambda f: (hashlib.sha256((SELECTION_SEED + "\n" + f).encode()).hexdigest(), f),
            )
        )
    selected = [
        pair
        for pair in pairs.values()
        if pair["attack"]["family_id"] in selected_families
        and pair["attack"]["variant_type"] == "paraphrase"
    ]
    selected.sort(key=lambda pair: (pair["attack"]["group_id"], pair["attack"]["family_id"]))
    return dict(
        protocol="phase5_grouped_dev_plan_v1",
        selection_seed=SELECTION_SEED,
        dev_source_sha256=sources,
        groups=8,
        families=40,
        selected_families=selected_families,
        selected_pairs=selected,
        selected_public_cases=16,
        levels=[f"A{i}" for i in range(7)],
        expected_runtime_tasks=112,
        automatic_semantic_retry=False,
        dispatch_allowed=False,
        guard_model_selected=False,
        phase5_accepted=False,
        remaining_dev_families=sorted(set(families) - set(selected_families)),
        worker_payload_included=False,
        test_payload_accessed=False,
        scope="Planning metadata only. Paired screening sample, not final ASR/FPR; "
        "freeze worker inputs, policies and exact package before dispatch.",
    )
