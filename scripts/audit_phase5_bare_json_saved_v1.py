"""Recover the completed candidate inference audit after its final CLI invocation failed."""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path
from typing import Any

from report_phase5_observer_gpu_v2 import summarize

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.context_stress_audit_v1 import equal
from react_agent.validation.guard_bare_json_native_audit_v1 import audit as native_audit

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "f7492fae80876891237fcd37084e79ed5af60a2e"
HANDLE = "huylmhuhu/react-vn-guard-bare-json-v1"
PREFLIGHT = "experiments/manifests/phase5_guard_bare_json_package_v1_preflight01.json"
SUBMISSION = "experiments/manifests/phase5_guard_bare_json_submission01.json"
# These entrypoints are never executed during recovery. All package src/ bytes
# and other source pins must remain identical locally for the reused audit code.
HISTORICAL_ONLY = {
    "scripts/audit_phase5_guard_bare_json_probe_v1.py",
    "scripts/prepare_phase5_guard_bare_json_package_v1.py",
}


def digest(path: Path) -> str:
    no_links(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def launcher_constants(path: Path) -> dict[str, Any]:
    """Inspect literals without executing remote Python."""
    values = {}
    for node in ast.parse(path.read_text()).body:
        value: ast.expr | None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        else:
            continue
        if isinstance(target, ast.Name) and target.id in {
            "SOURCE_COMMIT",
            "ARCHIVE",
            "ARCHIVE_SHA",
            "BUNDLE_SHA",
            "SOURCE_FILES",
        }:
            if target.id in values or value is None:
                raise ValueError("duplicate or missing launcher constant")
            values[target.id] = ast.literal_eval(value)
    return values


def audit(raw: Path, remote: Path, observation_path: Path) -> dict[str, Any]:
    for path in (raw, remote, observation_path):
        no_links(path)
    before, remote_before = inventory(raw), inventory(remote)
    prepath, subpath = ROOT / PREFLIGHT, ROOT / SUBMISSION
    selected, sub = json.loads(prepath.read_text()), json.loads(subpath.read_text())
    observation = json.loads(observation_path.read_text())
    equal(sub["submission_confirmed"], True, "confirmed submission")
    equal(digest(prepath), sub["preflight_sha256"], "preflight pin")
    equal(digest(subpath), observation["submission_sha256"], "submission pin")
    for obj in (sub, observation):
        equal(obj["actual_kernel"], HANDLE, "actual handle")
        equal(obj["kernel_version"], 1, "kernel version")
        equal(obj["kernel_id"], 134511636, "kernel id")
        equal(obj["private"], True, "private notebook")
    equal(observation["session_status"]["status"], "ERROR", "retained terminal failure")
    equal(observation["remote_sha256"], remote_before, "remote inventory")
    equal(selected["source_commit"], COMMIT, "fixed source commit")
    equal(sub["source_commit"], COMMIT, "submitted source commit")
    package = ROOT / selected["package_path"]
    no_links(package)
    if not package.resolve().is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("contained package required")
    fullpath = package / "preflight_receipt.json"
    equal(digest(fullpath), selected["full_receipt_sha256"], "full preflight pin")
    full = json.loads(fullpath.read_text())
    equal(selected["source_sha256"], full["source_sha256"], "source inventory")
    equal(selected["package_sha256"], full["package_sha256"], "package inventory")
    historical = []
    for name, expected in selected["source_sha256"].items():
        path = ROOT / name
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("contained source required")
        original = subprocess.check_output(  # noqa: S603 - validated Git object and source path
            ["git", "show", f"{COMMIT}:{name}"],  # noqa: S607
            cwd=ROOT,
        )
        equal(hashlib.sha256(original).hexdigest(), expected, "committed source")
        if name in HISTORICAL_ONLY:
            historical.append(name)
        else:
            equal(digest(path), expected, "local audited dependency")
    archive = package / "source.tar.gz"
    equal(digest(archive), selected["archive_sha256"], "archive hash")
    with tarfile.open(archive, "r:gz") as bundle:
        files = {}
        for member in bundle.getmembers():
            if not member.isfile() or member.name in files:
                raise ValueError("exact regular archive files required")
            stream = bundle.extractfile(member)
            if stream is None:
                raise ValueError("archive member unreadable")
            files[member.name] = hashlib.sha256(stream.read()).hexdigest()
        equal(files, full["package_sha256"], "archive file inventory")
    meta = json.loads((remote / "kernel-metadata.json").read_text())
    code = meta["code_file"]
    if not isinstance(code, str) or Path(code).name != code:
        raise ValueError("code basename required")
    equal(sorted(remote_before), sorted([code, "kernel-metadata.json"]), "remote files")
    equal(digest(remote / code), sub["remote_source_sha256"], "submitted executable")
    equal(digest(remote / code), observation["remote_source_sha256"], "observed executable")
    equal(
        digest(remote / code),
        selected["kernel_sha256"]["guard_bare_json_kernel_v1.py"],
        "preflight executable",
    )
    localmeta = package / "kernel/kernel-metadata.json"
    equal(digest(localmeta), selected["kernel_sha256"]["kernel-metadata.json"], "metadata pin")
    local = json.loads(localmeta.read_text())
    for key in (
        "id",
        "is_private",
        "enable_gpu",
        "enable_tpu",
        "enable_internet",
        "machine_shape",
        "docker_image",
        "dataset_sources",
        "kernel_sources",
        "competition_sources",
        "language",
        "kernel_type",
    ):
        equal(meta[key], local[key], "metadata binding")
    equal(meta["id_no"], observation["kernel_id"], "metadata kernel id")
    equal(
        [v.lower() for v in meta["model_sources"]],
        [v.lower() for v in local["model_sources"]],
        "model mounts",
    )
    constants = launcher_constants(remote / code)
    equal(constants["SOURCE_COMMIT"], COMMIT, "embedded commit")
    equal(constants["SOURCE_FILES"], files, "embedded source inventory")
    equal(constants["ARCHIVE_SHA"], digest(archive), "embedded archive pin")
    equal(
        hashlib.sha256(base64.b64decode(constants["ARCHIVE"], validate=True)).hexdigest(),
        digest(archive),
        "embedded archive bytes",
    )
    manifest = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
    equal(digest(manifest), full["dataset_manifest_sha256"], "Dataset manifest")
    equal(constants["BUNDLE_SHA"], digest(manifest), "embedded Dataset pin")
    bundle_data = json.loads(manifest.read_text())
    equal(
        json.loads((raw / "observer_bootstrap.json").read_text()),
        dict(
            protocol="guard_bare_json_package_v1",
            source_commit=COMMIT,
            source_sha256=files,
            source_archive_sha256=digest(archive),
            bundle_manifest_sha256=digest(manifest),
            snapshot=bundle_data["snapshot"],
            wheel_sha256=bundle_data["wheel_sha256"],
            phase5_accepted=False,
        ),
        "bootstrap binding",
    )
    log = (raw / "react-vn-guard-bare-json-v1.log").read_text()
    if "the following arguments are required: --condition" not in log:
        raise ValueError("documented post-inference CLI failure required")
    if (raw / "native_audit.json").exists():
        raise ValueError("unexpected successful worker audit")
    native = native_audit(
        raw / "observer",
        raw / "tokenizers",
        ROOT / "docs/evaluation/publisher_policy_v1",
        GuardSnapshot.model_validate(bundle_data["snapshot"]),
        COMMIT,
        ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json",
        ROOT / "data/clean/v1_1/environment",
    )
    equal(inventory(raw), before, "raw unchanged")
    equal(inventory(remote), remote_before, "remote unchanged")
    return dict(
        protocol="bare_json_saved_inference_release_v1",
        valid=True,
        source_authenticated=True,
        source_commit=COMMIT,
        kernel_status="ERROR",
        recovered_audit_only=True,
        new_inference_runs=0,
        native=native,
        raw_sha256=before,
        remote_sha256=remote_before,
        observation_sha256=digest(observation_path),
        historical_only_sources=historical,
        source_pins_verified=len(selected["source_sha256"]),
        notebook_url=sub["notebook_url"],
        kernel_version=1,
        phase5_accepted=False,
        guard_quality_validated=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "remote", "observation", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    if args.output.exists() or any(
        args.output.resolve().is_relative_to(p.resolve())
        or p.resolve().is_relative_to(args.output.resolve())
        for p in (args.raw, args.remote, args.observation, ROOT / "data")
    ):
        raise ValueError("fresh output outside inputs required")
    verified = audit(args.raw, args.remote, args.observation)
    summary = summarize(verified, args.raw)
    args.output.mkdir(parents=True)
    write_receipt(args.output / "audit.json", verified)
    write_receipt(args.output / "summary.json", summary)
    print("SAVED_NATIVE_AUDIT_COMPLETE")


if __name__ == "__main__":
    main()
