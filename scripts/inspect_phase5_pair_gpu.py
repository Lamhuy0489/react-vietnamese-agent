#!/usr/bin/env python3
"""Read-only pair GPU evidence inventory, including incomplete/failed executions.

Envelope integrity is separate from execution acceptance. This inspector never
certifies model quality, model fit, graceful close, or Phase 5 completion.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from audit_phase5_guard_gpu_release import audit_dummy

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.model_pair_probe_v1 import TOLERANCE, validate_memory
from react_agent.validation.guard_probe_audit_v2 import digest, read_json, require

ROOT = Path(__file__).resolve().parents[1]


def recovery_observations(probe: Path) -> dict[str, Any]:
    """Recompute only recovery from all six samples; missing evidence is not pass."""
    names = ["baseline.json", *[f"recovery_{i}.json" for i in range(6)]]
    if not all((probe / name).is_file() for name in names):
        return {"complete": False, "recovery_pass": False}
    rows = [read_json(probe / name)["memory"] for name in names]
    for row in rows:
        validate_memory(row)
        require(
            [v["total_bytes"] for v in row] == [v["total_bytes"] for v in rows[0]],
            "device total changed",
        )
    residuals = [
        [rows[0][i]["free_bytes"] - row[i]["free_bytes"] for i in (0, 1)] for row in rows[1:]
    ]
    elapsed = [read_json(probe / name)["elapsed_seconds"] for name in names[1:]]
    require(
        all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in elapsed)
        and elapsed == sorted(elapsed),
        "recovery sample time order",
    )
    return {
        "complete": True,
        "recovery_pass": all(abs(v) <= TOLERANCE for row in residuals[-3:] for v in row),
        "signed_residual_bytes": residuals,
        "elapsed_seconds": elapsed,
    }


def inspect(raw: Path, remote: Path) -> dict[str, Any]:
    no_links(raw)
    no_links(remote)
    require(not any(p.is_symlink() for p in raw.rglob("*")), "linked raw artifact")
    hashes = {p.relative_to(raw).as_posix(): digest(p) for p in raw.rglob("*") if p.is_file()}
    receipt = read_json(ROOT / "experiments/manifests/phase5_pair_gpu_v1_preflight02.json")
    bundle_path = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
    bundle = read_json(bundle_path)
    require(digest(bundle_path) == receipt["bundle_manifest_sha256"], "bundle hash")
    metadata = read_json(remote / "kernel-metadata.json")
    require(metadata["code_file"] == Path(metadata["code_file"]).name, "remote filename")
    require(digest(remote / metadata["code_file"]) == receipt["wrapper_sha256"], "remote source")
    for key, value in {
        "id": "huylmhuhu/react-vn-pair-gpu-v1",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": [bundle["dataset"]],
        # Kaggle returns the display-case framework label for the same pinned handle.
        "model_sources": ["qwen-lm/qwen2.5/Transformers/7b-instruct/1"],
        "competition_sources": [],
        "kernel_sources": [],
    }.items():
        require(metadata[key] == value, "remote metadata: " + key)
    require(
        read_json(raw / "pair_bootstrap_identity.json")
        == {
            "protocol": "pair_bootstrap_v1",
            "source_commit": receipt["source_commit"],
            "base_source_sha256": receipt["base_source_sha256"],
            "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
            "overlay_sha256": receipt["overlay_sha256"],
            "snapshot": bundle["snapshot"],
            "wheel_sha256": bundle["wheel_sha256"],
        },
        "bootstrap identity",
    )
    require(
        all(digest(ROOT / n) == h for n, h in receipt["overlay_sha256"].items()),
        "local frozen overlay changed",
    )
    require(prerequisites(ROOT) == receipt["prerequisites"], "sealed input changed")
    dummy = audit_dummy(raw, bundle)
    probe = raw / "pair_probe"
    observations = {}
    names = (
        "manifest",
        "summary",
        "error",
        "baseline",
        "ready",
        "closed",
        "agent_call",
        "guard_call",
    )
    for name in names:
        path = probe / f"{name}.json"
        if path.is_file():
            observations[name] = read_json(path)
    metrics = {}
    for role in ("agent", "guard"):
        path = probe / f"{role}_hf_metrics.jsonl"
        if path.is_file():
            metrics[role] = [json.loads(line) for line in path.read_text().splitlines()]
    require(
        hashes == {p.relative_to(raw).as_posix(): digest(p) for p in raw.rglob("*") if p.is_file()},
        "raw artifact changed during inspection",
    )
    return {
        "protocol": "phase5_pair_gpu_evidence_inspection_v1",
        "envelope_integrity_valid": True,
        "execution_acceptance": "NOT_CERTIFIED_BY_THIS_INSPECTOR",
        "phase5_accepted": False,
        "raw_sha256": hashes,
        "remote_metadata": metadata,
        "remote_metadata_sha256": digest(remote / "kernel-metadata.json"),
        "wrapper_sha256": receipt["wrapper_sha256"],
        "dummy": dummy,
        "observations": observations,
        "hf_metrics": metrics,
        "recomputed_recovery": recovery_observations(probe),
        "test_access": "seals/hash-only; no Test payload or private ground truth",
        "scope": "Source/inputs/Dummy/raw integrity and recovery only; "
        "retain failed outputs unchanged",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--remote-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    require(
        not args.output.exists()
        and args.output.resolve().is_relative_to(ROOT / "results")
        and not args.output.resolve().is_relative_to(args.raw.resolve()),
        "fresh results-only output outside raw",
    )
    result = inspect(args.raw, args.remote_source)
    write_receipt(args.output, result)
    print("PAIR_EVIDENCE_INSPECTED; execution acceptance remains separate")


if __name__ == "__main__":
    main()
