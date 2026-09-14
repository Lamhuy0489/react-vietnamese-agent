#!/usr/bin/env python3
"""Build a small exact native overlay and audit archive/expanded mounts offline.

This is a package integrity/import preflight only. It intentionally does not
materialize weights, access Test data, or claim that native submission is ready.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.validation.grouped_dev_plan_v1 import DEV_SHA256

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "docs/architecture/phase5_grouped_native_v2_contract.md",
    "scripts/audit_phase5_grouped_dev.py",
    "scripts/run_phase5_grouped_dev.py",
    "src/react_agent/llm/grouped_dev_identity_v2.py",
    "src/react_agent/llm/grouped_dev_runner_v2.py",
    "src/react_agent/validation/grouped_dev_checkpoint_v2.py",
    "src/react_agent/validation/grouped_dev_native_audit_v2.py",
)


def digest(path: Path) -> str:
    no_links(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle output required")
    base_archive = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/source.tar.gz"
    base_manifest = ROOT / "build/kaggle/phase5_guard_probe_v1_bundle03/dataset/guard_bundle.json"
    no_links(base_archive)
    no_links(base_manifest)
    if not base_archive.is_file() or not base_manifest.is_file():
        raise ValueError("accepted base package missing")
    output.mkdir(parents=True)
    overlay = output / "overlay"
    expanded = output / "expanded"
    overlay.mkdir()
    expanded.mkdir()
    source = {}
    for name in FILES:
        source[name] = digest(ROOT / name)
        destination = overlay / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    shutil.copy2(base_archive, output / "base_source.tar.gz")
    shutil.copy2(base_manifest, output / "base_manifest.json")
    with tarfile.open(output / "native_overlay.tar.gz", "w:gz") as archive:
        archive.add(overlay, arcname="overlay", recursive=True)
    with tarfile.open(output / "base_source.tar.gz", "r:gz") as archive:
        for member in archive.getmembers():
            target = (expanded / member.name).resolve()
            if not target.is_relative_to(expanded.resolve()):
                raise ValueError("archive path traversal")
            archive.extract(member, expanded)
    extracted = next((p for p in expanded.iterdir() if p.is_dir()), expanded)
    for name in FILES:
        destination = extracted / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(overlay / name, destination)
    # Compile the expanded source without executing an inference path. This
    # catches syntax/import-file omissions while keeping models and data sealed.
    python = shutil.which("python3")
    if python is None:
        raise ValueError("python3 unavailable")
    compile_run = subprocess.run(  # noqa: S603 - fixed local compile command
        [python, "-m", "compileall", "-q", str(extracted / "src"), str(extracted / "scripts")],
        cwd=ROOT,
        check=False,
    )
    if compile_run.returncode != 0:
        raise ValueError("expanded native overlay does not compile")
    observed = {name: digest(extracted / name) for name in FILES}
    receipt = dict(
        protocol="grouped_dev_native_exact_preflight_v1",
        valid=observed == source,
        source_sha256=source,
        expanded_sha256=observed,
        base_archive_sha256=digest(output / "base_source.tar.gz"),
        base_manifest_sha256=digest(output / "base_manifest.json"),
        overlay_archive_sha256=digest(output / "native_overlay.tar.gz"),
        dev_sha256=dict(DEV_SHA256),
        archive_mount_checked=True,
        expanded_mount_checked=True,
        compile_only=True,
        actual_model_loads=0,
        gpu_runs=0,
        test_payload_accessed=False,
        native_submission_ready=False,
        scope="Overlay/archive/expanded integrity and compile only; no weights, "
        "native model calls, guard quality or Kaggle submission.",
        remaining=[
            "full source/package import in isolated Kaggle-like venv",
            "native grouped GPU run with pinned mounts",
            "native artifact audit",
        ],
    )
    (output / "preflight_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if not receipt["valid"]:
        raise ValueError("native overlay hash mismatch")
    print(json.dumps(dict(valid=True, output=str(output), actual_model_loads=0)))


if __name__ == "__main__":
    main()
