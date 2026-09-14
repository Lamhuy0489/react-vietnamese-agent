#!/usr/bin/env python3
"""Audit isolated imports from the expanded grouped-native overlay package."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    no_links(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    output = args.output.resolve()
    no_links(package)
    if output.exists() or not package.is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh independent manifest output required")
    preflight = json.loads((package / "preflight_receipt.json").read_text())
    if preflight.get("valid") is not True or preflight.get("expanded_mount_checked") is not True:
        raise ValueError("valid expanded preflight required")
    expanded = package / "expanded"
    candidates = [
        p
        for p in (expanded, *expanded.iterdir())
        if p.is_dir() and (p / "src/react_agent/llm/grouped_dev_runner_v2.py").is_file()
    ]
    if len(candidates) != 1:
        raise ValueError("one expanded source root required")
    python = sys.executable
    code = (
        "import sys; from pathlib import Path; "
        "root=Path(sys.argv[1]); sys.path.insert(0, str(root/'src')); "
        "import react_agent; "
        "import react_agent.llm.grouped_dev_runner_v2; "
        "import react_agent.validation.grouped_dev_native_audit_v2; "
        "assert not {'torch','transformers','tokenizers'} & sys.modules.keys(); "
        "print('GROUPED_NATIVE_ISOLATED_IMPORT_OK')"
    )
    result = subprocess.run(  # noqa: S603 - fixed isolated import command
        [python, "-I", "-c", code, str(candidates[0])],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or "GROUPED_NATIVE_ISOLATED_IMPORT_OK" not in result.stdout:
        raise ValueError("isolated grouped native import failed")
    source = preflight["source_sha256"]
    expanded_hashes = {name: digest(candidates[0] / name) for name in source}
    if expanded_hashes != source:
        raise ValueError("expanded source changed after preflight")
    receipt = dict(
        protocol="grouped_dev_native_isolated_import_audit_v1",
        valid=True,
        source_commit="3486dbf",
        preflight_receipt_sha256=digest(package / "preflight_receipt.json"),
        expanded_source_sha256=expanded_hashes,
        isolated_python=True,
        stdout_marker="GROUPED_NATIVE_ISOLATED_IMPORT_OK",
        model_imported=False,
        actual_model_loads=0,
        gpu_runs=0,
        test_payload_accessed=False,
        native_submission_ready=False,
        scope="Expanded overlay imports only; no model, weights, GPU or Kaggle execution.",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(dict(valid=True, isolated_python=True, actual_model_loads=0)))


if __name__ == "__main__":
    main()
