#!/usr/bin/env python3
"""Audit the completed ordinary pair GPU run without launching inference.

The audit authenticates the exact package, remote kernel metadata, native metric
records and the two independent in-process joined audits.  It deliberately does
not turn a technical A/B/A probe into model quality or Phase 5 acceptance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from audit_phase5_guard_gpu_release import audit_dummy

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.ordinary_pair_probe_v1 import native_config
from react_agent.validation.context_stress_audit_v1 import equal, inventory
from react_agent.validation.efficient_requests_audit_v1 import _record, _seconds
from react_agent.validation.guard_probe_audit_v2 import digest, require
from react_agent.validation.ordinary_tokenizer_audit_v1 import audit as audit_tokenizer

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
IMAGE = (
    "gcr.io/kaggle-private-byod/python@sha256:"
    "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
)
KERNEL_ID = "huylmhuhu/react-vn-ordinary-pair-t4x2-v1"
DATASET = "huylmhuhu/react-vn-guard15-probe-data-v1"
AGENT_HANDLE = "qwen-lm/qwen2.5/Transformers/7b-instruct/1"


def _json_bytes(value: dict[str, Any]) -> bytes:
    """Return the exact bytes emitted by ``write_receipt``."""
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _metrics(path: Path) -> list[dict[str, Any]]:
    no_links(path)
    require(path.is_file(), "native metrics file")
    rows = [_record(line) for line in path.read_text(encoding="utf-8").splitlines()]
    require(len(rows) == 4, "one load and three native calls")
    return rows


def _native_metrics(raw: Path, probe: dict[str, Any]) -> dict[str, Any]:
    """Check native load/call identities and derive timing-only observations."""
    config = native_config()
    rows_by_role: dict[str, list[dict[str, Any]]] = {}
    loads: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    for role in ("agent", "guard"):
        rows = _metrics(raw / "ordinary_probe" / f"{role}_hf_metrics.jsonl")
        rows_by_role[role] = rows
        load = rows[0]
        expected_id = getattr(config, role).model_id
        expected_revision = getattr(config, role).model_revision
        equal(load["event"], "load", role + " load event")
        equal(load["model_id"], expected_id, role + " model identity")
        equal(load["model_revision"], expected_revision, role + " model revision")
        equal(load["dtype"], "float16", role + " dtype")
        equal(load["quantization"], None, role + " quantization")
        equal(load["attention"], "sdpa", role + " attention")
        equal(load["torch_version"], "2.10.0+cu128", role + " torch")
        equal(load["transformers_version"], "5.5.0", role + " transformers")
        _seconds(load["load_seconds_including_hashes"], role + " load timing")
        loads.append(
            {
                "role": role,
                "seconds": load["load_seconds_including_hashes"],
                "model_id": load["model_id"],
                "model_revision": load["model_revision"],
            }
        )
        for index, row in enumerate(rows[1:], 1):
            equal(row["event"], "generate", role + " generation event")
            equal(row["call_index"], index, role + " call index")
            equal(row["status"], "OK", role + " generation status")
            _seconds(row["generate_seconds"], role + " generation timing")
            require(type(row["input_tokens"]) is int and row["input_tokens"] > 0, "input tokens")
            require(type(row["output_tokens"]) is int and row["output_tokens"] > 0, "output tokens")
            calls.append(
                {
                    "role": role,
                    "call_index": index,
                    "input_tokens": row["input_tokens"],
                    "output_tokens": row["output_tokens"],
                    "seconds": row["generate_seconds"],
                    "tokens_per_second": row["output_tokens"] / row["generate_seconds"],
                }
            )

    summary = probe["summary"]
    equal(summary["execution_valid"], True, "ordinary execution")
    equal(summary["calls_submitted"], 6, "six submitted calls")
    equal(summary["responses_returned"], 6, "six returned calls")
    equal(summary["reaped"], True, "workers reaped")
    equal(summary["recovery_valid"], True, "signed recovery")
    equal(summary["repeated_a_equal"], {"agent": True, "guard": True}, "A repeatability")
    equal(probe["inner"]["native_policy_attention_metrics_consistent"], True, "native joins")
    return {
        "native_model_loads": len(loads),
        "native_model_generation_calls": len(calls),
        "loads": loads,
        "calls": calls,
        "two_t4_memory_observed": True,
        "worker_pids": {
            role: probe["inner"]["supervisor"]["worker_pids"][role] for role in ("agent", "guard")
        },
        "scope": "Native model load/generation and timing records only; no quality or "
        "Phase 5 acceptance.",
    }


def _check_remote_metadata(remote: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    no_links(remote)
    metadata_path = remote / "kernel-metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    code = metadata.get("code_file")
    require(type(code) is str and Path(code).name == code, "remote code basename")
    remote_hashes = inventory(remote)
    equal(sorted(remote_hashes), sorted(["kernel-metadata.json", code]), "remote source inventory")
    equal(digest(remote / code), receipt["wrapper_sha256"], "remote wrapper hash")
    for key, expected in {
        "id": KERNEL_ID,
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaTeslaT4",
        "docker_image": IMAGE,
        "dataset_sources": [DATASET],
        "kernel_sources": [],
        "competition_sources": [],
    }.items():
        equal(metadata.get(key), expected, "remote metadata " + key)
    require(
        metadata.get("model_sources")
        in ([AGENT_HANDLE], ["qwen-lm/qwen2.5/transformers/7b-instruct/1"]),
        "exact agent model mount",
    )
    return {"metadata": metadata, "sha256": remote_hashes}


def audit(raw: Path, remote: Path, preflight: Path) -> dict[str, Any]:
    """Authenticate one immutable raw result and its remote source identity."""
    no_links(raw)
    no_links(preflight)
    require(raw.is_dir() and preflight.is_file(), "audit inputs")
    receipt = json.loads(preflight.read_text(encoding="utf-8"))
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    equal(receipt["protocol"], "ordinary_pair_gpu_exact_preflight_v1", "preflight protocol")
    require(receipt["valid"] is True and receipt["phase5_accepted"] is False, "preflight scope")
    equal(digest(BUNDLE), receipt["bundle_manifest_sha256"], "frozen bundle")
    equal(bundle["dataset"], DATASET, "bundle dataset")
    equal(prerequisites(ROOT), receipt["prerequisites"], "frozen prerequisites")
    require(
        all(digest(ROOT / name) == value for name, value in receipt["source_sha256"].items()),
        "packaged source bytes",
    )

    bootstrap = json.loads((raw / "ordinary_bootstrap_identity.json").read_text(encoding="utf-8"))
    equal(
        bootstrap,
        {
            "protocol": "ordinary_pair_bootstrap_v1",
            "source_commit": receipt["source_commit"],
            "runtime_commit": receipt["runtime_commit"],
            "base_source_sha256": receipt["base_source_sha256"],
            "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
            "overlay_sha256": receipt["overlay_sha256"],
            "snapshot": bundle["snapshot"],
            "wheel_sha256": bundle["wheel_sha256"],
        },
        "bootstrap source identity",
    )
    remote_info = _check_remote_metadata(remote, receipt)
    dummy = audit_dummy(raw, bundle)

    probe_root = raw / "ordinary_probe"
    native_inner = audit_tokenizer(
        probe_root,
        raw / "generation_policy",
        raw / "attention_policy",
        raw / "publishers",
        raw / "tokenizers",
        pin=GuardSnapshot.model_validate(bundle["snapshot"]),
        commit=receipt["source_commit"],
    )
    remote_audit_path = raw / "ordinary_native_audit.json"
    remote_audit = json.loads(remote_audit_path.read_text(encoding="utf-8"))
    # The worker's own audit is deterministic and must equal two fresh local
    # executions, including the canonical receipt bytes.
    native_inner_again = audit_tokenizer(
        probe_root,
        raw / "generation_policy",
        raw / "attention_policy",
        raw / "publishers",
        raw / "tokenizers",
        pin=GuardSnapshot.model_validate(bundle["snapshot"]),
        commit=receipt["source_commit"],
    )
    equal(native_inner_again, native_inner, "independent joined audits")
    equal(remote_audit, native_inner, "remote joined audit")
    require(
        remote_audit_path.read_bytes() == _json_bytes(native_inner),
        "canonical remote audit bytes",
    )
    inner = native_inner["joined"]
    probe_summary = json.loads((probe_root / "summary.json").read_text(encoding="utf-8"))
    probe = {"summary": probe_summary, "inner": inner}
    native = _native_metrics(raw, probe)

    log_name = KERNEL_ID.rsplit("/", 1)[1] + ".log"
    log_path = raw / log_name
    require(log_path.is_file(), "kernel log")
    require(
        "ORDINARY_PAIR_GPU_V1_COMPLETE" in log_path.read_text(encoding="utf-8"),
        "completion marker",
    )

    expected: set[str] = {
        "ordinary_bootstrap_identity.json",
        "ordinary_native_audit.json",
        log_name,
    }
    for name in ("identity.json", "results.json", "summary.json"):
        expected.add("dummy/" + name)
    task_ids = json.loads((raw / "dummy/identity.json").read_text(encoding="utf-8"))["task_ids"]
    for task_id in task_ids:
        expected.update(f"dummy/tasks/{task_id}/{name}" for name in ("result.json", "trace.jsonl"))
    section_paths = {
        "probe": "ordinary_probe",
        "policy": "generation_policy",
        "attention": "attention_policy",
        "publishers": "publishers",
        "tokenizers": "tokenizers",
    }
    for section, hashes in native_inner["input_sha256"].items():
        expected.update(section_paths[section] + "/" + name for name in hashes)
    raw_hashes = inventory(raw)
    equal(sorted(raw_hashes), sorted(expected), "complete raw inventory")
    equal(inventory(raw), raw_hashes, "raw unchanged during audit")

    return {
        "protocol": "ordinary_pair_t4x2_gpu_release_audit_v1",
        "valid": True,
        "phase5_accepted": False,
        "source_authenticated": True,
        "remote_source_authenticated": True,
        "package_authenticated": True,
        "native_execution_observed": True,
        "tokenizer_metadata_authenticated": native_inner["tokenizer_metadata_authenticated"],
        "joined_audit_byte_identical": True,
        "source_commit": receipt["source_commit"],
        "audit_script_sha256": digest(Path(__file__)),
        "preflight_sha256": digest(preflight),
        "remote_metadata": remote_info["metadata"],
        "remote_sha256": remote_info["sha256"],
        "raw_sha256": raw_hashes,
        "dummy": dummy,
        "native": native,
        "ordinary_audit": {
            "protocol": native_inner["protocol"],
            "valid": native_inner["valid"],
            "tokenizer_ids_bound_to_policy": native_inner["tokenizer_ids_bound_to_policy"],
            "supervisor_records_consistent": inner["supervisor_records_consistent"],
            "native_policy_attention_metrics_consistent": inner[
                "native_policy_attention_metrics_consistent"
            ],
            "allocator_records_within_caps": inner["allocator_records_within_caps"],
            "remote_audit_sha256": digest(remote_audit_path),
        },
        "test_access": "hash-only prerequisites; no Test payload or private ground truth",
        "scope": "One ordinary native A/B/A technical run. No quality, ASR, speed ranking, "
        "full-context/KV, global IPC-cleanup or Phase 5 acceptance claim.",
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
        and not args.output.resolve().is_relative_to(args.raw.resolve())
        and not args.output.resolve().is_relative_to(args.remote.resolve()),
        "fresh release audit output",
    )
    result = audit(args.raw, args.remote, args.preflight)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("ORDINARY_PAIR_T4X2_GPU_AUDIT_COMPLETE phase5_accepted=False")


if __name__ == "__main__":
    main()
