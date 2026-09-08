#!/usr/bin/env python3
"""Audit downloaded cancellation GPU artifacts without rerunning inference."""

from __future__ import annotations

import argparse
from pathlib import Path

from audit_phase5_guard_gpu_release import audit_dummy

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.guard_probe_v1 import write_json
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.guard_cancellation_audit_v1 import audit_probe
from react_agent.validation.guard_probe_audit_v2 import digest, read_json, require

ROOT = Path(__file__).resolve().parents[1]


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
        "fresh audit output",
    )
    receipt_path = ROOT / "experiments/manifests/phase5_guard_cancellation_v1_preflight01.json"
    bundle_path = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
    receipt, bundle = read_json(receipt_path), read_json(bundle_path)
    require(
        receipt["valid"] is True and digest(bundle_path) == receipt["bundle_manifest_sha256"],
        "frozen bundle",
    )
    require(
        not args.raw.is_symlink() and not any(p.is_symlink() for p in args.raw.rglob("*")),
        "linked raw artifact",
    )
    hashes = {
        p.relative_to(args.raw).as_posix(): digest(p) for p in args.raw.rglob("*") if p.is_file()
    }
    require(
        read_json(args.raw / "guard_bundle_identity.json")
        == {
            "source_commit": bundle["source_commit"],
            "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
            "snapshot": bundle["snapshot"],
            "wheel_sha256": bundle["wheel_sha256"],
        },
        "bundle identity",
    )
    require(
        read_json(args.raw / "guard_bootstrap_identity.json")
        == {
            "protocol": "guard_cancellation_bootstrap_v1",
            "overlay_sha256": receipt["overlay_sha256"],
            "bootstrap_commit": receipt["bootstrap_commit"],
            "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
        },
        "bootstrap identity",
    )
    remote = read_json(args.remote_source / "kernel-metadata.json")
    require(remote["code_file"] == Path(remote["code_file"]).name, "remote filename")
    require(
        digest(args.remote_source / remote["code_file"]) == receipt["wrapper_sha256"],
        "remote wrapper",
    )
    for key, value in {
        "id": "huylmhuhu/react-vn-guard-cancel-run-v1",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": [bundle["dataset"]],
        "model_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
    }.items():
        require(remote[key] == value, "remote metadata: " + key)
    require(
        all(digest(ROOT / p) == h for p, h in receipt["overlay_sha256"].items()),
        "local overlay changed",
    )
    require(prerequisites(ROOT) == receipt["prerequisites"], "sealed input changed")
    result = audit_probe(
        args.raw / "cancellation_probe",
        GuardSnapshot.model_validate(bundle["snapshot"]),
        receipt["bootstrap_commit"],
    )
    result["dummy"] = audit_dummy(args.raw, bundle)
    expected = {
        "guard_bundle_identity.json",
        "guard_bootstrap_identity.json",
        "react-vn-guard-cancel-run-v1.log",
        "dummy/identity.json",
        "dummy/results.json",
        "dummy/summary.json",
    }
    expected.update(p for p in hashes if p.startswith("cancellation_probe/"))
    for task in read_json(args.raw / "dummy/identity.json")["task_ids"]:
        expected.update(f"dummy/tasks/{task}/{name}" for name in ("result.json", "trace.jsonl"))
    require(set(hashes) == expected, "raw inventory")
    require(
        "GUARD_CANCELLATION_GPU_COMPLETE"
        in (args.raw / "react-vn-guard-cancel-run-v1.log").read_text(),
        "kernel completion",
    )
    require(
        hashes
        == {
            p.relative_to(args.raw).as_posix(): digest(p)
            for p in args.raw.rglob("*")
            if p.is_file()
        },
        "raw changed during audit",
    )
    result.update(
        raw_sha256=hashes,
        preflight_sha256=digest(receipt_path),
        bootstrap_commit=receipt["bootstrap_commit"],
        source_commit=bundle["source_commit"],
        bundle_manifest_sha256=digest(bundle_path),
        remote_metadata=remote,
        remote_source_sha256={
            p.name: digest(p) for p in args.remote_source.iterdir() if p.is_file()
        },
        source_sha256={
            str(p.relative_to(ROOT)): digest(p)
            for p in (
                Path(__file__),
                ROOT / "src/react_agent/validation/guard_cancellation_audit_v1.py",
                ROOT / "scripts/audit_phase5_guard_gpu_release.py",
            )
        },
        test_access="hash-only prerequisites; no Test payload or private GT",
    )
    lines = [
        "# Guard cancellation / VRAM recovery v1",
        "",
        "Three fixed sequential workers on device1; two T4 allocated; no model generation.",
        "",
        "| Trial | ACK s (includes load) | Timeout s | Cleanup | "
        "Resident GiB | Last residual MiB |",
        "| --- | ---: | ---: | --- | ---: | ---: |",
    ]
    for row in result["measurements"]:
        timeout = row["busy_timeout_seconds"]
        timing = "—" if timeout is None else f"{timeout:.3f}"
        lines.append(
            f"| {row['trial']} | {row['ack_seconds']:.3f} | {timing} | "
            f"{row['cleanup']['method']}/{row['cleanup']['exitcode']} | "
            f"{row['resident_bytes'] / 1024**3:.3f} | "
            f"{row['residual_bytes'][-1] / 1024**2:.3f} |"
        )
    lines.extend(
        [
            "",
            "Resource recovery passed all predeclared gates; normal graceful close: "
            + str(result["normal_close_graceful"])
            + ".",
            "",
            "Six post-close samples per trial; last three within ±256 MiB of baseline. "
            "Full signed residuals, load metrics and lifecycle events are in the receipt.",
            "",
            result["limitations"],
            "",
            "The earlier SAFE-on-B classification miss remains unresolved. "
            "This does not establish combined agent/guard fit or accept Phase 5.",
        ]
    )
    args.output.mkdir(parents=True)
    write_json(args.output / "audit.json", result)
    with (args.output / "report.md").open("x") as stream:
        stream.write("\n".join(lines) + "\n")
    print("PASS: cancellation resource integrity; Phase 5 remains open")


if __name__ == "__main__":
    main()
