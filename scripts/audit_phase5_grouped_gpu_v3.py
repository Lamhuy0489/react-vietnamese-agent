"""Read-only remote source/bootstrap authentication and joined grouped native audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.grouped_dev_identity_v2 import identity
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.context_stress_audit_v1 import equal
from react_agent.validation.grouped_dev_native_audit_v2 import audit as native_audit
from react_agent.validation.guard_probe_audit_v2 import digest, require

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
IMAGE = (
    "gcr.io/kaggle-private-byod/python@sha256:"
    "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
)
DATASET = "huylmhuhu/react-vn-guard15-probe-data-v1"
MODEL = "qwen-lm/qwen2.5/transformers/7b-instruct/1"


def remote_identity(
    remote: Path, preflight: dict[str, Any], submission: dict[str, Any]
) -> dict[str, Any]:
    before = inventory(remote)
    metadata = json.loads((remote / "kernel-metadata.json").read_text())
    code = metadata.get("code_file")
    require(type(code) is str and Path(code).name == code, "remote code basename")
    equal(sorted(before), sorted([code, "kernel-metadata.json"]), "exact remote inventory")
    shard = submission["shard"]
    require(type(shard) is int and 0 <= shard < 8, "known shard")
    kernel = preflight["kernels"][shard]
    equal(kernel["shard"], shard, "kernel shard")
    equal(
        digest(remote / code), kernel["files"]["grouped_native_kernel_v3.py"], "remote wrapper hash"
    )
    for name, expected in {
        "id": submission["actual_kernel"],
        "id_no": submission["kernel_id"],
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "machine_shape": "NvidiaTeslaT4",
        "docker_image": IMAGE,
        "dataset_sources": [DATASET],
        "kernel_sources": [],
        "competition_sources": [],
        "language": "python",
        "kernel_type": "script",
    }.items():
        equal(metadata.get(name), expected, "remote metadata " + name)
    sources = metadata.get("model_sources")
    require(
        isinstance(sources, list) and all(isinstance(s, str) for s in sources), "model mount list"
    )
    equal([s.lower() for s in sources], [MODEL], "pinned model mount")
    equal(inventory(remote), before, "remote inputs unchanged")
    return dict(metadata=metadata, sha256=before)


def authenticate(
    raw: Path, remote: Path, preflight_path: Path, submission_path: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Never execute downloaded code or trust a worker's success boolean."""
    for path in (raw, remote, preflight_path, submission_path, BUNDLE):
        no_links(path)
    preflight = json.loads(preflight_path.read_text())
    submission = json.loads(submission_path.read_text())
    require(submission["submission_confirmed"] is True, "confirmed submission")
    equal(digest(preflight_path), submission["preflight_sha256"], "submission preflight pin")
    equal(preflight["protocol"], "grouped_package_v3_preflight", "preflight protocol")
    require(
        preflight["valid"] is True and preflight["package_rehearsal_passed"] is True,
        "exact package rehearsal",
    )
    equal(submission["source_commit"], preflight["source_commit"], "source commit")
    equal(digest(BUNDLE), preflight["bundle_manifest_sha256"], "bundle manifest")
    bundle = json.loads(BUNDLE.read_text())
    equal(bundle["dataset"], DATASET, "bundle dataset")
    for name, expected in preflight["source_sha256"].items():
        no_links(ROOT / name)
        require((ROOT / name).resolve().is_relative_to(ROOT), "contained source")
        equal(digest(ROOT / name), expected, "frozen source " + name)
    remote_info = remote_identity(remote, preflight, submission)
    bootstrap = json.loads((raw / "grouped_bootstrap.json").read_text())
    equal(
        bootstrap,
        dict(
            protocol="grouped_native_package_v3",
            source_commit=preflight["source_commit"],
            source_sha256=preflight["package_sha256"],
            source_archive_sha256=preflight["archive_sha256"],
            shard=submission["shard"],
            bundle_manifest_sha256=preflight["bundle_manifest_sha256"],
            snapshot=bundle["snapshot"],
            wheel_sha256=bundle["wheel_sha256"],
            phase5_accepted=False,
        ),
        "exact bootstrap identity",
    )
    return preflight, submission, remote_info


def audit(raw: Path, remote: Path, preflight_path: Path, submission_path: Path) -> dict[str, Any]:
    """A complete shard is required; retain partial/error outputs for separate diagnosis."""
    before = inventory(raw)
    preflight, submission, remote_info = authenticate(raw, remote, preflight_path, submission_path)
    bundle = json.loads(BUNDLE.read_text())
    snapshot = GuardSnapshot.model_validate(bundle["snapshot"])
    manifest, _ = identity(
        ROOT / "data/adversarial/release_v2",
        ROOT / "data/clean/v1_1/environment",
        preflight["source_commit"],
        "hf",
        ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json",
        snapshot,
    )
    args = (
        raw / "grouped",
        manifest,
        submission["shard"],
        raw / "tokenizers",
        ROOT / "docs/evaluation/publisher_policy_v1",
        snapshot,
    )
    joined = native_audit(*args)
    require(joined["complete"] is True and joined["completed"] == 14, "complete native shard")
    equal(native_audit(*args), joined, "independent repeat audit")
    equal(json.loads((raw / "native_audit.json").read_text()), joined, "remote joined audit")
    require(
        (raw / "native_audit.json").read_bytes()
        == (json.dumps(joined, indent=2, sort_keys=True) + "\n").encode(),
        "canonical native audit bytes",
    )
    log_name = submission["actual_kernel"].split("/")[-1] + ".log"
    expected = {"grouped_bootstrap.json", "native_audit.json", log_name}
    expected.update("grouped/" + name for name in joined["raw_sha256"])
    tokenizers = inventory(raw / "tokenizers")
    equal(
        sorted(tokenizers),
        sorted(["agent_tokenizer_config.json", "guard_tokenizer_config.json"]),
        "exact tokenizer evidence",
    )
    expected.update("tokenizers/" + name for name in tokenizers)
    equal(sorted(before), sorted(expected), "exact complete output inventory")
    equal(inventory(raw), before, "raw unchanged")
    equal(inventory(remote), remote_info["sha256"], "remote unchanged")
    return dict(
        protocol="grouped_gpu_v3_release_audit",
        artifact_integrity_valid=True,
        remote_source_authenticated=True,
        joined_audit_byte_identical=True,
        source_commit=preflight["source_commit"],
        shard=submission["shard"],
        actual_kernel=submission["actual_kernel"],
        kernel_version=submission["kernel_version"],
        preflight_sha256=digest(preflight_path),
        submission_sha256=digest(submission_path),
        auditor_sha256=digest(Path(__file__)),
        raw_sha256=before,
        remote=remote_info,
        completed=14,
        expected=14,
        tasks=joined["tasks"],
        phase5_accepted=False,
        guard_quality_validated=False,
        quality_scoring=False,
        scope="One complete native public Dev shard, failures retained. Source and runtime "
        "integrity are not semantic utility, ASR/FPR, or full Phase 5 acceptance.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "remote", "preflight", "submission", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    protected = (args.raw, args.remote, args.preflight, args.submission, ROOT / "data")
    require(
        not args.output.exists()
        and all(
            not args.output.resolve().is_relative_to(p.resolve())
            and not p.resolve().is_relative_to(args.output.resolve())
            for p in protected
        ),
        "fresh independent output outside frozen inputs",
    )
    result = audit(args.raw, args.remote, args.preflight, args.submission)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("GROUPED_GPU_V3_RELEASE_AUDIT_OK phase5_accepted=False")


if __name__ == "__main__":
    main()
