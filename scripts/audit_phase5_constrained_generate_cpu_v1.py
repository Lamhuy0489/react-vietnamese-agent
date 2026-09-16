"""Authenticate saved CPU compatibility artifacts; never execute downloaded code."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from audit_phase5_bare_json_saved_v1 import launcher_constants

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.guard_language_native_v1 import BUNDLE_SHA, FILES, digest
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.constrained_generate_cpu_audit_v1 import validate_result
from react_agent.validation.context_stress_audit_v1 import equal

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = "experiments/manifests/phase5_constrained_generate_cpu_submission02.json"


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
        protocol="constrained_generate_cpu_package_v1",
        source_commit=sub["source_commit"],
        source_sha256=pre["package_sha256"],
        archive_sha256=pre["archive_sha256"],
        dataset_manifest_sha256=BUNDLE_SHA,
        snapshot=value["snapshot"],
        wheel_sha256=value["wheel_sha256"],
        gpu_used=False,
        pretrained_model_loads=0,
        random_models_planned=4,
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
    validate_result(
        raw / "language/generation", summary, sub["source_commit"], wheel, processor_sha
    )
    expected_files = {"language/" + p for p in ("admission.json", "summary.json")}
    expected_files |= {"language/tokenizer/" + p for p in FILES}
    expected_files |= {"language_bootstrap.json", "react-vn-constrained-generate-cpu-v2.log"}
    expected_files |= {"language/generation/" + p for p in inventory(raw / "language/generation")}
    equal(sorted(before), sorted(expected_files), "raw file coverage")
    equal(inventory(raw), before, "raw unchanged")
    equal(inventory(remote), remotes, "remote unchanged")
    return dict(
        protocol="constrained_generate_cpu_release_audit_v1",
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
            "does not rerun native libraries or prove production guard quality/CUDA."
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
    print("CONSTRAINED_GENERATE_CPU_AUDIT_COMPLETE")


if __name__ == "__main__":
    main()
