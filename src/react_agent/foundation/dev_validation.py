"""Phase 4 primitive QA: hash-only Test integrity, Dev text only, no model/GT loading."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

from react_agent.adversarial_release import load_split
from react_agent.authoring.admission_review import verify_hash_map
from react_agent.authoring.release_v2 import verify_seal
from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.foundation.normalization import PROFILES, normalize, text_hash


def prerequisites(root: Path) -> dict[str, Any]:
    clean = root / "data/clean/v1_1"
    manifest = json.loads((clean / "manifests/benchmark_manifest.json").read_text(encoding="utf-8"))
    if manifest["benchmark"] != "clean_v1.1" or manifest["frozen"] is not True:
        raise ValueError("clean release is not frozen")
    verify_hash_map(clean, manifest["component_hashes"])
    if len(manifest["component_hashes"]) != 18:
        raise ValueError("unexpected clean component inventory")
    ids = json.loads((clean / "private/robustness_canonical_ids.json").read_text(encoding="utf-8"))[
        "task_ids"
    ]
    if len(ids) != 50 or len(set(ids)) != 50:
        raise ValueError("50 unique pre-sealed robustness IDs required")
    closure_path = root / "experiments/manifests/phase3_release_v2_closure.json"
    closure = json.loads(closure_path.read_text(encoding="utf-8"))
    release = root / "data/adversarial/release_v2"
    if hashlib.sha256((release / "seal.json").read_bytes()).hexdigest() != closure["seal_sha256"]:
        raise ValueError("adversarial seal differs from closure receipt")
    status = verify_seal(root, release)
    return {
        "clean_frozen": True,
        "robustness_ids_presealed": 50,
        "adversarial_seal_valid": status["valid"],
        "test_access": "hash-only; robustness IDs only",
        "clean_component_hashes": manifest["component_hashes"],
        "adversarial_seal_sha256": closure["seal_sha256"],
    }


def validate_dev(root: Path) -> dict[str, Any]:
    root = root.resolve()
    pre = prerequisites(root)
    clean_path = root / "data/clean/v1_1/splits/dev.jsonl"
    clean = [json.loads(s) for s in clean_path.read_text(encoding="utf-8").splitlines()]
    if len(clean) != 150 or any(r["split"] != "dev" for r in clean):
        raise ValueError("exact clean Dev split required")
    dev = load_split(root / "data/adversarial/release_v2")
    texts = [(r["task_id"], r["instruction"]) for r in clean]
    texts.extend((r.variant_id, getattr(r.overlay, r.branch + "_text")) for r in dev)
    if len(texts) != 550 or len({identity for identity, _ in texts}) != 550:
        raise ValueError("Dev coverage/identity mismatch")
    counts: Counter[str] = Counter()
    summaries = []
    timings = []
    for index, (identity, text) in enumerate(texts):
        for profile in PROFILES:
            started = perf_counter()
            result = normalize(text, profile)
            timings.append(perf_counter() - started)
            if (
                normalize(text, profile) != result
                or normalize(result.normalized_text, profile).normalized_text
                != result.normalized_text
            ):
                raise ValueError("Dev normalization not deterministic/idempotent")
            if result.raw_text != text or result.input_hash != text_hash(text):
                raise ValueError("raw changed during normalization")
            if profile == "raw_v1" and result.normalized_text != text:
                raise ValueError("raw profile changed content")
            # Synthetic stress labels, not annotations inferred from benchmark GT.
            store = ArtifactStore(f"dev_{index}_{profile}")
            raw = store.create(
                text,
                artifact_type=ArtifactType.DOCUMENT_CONTENT,
                source_type=SourceType.SYSTEM,
                source_id=identity,
                producer="primitive_qa",
                created_step=0,
                sensitivity=Sensitivity.CONFIDENTIAL,
                trust=Trust.UNTRUSTED,
            )
            view = store.normalized_view(raw.artifact_id, result)
            if (view.sensitivity, view.trust) != (raw.sensitivity, raw.trust):
                raise ValueError("normalization upgraded trust or declassified")
            restored = ArtifactStore.deserialize(store.run_id, store.serialize())
            if restored.all() != store.all() or restored.ancestors(view.artifact_id) != (raw,):
                raise ValueError("artifact round-trip/lineage mismatch")
            counts[profile + ":changed"] += result.input_hash != result.output_hash
            summaries.append(
                {
                    "identity": identity,
                    "profile": profile,
                    "raw_hash": result.input_hash,
                    "view_hash": result.output_hash,
                    "cache_key": result.cache_key,
                    "features": asdict(result.features),
                }
            )
    after = prerequisites(root)
    if after != pre:
        raise ValueError("frozen dependencies changed during Dev QA")
    ordered = sorted(timings)
    return {
        "schema_version": "phase4_primitive_dev_qa_v1",
        "valid": True,
        "phase4_accepted": False,
        "runtime_integration_complete": False,
        "clean_dev_instructions": 150,
        "adversarial_dev_payloads": 400,
        "profile_checks": len(summaries),
        "profiles": list(PROFILES),
        "changed_counts": dict(counts),
        "prerequisites": pre,
        "test_payloads_parsed_by_this_validator": 0,
        "private_ground_truth_loaded": False,
        "model_runs": 0,
        "broker_runs": 0,
        "label_qa_scope": "synthetic S2/UNTRUSTED stress labels, not benchmark source annotation",
        "normalization_timing_ms": {
            "count": len(timings),
            "mean": sum(timings) / len(timings) * 1000,
            "p95": ordered[int((len(ordered) - 1) * 0.95)] * 1000,
            "scope": "local single-call normalization only; diagnostic, not LLM performance",
        },
        "stable_summary_sha256": text_hash(
            json.dumps(summaries, ensure_ascii=False, sort_keys=True)
        ),
        "remaining": [
            "ControlState/ContextBundle and pass-through hooks",
            "runtime artifact integration, source metadata and A0 parity",
            "smoke/clean/attack Dev trajectory coverage and phase acceptance",
        ],
    }
