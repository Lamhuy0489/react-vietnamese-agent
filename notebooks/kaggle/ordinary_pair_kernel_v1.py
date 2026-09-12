"""Ordinary six-request A/B/A package; frozen base and loaders, no Test payload."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from types import ModuleType

BASE64_SOURCE = "__BASE64_SOURCE__"
BASE_SHA256 = "__BASE_SHA256__"
SOURCE_COMMIT = "__SOURCE_COMMIT__"
EXPECTED_MANIFEST = "__EXPECTED_MANIFEST__"
OVERLAY: dict[str, dict[str, str]] = {}  # __PAIR_OVERLAY__
OVERLAY_PATHS = {
    "scripts/audit_phase5_ordinary_pair.py",
    "scripts/audit_phase5_ordinary_tokenizer.py",
    "scripts/collect_phase5_tokenizer_metadata.py",
    "scripts/run_phase5_ordinary_pair.py",
    "src/react_agent/llm/efficient_requests_v1.py",
    "src/react_agent/llm/ordinary_pair_probe_v1.py",
    "src/react_agent/llm/request_policy_pair_v1.py",
    "src/react_agent/llm/request_policy_v1.py",
    "src/react_agent/validation/efficient_requests_audit_v1.py",
    "src/react_agent/validation/ordinary_native_audit_v1.py",
    "src/react_agent/validation/ordinary_pair_audit_v1.py",
    "src/react_agent/validation/ordinary_tokenizer_audit_v1.py",
    "src/react_agent/validation/request_policy_audit_v1.py",
    "src/react_agent/validation/tokenizer_metadata_v1.py",
    "scripts/run_phase5_policy_stress_v3.py",
    "src/react_agent/llm/sdpa_probe_v1.py",
    "src/react_agent/llm/efficient_stress_v1.py",
    "src/react_agent/validation/efficient_stress_audit_v1.py",
    "scripts/check_phase5_efficient_factory.py",
    "scripts/run_phase5_efficient_stress.py",
    "scripts/run_phase5_efficient_dispatch.py",
    "src/react_agent/llm/agent_mount_v1.py",
    "src/react_agent/validation/agent_mount_audit_v1.py",
    "src/react_agent/llm/coexistence_placement_v1.py",
    "src/react_agent/llm/agent_runtime_input_v1.py",
    "src/react_agent/llm/agent_hf_v1.py",
    "src/react_agent/llm/agent_hf_v2.py",
    "src/react_agent/llm/model_pair_v1.py",
    "src/react_agent/llm/model_pair_probe_v1.py",
    "src/react_agent/llm/model_pair_hf_v1.py",
    "docs/evaluation/qwen7b_upstream_inventory_v1.json",
    "scripts/run_phase5_pair_worker.py",
    "src/react_agent/llm/pair_cancellation_v1.py",
    "scripts/run_phase5_pair_cancel_worker.py",
    "src/react_agent/llm/ipc_trace_v1.py",
    "scripts/run_phase5_pair_ipc_worker.py",
    "src/react_agent/llm/worker_progress_v1.py",
    "scripts/run_phase5_pair_progress_worker.py",
    "src/react_agent/llm/context_geometry_v1.py",
    "src/react_agent/llm/context_stress_v1.py",
    "src/react_agent/llm/generation_policy_v1.py",
    "src/react_agent/validation/guard_probe_audit_v2.py",
    "src/react_agent/validation/pair_cancellation_audit_v1.py",
    "src/react_agent/validation/context_stress_audit_v1.py",
    "src/react_agent/validation/generation_policy_audit_v1.py",
    "scripts/run_phase5_policy_native_compat.py",
    "src/react_agent/llm/context_stress_probe_v1.py",
    "scripts/run_phase5_context_stress_worker.py",
    "scripts/run_phase5_policy_stress_worker.py",
    "scripts/run_phase5_policy_stress_v2.py",
    "scripts/run_phase5_policy_stress_fixed.py",
    "scripts/check_phase5_policy_factory.py",
    "src/react_agent/llm/policy_stress_factory_v2.py",
    "src/react_agent/validation/context_policy_audit_v1.py",
    "docs/evaluation/publisher_policy_v1/agent_generation_config.json",
    "docs/evaluation/publisher_policy_v1/guard_generation_config.json",
}


def load_base(scratch: Path) -> ModuleType:
    data = base64.b64decode(BASE64_SOURCE, validate=True)
    if hashlib.sha256(data).hexdigest() != BASE_SHA256:
        raise ValueError("frozen bootstrap source mismatch")
    path = scratch / "frozen_bootstrap.py"
    with path.open("xb") as stream:
        stream.write(data)
    spec = importlib.util.spec_from_file_location("frozen_bootstrap", path)
    if spec is None or spec.loader is None:
        raise ValueError("bootstrap import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install_overlay(base: ModuleType, project: Path, original: dict[str, str]) -> dict[str, str]:
    base.verify_tree(project, original)
    if set(OVERLAY) != OVERLAY_PATHS:
        raise ValueError("exact model-pair overlay required")
    expanded = dict(original)
    for name, item in OVERLAY.items():
        base.relative_name(name)
        target = project / name
        if target.exists() or target.is_symlink() or name in original:
            raise ValueError("overlay cannot overwrite frozen source")
        contents = base64.b64decode(item["base64"], validate=True)
        if hashlib.sha256(contents).hexdigest() != item["sha256"]:
            raise ValueError("overlay content mismatch")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(contents)
        expanded[name] = item["sha256"]
    base.verify_tree(project, expanded)
    return expanded


def run_payload(
    base: ModuleType,
    python: Path,
    project: Path,
    dependencies: Path | None,
    runtime_commit: str,
    guard: Path,
    snapshot: Path,
    output: Path,
    input_root: Path,
) -> None:
    """Exact native routing; failures propagate without retries or relabeling."""
    candidates = [
        p.parent
        for p in input_root.rglob("config.json")
        if p.parent.parts[-4:] == ("qwen2.5", "transformers", "7b-instruct", "1")
    ]
    if len(candidates) != 1:
        raise ValueError("one pinned agent mount required")
    # The collector and loader independently reject symlinks and authenticate bytes.
    base.run(
        python,
        project,
        dependencies,
        runtime_commit,
        "scripts/collect_phase5_tokenizer_metadata.py",
        "--agent-path",
        str(candidates[0]),
        "--guard-path",
        str(guard),
        "--output",
        str(output / "tokenizers"),
    )
    publishers = output / "publishers"
    publishers.mkdir()
    for role in ("agent", "guard"):
        name = f"{role}_generation_config.json"
        shutil.copyfile(project / "docs/evaluation/publisher_policy_v1" / name, publishers / name)
    # These publisher bytes are pinned package metadata. The joined auditor binds
    # them to actual loader-admitted model file lists; they are not live mount copies.
    base.run(
        python,
        project,
        dependencies,
        runtime_commit,
        "scripts/run_phase5_ordinary_pair.py",
        "--backend",
        "hf",
        "--input-root",
        str(input_root),
        "--guard-path",
        str(guard),
        "--snapshot",
        str(snapshot),
        "--output",
        str(output / "ordinary_probe"),
        "--policy-output",
        str(output / "generation_policy"),
        "--attention-output",
        str(output / "attention_policy"),
    )
    base.run(
        python,
        project,
        dependencies,
        runtime_commit,
        "scripts/audit_phase5_ordinary_tokenizer.py",
        "--probe",
        str(output / "ordinary_probe"),
        "--policy",
        str(output / "generation_policy"),
        "--attention",
        str(output / "attention_policy"),
        "--publishers",
        str(publishers),
        "--tokenizers",
        str(output / "tokenizers"),
        "--snapshot",
        str(snapshot),
        "--source-commit",
        SOURCE_COMMIT,
        "--output",
        str(output / "ordinary_native_audit.json"),
    )


def main() -> None:
    output, input_root = Path("/kaggle/working"), Path("/kaggle/input")
    if len(SOURCE_COMMIT) != 40 or any(c not in "0123456789abcdef" for c in SOURCE_COMMIT):
        raise ValueError("committed wrapper source required")
    for name in (
        "ordinary_bootstrap_identity.json",
        "dummy",
        "tokenizers",
        "publishers",
        "ordinary_probe",
        "generation_policy",
        "attention_policy",
        "ordinary_native_audit.json",
    ):
        if (output / name).exists() or (output / name).is_symlink():
            raise ValueError("fresh ordinary output paths required")
    os.environ["PAIR_SOURCE_COMMIT"] = SOURCE_COMMIT
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory(prefix="ordinary-pair-") as temporary:
        scratch = Path(temporary).resolve()
        base = load_base(scratch)
        bundle, value = base.manifest(input_root, EXPECTED_MANIFEST)
        with (output / "ordinary_bootstrap_identity.json").open("x") as stream:
            json.dump(
                {
                    "protocol": "ordinary_pair_bootstrap_v1",
                    "source_commit": SOURCE_COMMIT,
                    "runtime_commit": value["source_commit"],
                    "base_source_sha256": BASE_SHA256,
                    "bundle_manifest_sha256": EXPECTED_MANIFEST,
                    "overlay_sha256": {n: v["sha256"] for n, v in OVERLAY.items()},
                    "snapshot": value["snapshot"],
                    "wheel_sha256": value["wheel_sha256"],
                },
                stream,
                indent=2,
            )
        project, guard = scratch / "project", scratch / "guard"
        base.materialize(
            bundle,
            "source.tar.gz",
            value["source_archive_sha256"],
            "pyproject.toml",
            project,
            value["source_sha256"],
            source_commit=value["source_commit"],
        )
        base.materialize(
            bundle,
            "guard-model.tar",
            value["model_archive_sha256"],
            "model.safetensors",
            guard,
            {f["name"]: f["sha256"] for f in value["snapshot"]["files"]},
        )
        expanded = install_overlay(base, project, value["source_sha256"])
        try:
            deps, python = scratch / "dependencies", Path(sys.executable)
            base.install(python, bundle, value, deps)
            commit = value["source_commit"]
            base.run(python, project, deps, commit, "scripts/preflight_clean_worker.py")
            for extra in ((), ("--resume",)):
                base.run(
                    python,
                    project,
                    deps,
                    commit,
                    "scripts/run_clean_v11_dev.py",
                    "--output",
                    str(output / "dummy"),
                    *extra,
                )
            snapshot = scratch / "snapshot.json"
            snapshot.write_text(json.dumps(value["snapshot"]))
            run_payload(base, python, project, deps, commit, guard, snapshot, output, input_root)
        finally:
            base.verify_tree(project, expanded)
    print("ORDINARY_PAIR_GPU_V1_COMPLETE artifact_audit_only=True")


if __name__ == "__main__":
    main()
