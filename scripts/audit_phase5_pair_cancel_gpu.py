#!/usr/bin/env python3
"""Audit the single completed combined cancellation run without new inference."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from audit_phase5_guard_gpu_release import audit_dummy

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.guard_probe_audit_v2 import digest, read_json, require
from react_agent.validation.pair_cancellation_audit_v1 import audit_probe

ROOT = Path(__file__).resolve().parents[1]
IMAGE = (
    "gcr.io/kaggle-private-byod/python@sha256:"
    "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
)


def shutdown_warnings(log: str) -> dict[str, Any]:
    counts = [int(n) for n in re.findall(r"There appear to be (\d+) leaked semaphore objects", log)]
    return {
        "semaphore_warning_counts": counts,
        "ipc_cleanup_verified": False,
        "scope": "Kernel shutdown warnings are separate from measured worker reap/VRAM recovery",
    }


def audit(raw: Path, remote: Path) -> dict[str, Any]:
    no_links(raw)
    no_links(remote)
    require(not any(p.is_symlink() for p in raw.rglob("*")), "linked raw artifact")
    receipt_path = ROOT / "experiments/manifests/phase5_pair_cancel_gpu_v1_preflight01.json"
    receipt = read_json(receipt_path)
    bundle_path = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
    bundle = read_json(bundle_path)
    require(
        receipt["valid"] is True and digest(bundle_path) == receipt["bundle_manifest_sha256"],
        "frozen bundle",
    )
    hashes = {p.relative_to(raw).as_posix(): digest(p) for p in raw.rglob("*") if p.is_file()}
    require(
        read_json(raw / "pair_cancel_bootstrap_identity.json")
        == {
            "protocol": "pair_cancel_bootstrap_v1",
            "source_commit": receipt["source_commit"],
            "base_source_sha256": receipt["base_source_sha256"],
            "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
            "overlay_sha256": receipt["overlay_sha256"],
            "snapshot": bundle["snapshot"],
            "wheel_sha256": bundle["wheel_sha256"],
        },
        "bootstrap identity",
    )
    metadata = read_json(remote / "kernel-metadata.json")
    require(metadata["code_file"] == Path(metadata["code_file"]).name, "remote filename")
    require(digest(remote / metadata["code_file"]) == receipt["wrapper_sha256"], "remote wrapper")
    for key, value in {
        "id": "huylmhuhu/react-vn-pair-cancel-v1",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaTeslaT4",
        "docker_image": IMAGE,
        "dataset_sources": [bundle["dataset"]],
        "kernel_sources": [],
        "competition_sources": [],
        "model_sources": ["qwen-lm/qwen2.5/Transformers/7b-instruct/1"],
    }.items():
        require(metadata[key] == value, "remote metadata: " + key)
    require(
        all(digest(ROOT / n) == h for n, h in receipt["overlay_sha256"].items()), "overlay drift"
    )
    require(prerequisites(ROOT) == receipt["prerequisites"], "sealed inputs changed")
    result = audit_probe(
        raw / "pair_cancellation",
        GuardSnapshot.model_validate(bundle["snapshot"]),
        receipt["source_commit"],
    )
    result["dummy"] = audit_dummy(raw, bundle)
    expected = {
        "pair_cancel_bootstrap_identity.json",
        "react-vn-pair-cancel-v1.log",
        "dummy/identity.json",
        "dummy/results.json",
        "dummy/summary.json",
    }
    expected.update(n for n in hashes if n.startswith("pair_cancellation/"))
    for task in read_json(raw / "dummy/identity.json")["task_ids"]:
        expected.update(f"dummy/tasks/{task}/{n}" for n in ("result.json", "trace.jsonl"))
    require(set(hashes) == expected, "raw inventory")
    log = (raw / "react-vn-pair-cancel-v1.log").read_text()
    require("PAIR_CANCEL_GPU_COMPLETE" in log, "worker completion")
    result["shutdown_warnings"] = shutdown_warnings(log)
    require(
        hashes == {p.relative_to(raw).as_posix(): digest(p) for p in raw.rglob("*") if p.is_file()},
        "raw changed during audit",
    )
    result.update(
        raw_sha256=hashes,
        preflight_sha256=digest(receipt_path),
        remote_metadata=metadata,
        remote_source_sha256={p.name: digest(p) for p in remote.iterdir() if p.is_file()},
        source_sha256={
            str(p.relative_to(ROOT)): digest(p)
            for p in (
                Path(__file__),
                ROOT / "src/react_agent/validation/pair_cancellation_audit_v1.py",
            )
        },
        test_access="hash-only seals/presealed IDs; no Test or private GT payload",
    )
    return result


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
        "fresh audit output",
    )
    result = audit(args.raw, args.remote_source)
    args.output.mkdir(parents=True)
    write_receipt(args.output / "audit.json", result)
    lines = [
        "# Pair cancellation GPU technical results",
        "",
        "| Trial | Agent ready s | Guard ready s | Busy timeout s | "
        "Busy cleanup | Resident GiB 0 / 1 |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in result["measurements"]:
        workers = row["workers"]
        busy = workers["agent" if row["trial"] == "agent_busy" else "guard"]
        resident = " / ".join(f"{n / 1024**3:.3f}" for n in row["resident_bytes"])
        lines.append(
            f"| {row['trial']} | {workers['agent']['ready_seconds']:.3f} | "
            f"{workers['guard']['ready_seconds']:.3f} | {busy['busy_seconds']:.3f} | "
            f"{busy['cleanup']['method']}/{busy['cleanup']['exitcode']} | {resident} |"
        )
    lines.extend(
        [
            "",
            "Six workers reaped; eighteen recovery samples across two GPUs.",
            "Idle-worker graceful flags and signed residuals remain in audit.json.",
            "",
            result["limitations"],
            "",
            "No model generation or Phase5 acceptance.",
        ]
    )
    lines.extend(
        [
            "",
            "Shutdown semaphore warning counts: "
            + str(result["shutdown_warnings"]["semaphore_warning_counts"]),
            "IPC cleanup is not verified; this resource warning is not a VRAM measurement.",
        ]
    )
    with (args.output / "report.md").open("x") as stream:
        stream.write("\n".join(lines) + "\n")
    print("PASS: combined cancellation resource integrity; Phase5 remains open")


if __name__ == "__main__":
    main()
