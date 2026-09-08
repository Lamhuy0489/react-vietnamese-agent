#!/usr/bin/env python3
"""Render a tiny stdlib-only CPU Kaggle scanner; no model bundle/download."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import HANDLE, validate_inventory

ROOT = Path(__file__).resolve().parents[1]
TAIL = """

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--output", type=Path, default=Path("/kaggle/working/mount_receipt.json"))
    args = parser.parse_args()
    started = time.monotonic()
    identity = {"source_commit": SOURCE_COMMIT, "verifier_sha256": VERIFIER_SHA256,
                "inventory_sha256": INVENTORY_SHA256, "model_handle": HANDLE}
    try:
        result = scan_mount(resolve_mount(args.input_root), INVENTORY)
    except Exception as exc:
        result = {"protocol": "agent_mount_auth_v1", "valid": False,
                  "error_class": type(exc).__name__, "phase5_accepted": False,
                  "model_loads": 0, "gpu_used": False, "automatic_retry": False,
                  "elapsed_seconds": time.monotonic() - started}
    result["identity"] = identity
    write_receipt(args.output, result)
    print("AGENT_MOUNT_AUTH_COMPLETE valid=" + str(result["valid"]), flush=True)
    return 0 if result["valid"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
"""


def render(source: str, inventory: dict[str, Any], commit: str, pin_hash: str) -> str:
    validate_inventory(inventory)
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("committed source identity required")
    if len(pin_hash) != 64 or any(c not in "0123456789abcdef" for c in pin_hash):
        raise ValueError("inventory digest required")
    return (
        source
        + "\n"
        + "\n".join(
            [
                f"SOURCE_COMMIT = {commit!r}",
                f"VERIFIER_SHA256 = {hashlib.sha256(source.encode()).hexdigest()!r}",
                f"INVENTORY_SHA256 = {pin_hash!r}",
                f"INVENTORY = {inventory!r}",
            ]
        )
        + TAIL
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or not args.output.resolve().is_relative_to(ROOT / "build/kaggle"):
        raise ValueError("fresh build/kaggle directory required")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT):  # noqa: S603,S607
        raise ValueError("clean committed source required")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603,S607
    source_path = ROOT / "src/react_agent/llm/agent_mount_v1.py"
    pin_path = ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json"
    pin_hash = hashlib.sha256(pin_path.read_bytes()).hexdigest()
    wrapper = render(source_path.read_text(), json.loads(pin_path.read_text()), commit, pin_hash)
    args.output.mkdir(parents=True)
    (args.output / "agent_mount_kernel_v1.py").write_text(wrapper)
    metadata = {
        "id": "huylmhuhu/react-vn-agent7b-mount-auth-v1",
        "title": "ReAct VN Agent Mount Auth v1",
        "code_file": "agent_mount_kernel_v1.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "dataset_sources": [],
        "model_sources": [HANDLE],
        "competition_sources": [],
        "kernel_sources": [],
    }
    (args.output / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(
        json.dumps(
            {
                "source_commit": commit,
                "wrapper_sha256": hashlib.sha256(wrapper.encode()).hexdigest(),
                "inventory_sha256": pin_hash,
                "model_handle": HANDLE,
                "gpu": False,
            }
        )
    )


if __name__ == "__main__":
    main()
