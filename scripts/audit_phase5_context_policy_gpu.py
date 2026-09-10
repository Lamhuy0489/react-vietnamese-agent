#!/usr/bin/env python3
"""Authenticate a complete context/policy GPU release; no inference or raw mutations."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from audit_phase5_guard_gpu_release import audit_dummy
from audit_phase5_pair_progress_gpu import IMAGE, shutdown_warnings

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.context_policy_audit_v1 import audit_combined
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.guard_probe_audit_v2 import digest, require

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
BUNDLE_SHA = "b14976413b72898b6c0c1b8c46c1ebb0f62f63633f647ab2064fbc048262240f"


def audit(raw: Path, remote: Path, preflight: Path) -> dict[str, Any]:
    raw_hashes, remote_hashes = inventory(raw), inventory(remote)
    for path in (preflight, BUNDLE):
        no_links(path)
    receipt, bundle = read_record(preflight), read_record(BUNDLE)
    equal(receipt["protocol"], "context_policy_gpu_exact_preflight_v1", "preflight protocol")
    require(receipt["valid"] is True and receipt["phase5_accepted"] is False, "preflight result")
    equal(digest(BUNDLE), BUNDLE_SHA, "frozen bundle bytes")
    equal(receipt["bundle_manifest_sha256"], BUNDLE_SHA, "preflight bundle")
    equal(prerequisites(ROOT), receipt["prerequisites"], "held-out seals")
    require(
        all(digest(ROOT / n) == h for n, h in receipt["overlay_sha256"].items()), "overlay drift"
    )
    metadata = read_record(remote / "kernel-metadata.json")
    code = metadata["code_file"]
    require(type(code) is str and Path(code).name == code, "remote code basename")
    equal(sorted(remote_hashes), sorted([code, "kernel-metadata.json"]), "remote inventory")
    equal(digest(remote / code), receipt["wrapper_sha256"], "remote wrapper")
    for key, expected in {
        "id": "huylmhuhu/react-vn-context-policy-v1",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaTeslaT4",
        "docker_image": IMAGE,
        "dataset_sources": [bundle["dataset"]],
        "kernel_sources": [],
        "competition_sources": [],
    }.items():
        equal(metadata[key], expected, "remote metadata " + key)
    require(
        metadata["model_sources"]
        in (
            ["qwen-lm/qwen2.5/Transformers/7b-instruct/1"],
            ["qwen-lm/qwen2.5/transformers/7b-instruct/1"],
        ),
        "exact pinned agent mount",
    )
    equal(
        read_record(raw / "context_policy_bootstrap_identity.json"),
        {
            "protocol": "context_policy_bootstrap_v1",
            "source_commit": receipt["source_commit"],
            "base_source_sha256": receipt["base_source_sha256"],
            "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
            "overlay_sha256": receipt["overlay_sha256"],
            "snapshot": bundle["snapshot"],
            "wheel_sha256": bundle["wheel_sha256"],
        },
        "bootstrap source identity",
    )
    result = audit_combined(
        raw / "context_stress",
        raw / "generation_policy",
        ROOT / "docs/evaluation/publisher_policy_v1",
        GuardSnapshot.model_validate(bundle["snapshot"]),
        receipt["source_commit"],
    )
    dummy = audit_dummy(raw, bundle)
    names = {
        "context_policy_bootstrap_identity.json",
        "react-vn-context-policy-v1.log",
        "dummy/identity.json",
        "dummy/results.json",
        "dummy/summary.json",
    }
    for task in read_record(raw / "dummy/identity.json")["task_ids"]:
        names.update(f"dummy/tasks/{task}/{n}" for n in ("result.json", "trace.jsonl"))
    names.update("context_stress/" + n for n in result["input_sha256"]["probe"])
    names.update("generation_policy/" + n for n in result["input_sha256"]["policy"])
    equal(sorted(raw_hashes), sorted(names), "complete raw inventory")
    log = (raw / "react-vn-context-policy-v1.log").read_text()
    require("CONTEXT_POLICY_GPU_COMPLETE" in log, "worker completion marker")
    equal(inventory(raw), raw_hashes, "raw mutated during audit")
    equal(inventory(remote), remote_hashes, "remote mutated during audit")
    return {
        "protocol": "context_policy_gpu_release_audit_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_authenticated": True,
        "publisher_metadata_authenticated": True,
        "source_commit": receipt["source_commit"],
        "combined": result,
        "dummy": dummy,
        "raw_sha256": raw_hashes,
        "remote_sha256": remote_hashes,
        "remote_metadata": metadata,
        "preflight_sha256": digest(preflight),
        "shutdown_warnings": shutdown_warnings(log),
        "scope": "One instrumented context workload per role; no quality, cross-model speed "
        "ranking, separated prefill or global IPC/driver-clean claim. Not Phase5 acceptance",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--remote", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    require(
        not args.output.exists()
        and not any(
            args.output.resolve().is_relative_to(p.resolve()) for p in (args.raw, args.remote)
        ),
        "fresh audit outside immutable inputs",
    )
    result = audit(args.raw, args.remote, args.preflight)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("CONTEXT_POLICY_GPU_AUDIT_COMPLETE phase5_accepted=False")


if __name__ == "__main__":
    main()
