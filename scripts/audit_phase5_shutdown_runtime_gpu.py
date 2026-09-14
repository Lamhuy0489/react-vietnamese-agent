"""Authenticate downloaded runtime artifacts without inference or quality claims."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from audit_phase5_guard_gpu_release import audit_dummy
from audit_phase5_ordinary_pair_gpu import AGENT_HANDLE, BUNDLE, DATASET, IMAGE

from react_agent.foundation.dev_validation import prerequisites
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.security_runtime_probe_v2 import inventory
from react_agent.validation.context_stress_audit_v1 import equal
from react_agent.validation.guard_probe_audit_v2 import digest, require
from react_agent.validation.security_runtime_probe_audit_v2 import audit as native_audit

ROOT = Path(__file__).resolve().parents[1]
KERNEL_ID = "huylmhuhu/react-vn-security-runtime-v2"


def remote_identity(remote: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    """Authenticate bytes, private/offline settings, accelerator and exact mounts."""
    before = inventory(remote)
    metadata = json.loads((remote / "kernel-metadata.json").read_text())
    code = metadata.get("code_file")
    require(type(code) is str and Path(code).name == code, "remote code basename")
    equal(sorted(before), sorted([code, "kernel-metadata.json"]), "remote inventory")
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
        metadata.get("model_sources") in ([AGENT_HANDLE], [AGENT_HANDLE.lower()]),
        "exact agent model mount",
    )
    equal(inventory(remote), before, "remote unchanged")
    return {"metadata": metadata, "sha256": before}


def audit(raw: Path, remote: Path, preflight: Path) -> dict[str, Any]:
    """Completed artifact audit; execution/semantic failures are not retried."""
    no_links(preflight)
    before = inventory(raw)
    receipt = json.loads(preflight.read_text())
    bundle = json.loads(BUNDLE.read_text())
    equal(receipt["protocol"], "security_runtime_gpu_exact_preflight_v2", "preflight protocol")
    require(receipt["valid"] is True and receipt["phase5_accepted"] is False, "preflight scope")
    equal(digest(BUNDLE), receipt["bundle_manifest_sha256"], "frozen bundle")
    equal(bundle["dataset"], DATASET, "bundle dataset")
    equal(prerequisites(ROOT), receipt["prerequisites"], "frozen prerequisites")
    for name, expected_hash in receipt["source_sha256"].items():
        equal(digest(ROOT / name), expected_hash, "packaged source " + name)
    bootstrap = json.loads((raw / "security_runtime_bootstrap_identity.json").read_text())
    equal(
        bootstrap,
        {
            "protocol": "security_runtime_bootstrap_v2",
            "source_commit": receipt["source_commit"],
            "runtime_commit": receipt["runtime_commit"],
            "base_source_sha256": receipt["base_source_sha256"],
            "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
            "overlay_sha256": receipt["overlay_sha256"],
            "snapshot": bundle["snapshot"],
            "wheel_sha256": bundle["wheel_sha256"],
        },
        "bootstrap identity",
    )
    remote_info = remote_identity(remote, receipt)
    dummy = audit_dummy(raw, bundle)
    args = (
        raw / "security_runtime",
        raw / "tokenizers",
        raw / "publishers",
        GuardSnapshot.model_validate(bundle["snapshot"]),
        receipt["source_commit"],
    )
    joined = native_audit(*args)
    equal(native_audit(*args), joined, "repeat joined audit")
    remote_audit = raw / "security_runtime_native_audit.json"
    equal(json.loads(remote_audit.read_text()), joined, "remote joined audit")
    require(
        remote_audit.read_bytes() == (json.dumps(joined, indent=2, sort_keys=True) + "\n").encode(),
        "canonical remote audit bytes",
    )
    log_name = KERNEL_ID.rsplit("/", 1)[1] + ".log"
    require(
        "SECURITY_RUNTIME_GPU_V2_COMPLETE" in (raw / log_name).read_text(),
        "completion marker",
    )
    expected = {"security_runtime_bootstrap_identity.json", remote_audit.name, log_name}
    expected.update("dummy/" + name for name in ("identity.json", "results.json", "summary.json"))
    ids = json.loads((raw / "dummy/identity.json").read_text())["task_ids"]
    expected.update(
        f"dummy/tasks/{task}/{name}" for task in ids for name in ("result.json", "trace.jsonl")
    )
    for section, prefix in {
        "probe": "security_runtime",
        "tokenizers": "tokenizers",
        "publishers": "publishers",
    }.items():
        expected.update(prefix + "/" + name for name in joined["raw_sha256"][section])
    equal(sorted(before), sorted(expected), "complete raw inventory")
    equal(inventory(raw), before, "raw unchanged")
    equal(inventory(remote), remote_info["sha256"], "remote unchanged during audit")
    return {
        "protocol": "security_runtime_gpu_release_audit_v2",
        "artifact_integrity_valid": True,
        "remote_source_authenticated": True,
        "joined_audit_byte_identical": True,
        "phase5_accepted": False,
        "guard_quality_validated": False,
        "source_commit": receipt["source_commit"],
        "preflight_sha256": digest(preflight),
        "audit_script_sha256": digest(Path(__file__)),
        "raw_sha256": before,
        "remote": remote_info,
        "dummy": dummy,
        "levels": joined["levels"],
        "scope": "One public synthetic task per level. Artifact integrity is not semantic "
        "success, guard quality, graceful cleanup or Phase 5 acceptance. Partial roles remain "
        "unassessed. Equal configured agent deadlines do not establish controlled latency ranking.",
        "test_access": "hash-only prerequisites; no held-out payload or private ground truth",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "remote", "preflight", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    require(
        not args.output.exists()
        and not args.output.resolve().is_relative_to(args.raw.resolve())
        and not args.output.resolve().is_relative_to(args.remote.resolve()),
        "fresh independent audit output",
    )
    result = audit(args.raw, args.remote, args.preflight)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_receipt(args.output, result)
    print("SECURITY_RUNTIME_GPU_RELEASE_AUDIT_COMPLETE phase5_accepted=False")


if __name__ == "__main__":
    main()
