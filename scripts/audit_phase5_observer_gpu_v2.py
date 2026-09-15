"""Authenticate downloaded observer version/source/bootstrap before native artifact audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.context_stress_audit_v1 import equal
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.observer_native_audit_v2 import audit as native_audit

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"


def digest(path: Path) -> str:
    no_links(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(
    raw: Path, remote: Path, preflight_path: Path, submission_path: Path, observation_path: Path
) -> dict[str, Any]:
    for path in (raw, remote, preflight_path, submission_path, observation_path):
        no_links(path)
    before, remote_before = inventory(raw), inventory(remote)
    selected = json.loads(preflight_path.read_text())
    submission = json.loads(submission_path.read_text())
    observation = json.loads(observation_path.read_text())
    require(
        selected["valid"] is True and selected["native_submission_ready"] is True,
        "accepted preflight",
    )
    require(submission["submission_confirmed"] is True, "confirmed submission")
    equal(digest(preflight_path), submission["preflight_sha256"], "preflight pin")
    equal(digest(submission_path), observation["submission_sha256"], "observation submission pin")
    equal(observation["kernel_version"], submission["kernel_version"], "remote version")
    equal(
        observation["session_status"]["status"],
        "COMPLETE",
        "terminal COMPLETE observation required",
    )
    equal(submission["source_commit"], selected["source_commit"], "source commit")
    equal(observation["actual_kernel"], submission["actual_kernel"], "observed handle")
    equal(observation["remote_sha256"], remote_before, "versioned remote evidence")
    package = ROOT / selected["package_path"]
    no_links(package)
    require(package.resolve().is_relative_to(ROOT / "build/kaggle"), "contained package")
    full_path = package / "preflight_receipt.json"
    equal(digest(full_path), selected["full_receipt_sha256"], "full preflight receipt")
    full = json.loads(full_path.read_text())
    for name, expected in selected["source_sha256"].items():
        path = ROOT / name
        require(path.resolve().is_relative_to(ROOT), "contained source")
        equal(digest(path), expected, "source bytes")
    metadata = json.loads((remote / "kernel-metadata.json").read_text())
    code = metadata["code_file"]
    require(isinstance(code, str) and Path(code).name == code, "code basename")
    equal(sorted(remote_before), sorted(["kernel-metadata.json", code]), "exact remote files")
    equal(
        digest(remote / code),
        selected["kernel_sha256"]["observer_native_kernel_v2.py"],
        "remote executable",
    )
    local_metadata = json.loads((package / "kernel/kernel-metadata.json").read_text())
    equal(
        digest(package / "kernel/kernel-metadata.json"),
        selected["kernel_sha256"]["kernel-metadata.json"],
        "local metadata pin",
    )
    for key in (
        "id",
        "is_private",
        "enable_gpu",
        "enable_tpu",
        "enable_internet",
        "machine_shape",
        "docker_image",
        "dataset_sources",
        "competition_sources",
        "kernel_sources",
        "language",
        "kernel_type",
    ):
        equal(metadata[key], local_metadata[key], "remote metadata")
    equal(metadata["id"], submission["actual_kernel"], "actual handle")
    equal(metadata["id_no"], observation["kernel_id"], "remote kernel id")
    equal(
        [s.lower() for s in metadata["model_sources"]],
        [s.lower() for s in local_metadata["model_sources"]],
        "model mount",
    )
    equal(digest(BUNDLE), full["dataset_manifest_sha256"], "Dataset manifest")
    bundle = json.loads(BUNDLE.read_text())
    bootstrap = json.loads((raw / "observer_bootstrap.json").read_text())
    equal(
        bootstrap,
        dict(
            protocol="observer_native_package_v2",
            source_commit=selected["source_commit"],
            source_sha256=full["package_sha256"],
            source_archive_sha256=selected["archive_sha256"],
            bundle_manifest_sha256=full["dataset_manifest_sha256"],
            snapshot=bundle["snapshot"],
            wheel_sha256=bundle["wheel_sha256"],
            phase5_accepted=False,
        ),
        "bootstrap pins",
    )
    result = native_audit(
        raw / "observer",
        raw / "tokenizers",
        ROOT / "docs/evaluation/publisher_policy_v1",
        GuardSnapshot.model_validate(bundle["snapshot"]),
        selected["source_commit"],
        ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json",
        ROOT / "data/clean/v1_1/environment",
    )
    equal(
        result, json.loads((raw / "native_audit.json").read_text()), "independent native re-audit"
    )
    equal(inventory(raw), before, "raw unchanged")
    equal(inventory(remote), remote_before, "remote unchanged")
    return dict(
        protocol="observer_gpu_release_audit_v2",
        valid=True,
        source_authenticated=True,
        source_commit=selected["source_commit"],
        native=result,
        raw_sha256=before,
        remote_sha256=remote_before,
        observation_sha256=digest(observation_path),
        notebook_url=submission["notebook_url"],
        kernel_version=submission["kernel_version"],
        phase5_accepted=False,
        guard_quality_validated=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "remote", "preflight", "submission", "observation", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    no_links(args.output)
    protected = (
        args.raw,
        args.remote,
        args.preflight,
        args.submission,
        args.observation,
        ROOT / "data",
    )
    if args.output.exists() or any(
        args.output.resolve().is_relative_to(p.resolve())
        or p.resolve().is_relative_to(args.output.resolve())
        for p in protected
    ):
        raise ValueError("fresh audit output outside inputs required")
    write_receipt(
        args.output, audit(args.raw, args.remote, args.preflight, args.submission, args.observation)
    )
    print("OBSERVER_GPU_RELEASE_AUDIT_COMPLETE")


if __name__ == "__main__":
    main()
