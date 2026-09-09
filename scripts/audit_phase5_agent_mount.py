#!/usr/bin/env python3
"""Select reproducible CPU scan evidence while retaining full-inventory rejection."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import HANDLE, write_receipt
from react_agent.validation.agent_mount_audit_v1 import classify_scan, require

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--remote-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(
        not args.output.exists()
        and args.output.resolve().is_relative_to(ROOT / "results")
        and not args.output.resolve().is_relative_to(args.raw.resolve()),
        "fresh audit directory",
    )
    pre_path = ROOT / "experiments/manifests/phase5_agent_mount_v1_preflight01.json"
    pin_path = ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json"
    pre, pin = read(pre_path), read(pin_path)
    require(
        pre["valid"] is True and all(sha(ROOT / n) == h for n, h in pre["source_sha256"].items()),
        "preflight source changed",
    )
    require(
        not args.raw.is_symlink() and not any(p.is_symlink() for p in args.raw.rglob("*")),
        "raw links",
    )
    raw_hashes = {p.name: sha(p) for p in args.raw.iterdir() if p.is_file()}
    require(
        set(p.name for p in args.raw.iterdir())
        == {"mount_receipt.json", "react-vn-agent-mount-auth-v1.log"},
        "raw output inventory",
    )
    meta = read(args.remote_source / "kernel-metadata.json")
    require(meta["code_file"] == Path(meta["code_file"]).name, "remote filename")
    require(
        sha(args.remote_source / meta["code_file"]) == pre["wrapper_sha256"], "remote wrapper hash"
    )
    for key, value in {
        "id": "huylmhuhu/react-vn-agent-mount-auth-v1",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
    }.items():
        require(meta[key] == value, "remote metadata: " + key)
    # Kaggle serializes this framework enum as "Transformers" in pulled metadata.
    # Keep owner/model/variation/version exact; no arbitrary case-fold or alias.
    require(
        meta["model_sources"] in ([HANDLE], [HANDLE.replace("/transformers/", "/Transformers/")]),
        "remote pinned model version",
    )
    result = classify_scan(
        read(args.raw / "mount_receipt.json"),
        pin,
        {
            "inventory_sha256": sha(pin_path),
            "model_handle": HANDLE,
            "source_commit": pre["source_commit"],
            "verifier_sha256": pre["source_sha256"]["src/react_agent/llm/agent_mount_v1.py"],
        },
    )
    require(
        "AGENT_MOUNT_AUTH_COMPLETE valid=False"
        in (args.raw / "react-vn-agent-mount-auth-v1.log").read_text(),
        "expected rejected scan completion",
    )
    require(
        result["mismatches"] == ["README.md"], "not the predeclared documentation-only mismatch"
    )
    require(
        raw_hashes == {p.name: sha(p) for p in args.raw.iterdir() if p.is_file()}, "raw changed"
    )
    result.update(
        source_commit=pre["source_commit"],
        kernel_submissions=1,
        kernel_version=1,
        kernel_status="ERROR",
        requested_kernel="huylmhuhu/react-vn-agent7b-mount-auth-v1",
        actual_kernel=meta["id"],
        slug_deviation="Kaggle created title-derived slug; no resubmission; source hash exact",
        framework_serialization="Requested transformers; Kaggle metadata returned Transformers",
        raw_sha256=raw_hashes,
        preflight_sha256=sha(pre_path),
        upstream_inventory_sha256=sha(pin_path),
        remote_metadata=meta,
        remote_source_sha256={p.name: sha(p) for p in args.remote_source.iterdir() if p.is_file()},
        source_sha256={
            str(p.relative_to(ROOT)): sha(p)
            for p in (Path(__file__), ROOT / "src/react_agent/validation/agent_mount_audit_v1.py")
        },
        prerequisites=prerequisites(ROOT),
    )
    args.output.mkdir(parents=True)
    write_receipt(args.output / "audit.json", result)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "audit_integrity_valid",
                    "full_inventory_match",
                    "runtime_files_match",
                    "mount_admitted_for_loader",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
