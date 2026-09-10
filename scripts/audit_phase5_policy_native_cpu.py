#!/usr/bin/env python3
"""Authenticate the CPU library harness; never claim native model generation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from audit_phase5_guard_gpu_release import audit_dummy

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.generation_policy_v1 import CONFIG_FIELDS, METHODS
from react_agent.llm.model_pair_v1 import ModelIdentity, Role
from react_agent.validation.context_stress_audit_v1 import (
    NATIVE_NONE_FIELDS,
    equal,
    inventory,
    read_record,
)
from react_agent.validation.generation_policy_audit_v1 import GLOBAL_DEFAULTS, audit_policy, resolve
from react_agent.validation.guard_probe_audit_v2 import digest, require

ROOT = Path(__file__).resolve().parents[1]
CASES: tuple[tuple[Role, str], ...] = (
    ("agent", "none"),
    ("guard", "none"),
    ("guard", "error"),
    ("guard", "interrupt"),
)
NATIVE = {
    "backend": "native",
    "native_imported": True,
    "torch": "2.10.0+cu128",
    "transformers": "5.5.0",
    "cuda_used": False,
    "installed_source_sha256": {
        "GenerationMixin": "dde2df36821c0d724b5af47cb0ff71c3c4c1990c86d81b821911127ae4dc1254",
        "GenerationConfig": "0aaf06e21d844256eee23aac663672d0aa9d06ca1f7f59e9be655c761ccdb0a0",
    },
}


def audit_harness(root: Path, commit: str) -> dict[str, Any]:
    hashes = inventory(root)
    expected = {"summary.json"}
    rows, policies = [], {}
    owner = None
    publisher = {
        **dict.fromkeys(CONFIG_FIELDS),
        "do_sample": True,
        "repetition_penalty": 1.1,
        "eos_token_id": [151645, 151643],
        "transformers_version": "5.5.0",
    }
    for role, fault in CASES:
        files: tuple[str, ...]
        name = f"{role}_{fault}"
        path = root / name / "policy"
        entered = read_record(path / "entered.json")
        pid = entered["pid"]
        require(type(pid) is int and pid > 0, "harness PID")
        if owner is None:
            owner = pid
        equal(pid, owner, "one CPU harness owner")
        identity = ModelIdentity(f"synthetic-library-harness-{role}", "v1")
        count = 512 if role == "agent" else 128
        submitted = {
            **dict.fromkeys(NATIVE_NONE_FIELDS),
            "min_new_tokens": count,
            "max_new_tokens": count,
            "do_sample": False,
            "num_beams": 1,
            "use_cache": True,
            "cache_implementation": "dynamic",
            "return_dict_in_generate": True,
            "output_scores": False,
            "output_logits": False,
            "output_attentions": False,
            "output_hidden_states": False,
            "eos_token_id": [151645, 151643],
            "pad_token_id": 151643,
            "transformers_version": "5.5.0",
        }
        common = {
            "protocol": "generation_policy_observation_v1",
            "pid": pid,
            "role": role,
            "model_id": identity.model_id,
            "model_revision": identity.model_revision,
        }
        error = {"none": None, "error": "RuntimeError", "interrupt": "KeyboardInterrupt"}[fault]
        if fault == "none":
            audit = audit_policy(path, role, identity, pid, submitted, publisher)
            equal(read_record(root / name / "audit.json"), audit, "worker/independent audit")
            policies[name] = audit
            files = ("entered", "resolved", "length", "restored", "completed")
            expected.add(f"{name}/audit.json")
        else:
            equal(
                entered,
                {
                    **common,
                    "stage": "entered",
                    "publisher": publisher,
                    "global_defaults": GLOBAL_DEFAULTS,
                    "transformers_version": "5.5.0",
                    "model_generation_calls_planned": 1,
                    "policy_changed": False,
                },
                "failure entry",
            )
            equal(
                read_record(path / "resolved.json"),
                {
                    **common,
                    "stage": "resolved",
                    "submitted": submitted,
                    "resolved": resolve(submitted, publisher),
                    "model_kwargs_keys": ["attention_mask", "input_ids"],
                },
                "failure resolved",
            )
            calls = {METHODS[0]: 1, METHODS[1]: 0}
            equal(
                read_record(path / "error.json"),
                {**common, "stage": "error", "error_class": error, "hook_calls": calls},
                "injected failure",
            )
            equal(
                read_record(path / "restored.json"),
                {**common, "stage": "restored", "methods_restored": True, "hook_calls": calls},
                "failure restoration",
            )
            files = ("entered", "resolved", "error", "restored")
        expected.update(f"{name}/policy/{stage}.json" for stage in files)
        rows.append(
            {
                "case": name,
                "caught": error,
                "methods_restored": True,
                "identity": NATIVE,
                "model_generate_calls": 0,
                "policy_receipt_generation_count_is_synthetic": True,
            }
        )
    summary = {
        "protocol": "native_policy_library_compat_v1",
        "valid": True,
        "backend": "native",
        "source_commit": commit,
        "cases": rows,
        "model_generate_calls": 0,
        "weights_loaded": 0,
        "gpu_used": False,
        "phase5_accepted": False,
        "native_library_verified": True,
        "scope": "Native config/special-token/length functions with synthetic harness; "
        "not Qwen generation or GPU stress",
    }
    equal(read_record(root / "summary.json"), summary, "native harness summary")
    equal(sorted(hashes), sorted(expected), "exact CPU harness inventory")
    equal(inventory(root), hashes, "harness changed during audit")
    return {"summary": summary, "policies": policies, "raw_sha256": hashes}


def audit(raw: Path, remote: Path, preflight: Path) -> dict[str, Any]:
    hashes, remote_hashes = inventory(raw), inventory(remote)
    receipt = read_record(preflight)
    require(
        receipt["valid"] is True and receipt["protocol"] == "policy_native_cpu_exact_preflight_v1",
        "accepted exact preflight",
    )
    bundle_path = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
    bundle = read_record(bundle_path)
    equal(digest(bundle_path), receipt["bundle_manifest_sha256"], "bundle seal")
    equal(prerequisites(ROOT), receipt["prerequisites"], "held-out seals")
    require(
        all(digest(ROOT / n) == h for n, h in receipt["overlay_sha256"].items()), "overlay drift"
    )
    metadata = read_record(remote / "kernel-metadata.json")
    code = metadata["code_file"]
    require(type(code) is str and Path(code).name == code, "remote code basename")
    equal(digest(remote / code), receipt["wrapper_sha256"], "remote wrapper")
    for key, value in {
        "id": "huylmhuhu/react-vn-policy-native-compat-v1",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "dataset_sources": [bundle["dataset"]],
        "model_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "docker_image": "gcr.io/kaggle-private-byod/python@sha256:"
        "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
    }.items():
        equal(metadata[key], value, "remote metadata " + key)
    require(metadata.get("machine_shape") in (None, ""), "CPU only")
    equal(
        read_record(raw / "policy_native_bootstrap_identity.json"),
        {
            "protocol": "policy_native_bootstrap_v1",
            "source_commit": receipt["source_commit"],
            "base_source_sha256": receipt["base_source_sha256"],
            "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
            "overlay_sha256": receipt["overlay_sha256"],
            "snapshot": bundle["snapshot"],
            "wheel_sha256": bundle["wheel_sha256"],
        },
        "bootstrap identity",
    )
    result = audit_harness(raw / "policy_native", receipt["source_commit"])
    dummy = audit_dummy(raw, bundle)
    names = {
        "policy_native_bootstrap_identity.json",
        "react-vn-policy-native-compat-v1.log",
        "dummy/identity.json",
        "dummy/results.json",
        "dummy/summary.json",
    }
    for task in read_record(raw / "dummy/identity.json")["task_ids"]:
        names.update(f"dummy/tasks/{task}/{n}" for n in ("result.json", "trace.jsonl"))
    names.update("policy_native/" + n for n in result["raw_sha256"])
    equal(sorted(hashes), sorted(names), "complete CPU output inventory")
    log = (raw / "react-vn-policy-native-compat-v1.log").read_text()
    require("POLICY_NATIVE_CPU_COMPLETE" in log, "CPU completion marker")
    equal(inventory(raw), hashes, "raw changed")
    equal(inventory(remote), remote_hashes, "remote changed")
    return {
        "protocol": "policy_native_cpu_release_audit_v1",
        "valid": True,
        "phase5_accepted": False,
        "native_library_verified": True,
        "model_generate_calls": 0,
        "weights_loaded": 0,
        "gpu_used": False,
        "source_commit": receipt["source_commit"],
        "preflight_sha256": digest(preflight),
        "harness": result,
        "dummy": dummy,
        "raw_sha256": hashes,
        "remote_sha256": remote_hashes,
        "remote_metadata": metadata,
        "limitations": "CPU native library functions only, not actual Qwen generation, "
        "maximum context GPU fit, publisher metadata authentication, IPC leak-free "
        "or Phase5 acceptance",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--remote", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    if args.output.exists() or any(
        args.output.resolve().is_relative_to(p.resolve()) for p in (args.raw, args.remote)
    ):
        raise ValueError("fresh audit outside raw inputs required")
    result = audit(args.raw, args.remote, args.preflight)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("POLICY_NATIVE_CPU_AUDIT_COMPLETE model_generate_calls=0 gpu_used=False")


if __name__ == "__main__":
    main()
