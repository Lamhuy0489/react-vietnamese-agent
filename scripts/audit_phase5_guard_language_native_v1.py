"""Authenticate saved CPU compatibility artifacts; never execute downloaded code."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import zipfile
from pathlib import Path
from typing import Any

from audit_phase5_bare_json_saved_v1 import launcher_constants

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.guard_language_native_v1 import BUNDLE_SHA, CASES, FILES, digest
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.context_stress_audit_v1 import equal

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = "experiments/manifests/phase5_guard_language_cpu_submission01.json"


def native_summary(summary: dict[str, Any], commit: str, processor_sha: str) -> None:
    expected = dict(
        protocol="guard_language_native_cpu_v1",
        valid=True,
        library_verified=True,
        source_commit=commit,
        torch="2.10.0+cu128",
        transformers="5.5.0",
        tokenizers="0.22.2",
        processor_source_sha256=processor_sha,
        documents=3069,
        case_indices=list(CASES),
        conflicting_processor_can_override=True,
        failures_propagated=["ValueError", "ValueError", "KeyboardInterrupt"],
        torch_threads_restored=True,
        model_generate_calls=0,
        model_weights_loaded=0,
        gpu_used=False,
        native_generation_validated=False,
        guard_quality_validated=False,
        phase5_accepted=False,
        test_payload_accessed=False,
        private_ground_truth_accessed=False,
    )
    numeric = {
        "native_mask_checks",
        "max_response_tokens_with_eos",
        "compilation_seconds",
        "mask_seconds",
    }
    equal(
        sorted(summary), sorted(set(expected) | numeric | {"language_identity"}), "summary fields"
    )
    for key, value in expected.items():
        equal(summary[key], value, "native summary " + key)
        if type(summary[key]) is not type(value):
            raise ValueError("strict summary type required")
    identity = summary["language_identity"]
    if (
        not isinstance(identity, str)
        or len(identity) != 64
        or any(c not in "0123456789abcdef" for c in identity)
    ):
        raise ValueError("language hash required")
    for key in ("native_mask_checks", "max_response_tokens_with_eos"):
        if type(summary[key]) is not int:
            raise ValueError("integer mask/token count required")
    if not 2 <= summary["max_response_tokens_with_eos"] <= 128 or not (
        len(CASES)
        <= summary["native_mask_checks"]
        <= len(CASES) * summary["max_response_tokens_with_eos"]
    ):
        raise ValueError("bounded mask/token count required")
    for key in ("compilation_seconds", "mask_seconds"):
        if (
            type(summary[key]) not in (float, int)
            or not math.isfinite(summary[key])
            or summary[key] < 0
        ):
            raise ValueError("finite nonnegative timing required")


def audit(raw: Path, remote: Path, observation_path: Path) -> dict[str, Any]:
    before, remotes = inventory(raw), inventory(remote)
    observation = json.loads(observation_path.read_text())
    sub = json.loads((ROOT / SUBMISSION).read_text())
    equal(digest(ROOT / SUBMISSION), observation["submission_sha256"], "submission hash")
    equal(observation["session_status"]["status"], "COMPLETE", "CPU terminal")
    for key in ("actual_kernel", "kernel_version", "kernel_id", "private", "remote_source_sha256"):
        equal(observation[key], sub[key], "live identity")
    equal(sub["kernel_version"], 1, "version")
    prepath = ROOT / sub["preflight_path"]
    equal(digest(prepath), sub["preflight_sha256"], "selected preflight")
    pre = json.loads(prepath.read_text())
    package = ROOT / pre["package_path"]
    equal(digest(package / "preflight_receipt.json"), pre["full_receipt_sha256"], "full preflight")
    equal(pre["source_commit"], sub["source_commit"], "source commit")
    for name, sha in pre["source_sha256"].items():
        equal(digest(ROOT / name), sha, "local source pin")
    meta = json.loads((remote / "kernel-metadata.json").read_text())
    localmeta = json.loads((package / "kernel/kernel-metadata.json").read_text())
    for key in (
        "id",
        "is_private",
        "enable_gpu",
        "enable_tpu",
        "enable_internet",
        "dataset_sources",
        "model_sources",
        "docker_image",
        "kernel_sources",
        "competition_sources",
    ):
        equal(meta[key], localmeta[key], "remote settings")
    equal(meta["id_no"], sub["kernel_id"], "remote kernel id")
    code = meta["code_file"]
    if Path(code).name != code or set(remotes) != {code, "kernel-metadata.json"}:
        raise ValueError("exact remote source files required")
    equal(digest(remote / code), sub["remote_source_sha256"], "remote executable")
    constants = launcher_constants(remote / code)
    equal(constants["SOURCE_COMMIT"], sub["source_commit"], "embedded source")
    equal(constants["SOURCE_FILES"], pre["package_sha256"], "embedded source hashes")
    equal(constants["BUNDLE_SHA"], BUNDLE_SHA, "embedded Dataset")
    equal(constants["ARCHIVE_SHA"], pre["archive_sha256"], "archive pin")
    equal(
        hashlib.sha256(base64.b64decode(constants["ARCHIVE"], validate=True)).hexdigest(),
        pre["archive_sha256"],
        "embedded archive bytes",
    )
    bundle = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset"
    equal(digest(bundle / "guard_bundle.json"), BUNDLE_SHA, "Dataset manifest")
    value = json.loads((bundle / "guard_bundle.json").read_text())
    pin = GuardSnapshot.model_validate(value["snapshot"])
    hashes = {f.name: f.sha256 for f in pin.files if f.name in FILES}
    equal(inventory(raw / "language/tokenizer"), hashes, "tokenizer bytes")
    config = json.loads((raw / "language/tokenizer/config.json").read_text())
    generation = json.loads((raw / "language/tokenizer/generation_config.json").read_text())
    expected_admission = dict(
        snapshot_sha256=pin.sha256,
        model_revision=pin.model_revision,
        tokenizer_sha256=hashes,
        vocabulary_size=config["vocab_size"],
        eos=sorted(generation["eos_token_id"]),
        dataset_manifest_sha256=BUNDLE_SHA,
        model_weights_read=False,
        full_weight_archive_authenticated=False,
    )
    equal(
        json.loads((raw / "language/admission.json").read_text()), expected_admission, "admission"
    )
    expected_bootstrap = dict(
        protocol="guard_language_cpu_package_v1",
        source_commit=sub["source_commit"],
        source_sha256=pre["package_sha256"],
        archive_sha256=pre["archive_sha256"],
        dataset_manifest_sha256=BUNDLE_SHA,
        snapshot=value["snapshot"],
        wheel_sha256=value["wheel_sha256"],
        gpu_used=False,
        model_loads=0,
    )
    equal(
        json.loads((raw / "language_bootstrap.json").read_text()), expected_bootstrap, "bootstrap"
    )
    wheel = bundle / "transformers-5.5.0-py3-none-any.whl"
    equal(digest(wheel), value["wheel_sha256"][wheel.name], "wheel hash")
    with zipfile.ZipFile(wheel) as stream:
        processor_sha = hashlib.sha256(
            stream.read("transformers/generation/logits_process.py")
        ).hexdigest()
    summary = json.loads((raw / "language/summary.json").read_text())
    native_summary(summary, sub["source_commit"], processor_sha)
    expected_files = {"language/" + p for p in ("admission.json", "summary.json")}
    expected_files |= {"language/tokenizer/" + p for p in FILES}
    expected_files |= {"language_bootstrap.json", "react-vn-guard-language-cpu-v1.log"}
    equal(sorted(before), sorted(expected_files), "raw file coverage")
    equal(inventory(raw), before, "raw unchanged")
    equal(inventory(remote), remotes, "remote unchanged")
    return dict(
        protocol="guard_language_cpu_release_audit_v1",
        valid=True,
        source_authenticated=True,
        native_metrics_recomputed_locally=False,
        summary=summary,
        raw_sha256=before,
        remote_sha256=remotes,
        observation_sha256=digest(observation_path),
        source_pins_verified=len(pre["source_sha256"]),
        phase5_accepted=False,
        limitations=(
            "Authenticates executing source and bounded reported CPU checks; "
            "does not rerun native libraries or prove model generation."
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "remote", "observation", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    for path in (args.raw, args.remote, args.observation, args.output):
        no_links(path)
    if (
        args.output.exists()
        or not args.output.resolve().is_relative_to(ROOT / "results")
        or any(args.output.resolve().is_relative_to(p.resolve()) for p in (args.raw, args.remote))
    ):
        raise ValueError("fresh results output outside inputs required")
    result = audit(args.raw, args.remote, args.observation)
    args.output.mkdir(parents=True)
    write_receipt(args.output / "audit.json", result)
    print("LANGUAGE_CPU_RELEASE_AUDIT_COMPLETE")


if __name__ == "__main__":
    main()
