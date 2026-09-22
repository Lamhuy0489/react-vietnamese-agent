"""Read-only committed-package and downloaded constrained GPU release authentication."""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import re
import subprocess
import tarfile
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.clause_dev_dispatch_v1 import release_identity
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.clause_dev_native_audit_v1 import audit as audit_shard
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.exit_pair_audit_v1 import checked_runtime
from react_agent.validation.guard_probe_audit_v2 import require

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
CODE = "clause_dev32_kernel_v1.py"


def digest(path: Path) -> str:
    no_links(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contained(root: Path, name: str) -> Path:
    require(isinstance(name, str) and bool(name), "relative path required")
    relative = Path(name)
    require(not relative.is_absolute() and ".." not in relative.parts, "relative path required")
    path = root / relative
    no_links(path)
    require(path.resolve().is_relative_to(root.resolve()), "contained path required")
    return path


def git_digest(commit: str, name: str) -> str:
    raw = subprocess.check_output(  # noqa: S603 - fixed Git command, validated commit/path
        ["git", "show", f"{commit}:{name}"],  # noqa: S607
        cwd=ROOT,
    )
    return hashlib.sha256(raw).hexdigest()


def constants(path: Path) -> dict[str, Any]:
    wanted = {
        "SOURCE_COMMIT",
        "SOURCE_MODE",
        "SOURCE_FILES",
        "ARCHIVE",
        "ARCHIVE_SHA",
        "BASE_SOURCE",
        "BASE_SHA",
        "BUNDLE_SHA",
    }
    values = {}
    for node in ast.parse(path.read_text()).body:
        value: ast.expr | None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        else:
            continue
        if isinstance(target, ast.Name) and target.id in wanted:
            if target.id in values or value is None:
                raise ValueError("unique launcher literal required")
            values[target.id] = ast.literal_eval(value)
    equal(sorted(values), sorted(wanted), "launcher constants")
    return values


def validate_package(preflight_path: Path) -> dict[str, Any]:
    """Also usable before upload; does not claim remote admission or native execution."""
    no_links(preflight_path)
    selected = read_record(preflight_path)
    require(
        selected["valid"] is True and selected["native_submission_ready"] is True,
        "accepted release preflight",
    )
    equal(selected["source_mode"], "committed", "committed source mode")
    commit = selected["source_commit"]
    require(
        isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) is not None,
        "frozen commit",
    )
    package = contained(ROOT, selected["package_path"])
    require(package.resolve().is_relative_to(ROOT / "build/kaggle"), "contained package")
    full_path = package / "preflight_receipt.json"
    equal(digest(full_path), selected["original_receipt_sha256"], "full receipt pin")
    full = read_record(full_path)
    for key in (
        "protocol",
        "valid",
        "source_mode",
        "source_commit",
        "source_sha256",
        "package_sha256",
        "archive_sha256",
        "dataset_manifest_sha256",
        "kernel_sha256",
        "native_submission_ready",
        "requested_notebook",
    ):
        equal(selected[key], full[key], "selected/full " + key)
    equal(full["protocol"], "clause_dev32_package_v1_cpu", "package protocol")
    require(bool(full["source_sha256"]) and bool(full["package_sha256"]), "nonempty source pins")
    for name, expected in full["source_sha256"].items():
        equal(digest(contained(ROOT, name)), expected, "local source bytes")
        equal(git_digest(commit, name), expected, "committed source bytes")
    for name, expected in full["package_sha256"].items():
        equal(full["source_sha256"].get(name), expected, "package source closure")
    archive = package / "source.tar.gz"
    equal(digest(archive), full["archive_sha256"], "source archive")
    with tarfile.open(archive, "r:gz") as stream:
        files = {}
        for member in stream.getmembers():
            contained(ROOT, member.name)
            require(member.isfile() and member.name not in files, "unique regular archive files")
            content = stream.extractfile(member)
            if content is None:
                raise ValueError("readable archive member required")
            files[member.name] = hashlib.sha256(content.read()).hexdigest()
        equal(files, full["package_sha256"], "archive inventory")
    equal(inventory(package / "kernel"), full["kernel_sha256"], "kernel inventory")
    # Frozen rehearsal imported the launcher once, retaining this local-only cache.
    # Hash it without executing it; Kaggle source pull must still contain exactly two files.
    required = {CODE, "kernel-metadata.json"}
    permitted = required | {"__pycache__/clause_dev32_kernel_v1.cpython-311.pyc"}
    require(required <= set(full["kernel_sha256"]) <= permitted, "kernel files")
    metadata = read_record(package / "kernel/kernel-metadata.json")
    for key, value in {
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "code_file": CODE,
    }.items():
        equal(metadata[key], value, "release settings " + key)
    equal(metadata["id"], selected["requested_notebook"], "requested handle")
    embedded = constants(package / "kernel" / CODE)
    for key, expected in {
        "SOURCE_COMMIT": commit,
        "SOURCE_MODE": "committed",
        "SOURCE_FILES": files,
        "ARCHIVE_SHA": full["archive_sha256"],
        "BUNDLE_SHA": full["dataset_manifest_sha256"],
    }.items():
        equal(embedded[key], expected, "embedded " + key)
    for key, expected in (
        ("ARCHIVE", full["archive_sha256"]),
        ("BASE_SOURCE", embedded["BASE_SHA"]),
    ):
        equal(
            hashlib.sha256(base64.b64decode(embedded[key], validate=True)).hexdigest(),
            expected,
            "embedded bytes " + key,
        )
    equal(
        embedded["BASE_SHA"],
        full["source_sha256"].get("notebooks/kaggle/guard_cancellation_kernel_v1.py"),
        "bootstrap committed source",
    )
    equal(digest(BUNDLE), full["dataset_manifest_sha256"], "Dataset manifest")
    source_manifest = read_record(package / "source_manifest.json")
    equal(
        source_manifest,
        dict(
            protocol="clause_dev32_source_v1",
            source_mode="committed",
            source_commit=commit,
            git_base_commit=commit,
            source_sha256=files,
            archive_sha256=full["archive_sha256"],
        ),
        "source admission manifest",
    )
    template = "notebooks/kaggle/clause_dev32_kernel_v1.py"
    rendered = contained(ROOT, template).read_text()
    replacements = {
        "__SOURCE_COMMIT__": commit,
        "__SOURCE_MODE__": "committed",
        "__BASE_SOURCE__": embedded["BASE_SOURCE"],
        "__BASE_SHA__": embedded["BASE_SHA"],
        "__ARCHIVE__": embedded["ARCHIVE"],
        "__ARCHIVE_SHA__": embedded["ARCHIVE_SHA"],
        "__BUNDLE_SHA__": embedded["BUNDLE_SHA"],
        "{}  # __SOURCE_FILES__": repr(files),
    }
    # Archive inventory follows sorted source paths; compare canonical rendering.
    replacements["{}  # __SOURCE_FILES__"] = repr(dict(sorted(files.items())))
    for marker, replacement in replacements.items():
        equal(rendered.count(marker), 1, "unique source placeholder")
        rendered = rendered.replace(marker, replacement)
    equal((package / "kernel" / CODE).read_text(), rendered, "committed launcher body")
    equal(len(full["checks"]), 2, "both mount layouts")
    equal([v["layout"] for v in full["checks"]], ["archive", "expanded"], "layout order")
    for check in full["checks"]:
        equal(check["valid"], True, "valid rehearsal")
        equal(check["tools"], 8, "tool coverage")
        equal(check["clean_dummy_tasks"], 21, "clean coverage")
        equal(check["dev32"]["runtime_tasks"], 32, "Dev32 coverage")
        for field in ("valid", "missing_only_resume", "complete_resume", "source_bytes_verified"):
            equal(check["dev32"][field], True, "Dev32 " + field)
    return selected


