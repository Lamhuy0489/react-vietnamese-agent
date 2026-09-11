"""GPU tensor diagnostic only; no weights materialized or model generation."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
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
    "src/react_agent/llm/sdpa_probe_v1.py",
    "src/react_agent/validation/sdpa_probe_audit_v1.py",
    "scripts/run_phase5_sdpa_probe.py",
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


def main() -> None:
    output = Path("/kaggle/working")
    os.environ["PAIR_SOURCE_COMMIT"] = SOURCE_COMMIT
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory(prefix="model-pair-") as temporary:
        scratch = Path(temporary)
        base = load_base(scratch)
        bundle, value = base.manifest(Path("/kaggle/input"), EXPECTED_MANIFEST)
        with (output / "sdpa_tensor_bootstrap_identity.json").open("x") as stream:
            json.dump(
                {
                    "protocol": "sdpa_tensor_bootstrap_v1",
                    "source_commit": SOURCE_COMMIT,
                    "base_source_sha256": BASE_SHA256,
                    "bundle_manifest_sha256": EXPECTED_MANIFEST,
                    "overlay_sha256": {n: v["sha256"] for n, v in OVERLAY.items()},
                    "snapshot": value["snapshot"],
                    "wheel_sha256": value["wheel_sha256"],
                },
                stream,
                indent=2,
            )
        project = scratch / "project"
        base.materialize(
            bundle,
            "source.tar.gz",
            value["source_archive_sha256"],
            "pyproject.toml",
            project,
            value["source_sha256"],
            source_commit=value["source_commit"],
        )
        expanded = install_overlay(base, project, value["source_sha256"])
        deps = scratch / "dependencies"
        python = Path(sys.executable)
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
        try:
            base.run(
                python,
                project,
                deps,
                commit,
                "scripts/run_phase5_sdpa_probe.py",
                "--backend",
                "native",
                "--output",
                str(output / "sdpa_tensor"),
            )
        finally:
            base.verify_tree(project, expanded)
    print("SDPA_TENSOR_GPU_COMPLETE")


if __name__ == "__main__":
    main()