def native_audit(
    probe: Path,
    tokenizers: Path,
    publishers: Path,
    pin: GuardSnapshot,
    commit: str,
    model_inventory: Path,
    environment: Path,
) -> dict[str, Any]:
    before = inventory(probe)
    equal(sorted(p.name for p in probe.iterdir()), [f"shard{i}" for i in range(8)], "all shards")
    release = read_record(probe.parent / "source_manifest.json")
    rows = []
    for shard in range(8):
        root = probe / f"shard{shard}"
        saved = read_record(root / "identity.json")["run"]
        manifest, _ = release_identity(
            ROOT / "data/adversarial/release_v2",
            environment,
            commit,
            "hf",
            model_inventory,
            pin,
            release=release,
        )
        manifest["exit_observer"]["runtime"] = checked_runtime(saved["exit_observer"]["runtime"])
        value = audit_shard(root, manifest, shard, tokenizers, publishers, pin)
        equal(value["complete"], True, "complete native shard")
        expected = {
            **value,
            "source_bytes_verified": True,
            "remote_release_authenticated": False,
            "phase5_accepted": False,
        }
        equal(
            read_record(probe.parent / "native_audits" / f"shard{shard}.json"),
            expected,
            "independent native audit",
        )
        rows.append(value)
    equal(inventory(probe), before, "native raw unchanged")
    return dict(
        protocol="clause_dev32_native_all_v1",
        completed=sum(r["completed"] for r in rows),
        expected=32,
        shards=rows,
        quality_scored=False,
        phase5_accepted=False,
    )


def audit(
    raw: Path, remote: Path, preflight_path: Path, submission_path: Path, observation_path: Path
) -> dict[str, Any]:
    for path in (raw, remote, preflight_path, submission_path, observation_path):
        no_links(path)
    before, remote_before = inventory(raw), inventory(remote)
    selected = validate_package(preflight_path)
    submission, observation = read_record(submission_path), read_record(observation_path)
    require(submission["submission_confirmed"] is True, "confirmed submission")
    equal(digest(preflight_path), submission["preflight_sha256"], "preflight pin")
    equal(digest(submission_path), observation["submission_sha256"], "submission pin")
    equal(submission["source_commit"], selected["source_commit"], "submitted commit")
    equal(submission["actual_kernel"], selected["requested_notebook"], "actual handle")
    equal(
        submission["notebook_url"],
        "https://www.kaggle.com/code/" + submission["actual_kernel"],
        "notebook URL",
    )
    for key in ("kernel_id", "kernel_version"):
        require(type(submission[key]) is int and submission[key] > 0, "positive " + key)
    for observed in (observation["before_download"], observation):
        for key in ("kernel_id", "kernel_version", "actual_kernel", "remote_source_sha256"):
            equal(observed[key], submission[key], "download identity " + key)
        equal(observed["private"], True, "private notebook")
        equal(observed["session_status"]["status"], "COMPLETE", "terminal COMPLETE required")
    equal(submission["private"], True, "private submission")
    equal(observation["raw_sha256"], before, "downloaded raw inventory")
    equal(observation["remote_sha256"], remote_before, "downloaded remote inventory")
    package = contained(ROOT, selected["package_path"])
    metadata = read_record(remote / "kernel-metadata.json")
    local = read_record(package / "kernel/kernel-metadata.json")
    code = metadata["code_file"]
    require(isinstance(code, str) and Path(code).name == code, "code basename")
    equal(sorted(remote_before), sorted([code, "kernel-metadata.json"]), "exact remote files")
    executable = digest(remote / code)
    equal(executable, selected["kernel_sha256"][CODE], "remote executable")
    equal(executable, submission["remote_source_sha256"], "submitted executable")
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
        equal(metadata[key], local[key], "remote metadata " + key)
    equal(metadata["id_no"], submission["kernel_id"], "remote numeric id")
    equal(
        [v.lower() for v in metadata["model_sources"]],
        [v.lower() for v in local["model_sources"]],
        "model mounts",
    )
    bundle = read_record(BUNDLE)
    equal(submission["dataset"], bundle["dataset"], "Dataset handle")
    equal(submission["dataset_version"], 1, "frozen Dataset version")
    equal(
        read_record(raw / "observer_bootstrap.json"),
        dict(
            protocol="clause_dev32_package_v1",
            source_mode="committed",
            source_commit=selected["source_commit"],
            source_sha256=selected["package_sha256"],
            source_archive_sha256=selected["archive_sha256"],
            bundle_manifest_sha256=selected["dataset_manifest_sha256"],
            snapshot=bundle["snapshot"],
            wheel_sha256=bundle["wheel_sha256"],
            phase5_accepted=False,
        ),
        "bootstrap binding",
    )
    equal(
        read_record(raw / "source_manifest.json"),
        read_record(package / "source_manifest.json"),
        "source record",
    )
    result = native_audit(
        raw / "dev32",
        raw / "tokenizers",
        ROOT / "docs/evaluation/publisher_policy_v1",
        GuardSnapshot.model_validate(bundle["snapshot"]),
        selected["source_commit"],
        ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json",
        ROOT / "data/clean/v1_1/environment",
    )
    equal(result["protocol"], "clause_dev32_native_all_v1", "native protocol")
    equal(inventory(raw), before, "raw unchanged")
    equal(inventory(remote), remote_before, "remote unchanged")
    return dict(
        protocol="clause_dev32_gpu_release_audit_v1",
        valid=True,
        source_authenticated=True,
        source_commit=selected["source_commit"],
        native=result,
        raw_sha256=before,
        remote_sha256=remote_before,
        preflight_sha256=digest(preflight_path),
        submission_sha256=digest(submission_path),
        observation_sha256=digest(observation_path),
        source_pins_verified=len(selected["source_sha256"]),
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
    target = args.output.resolve()
    require(
        target.is_relative_to(ROOT / "results") and target != ROOT / "results",
        "audit output must be under results",
    )
    protected = (args.raw, args.remote, args.preflight, args.submission, args.observation)
    require(
        not target.exists()
        and not any(
            target.is_relative_to(p.resolve()) or p.resolve().is_relative_to(target)
            for p in protected
        ),
        "fresh output outside inputs",
    )
    write_receipt(args.output, audit(*protected))
    print("CLAUSE_DEV32_GPU_RELEASE_AUDIT_COMPLETE")


if __name__ == "__main__":
    main()
