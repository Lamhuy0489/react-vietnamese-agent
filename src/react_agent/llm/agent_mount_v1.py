"""Stdlib-only read-only mount authentication; never downloads or loads models."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

MODEL = "Qwen/Qwen2.5-7B-Instruct"
REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
HANDLE = "qwen-lm/qwen2.5/transformers/7b-instruct/1"
SHARDS = {f"model-{i:05}-of-00004.safetensors" for i in range(1, 5)}
REQUIRED = SHARDS | {
    "config.json",
    "generation_config.json",
    "merges.txt",
    "model.safetensors.index.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
}
OPTIONAL = {"README.md", "LICENSE", ".gitattributes"}


def validate_inventory(pin: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if pin.get("model_id") != MODEL or pin.get("upstream_revision") != REVISION:
        raise ValueError("unrecognized publisher identity")
    rows = pin["files"]
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise ValueError("inventory rows required")
    names = [r["name"] for r in rows]
    if any(not isinstance(n, str) for n in names) or names != sorted(REQUIRED | OPTIONAL):
        raise ValueError("exact sorted publisher inventory required")
    for r in rows:
        if type(r["size"]) is not int or r["size"] <= 0:
            raise ValueError("positive integer file size required")
        if not isinstance(r["git_blob_sha1"], str) or not re.fullmatch(
            "[0-9a-f]{40}", r["git_blob_sha1"]
        ):
            raise ValueError("Git blob digest required")
        lfs = r["lfs_sha256"]
        if r["name"] in SHARDS:
            if not isinstance(lfs, str) or not re.fullmatch("[0-9a-f]{64}", lfs):
                raise ValueError("weight SHA256 required")
        elif lfs is not None:
            raise ValueError("metadata must have Git blob identity")
    return {r["name"]: r for r in rows}


def no_links(path: Path) -> None:
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("linked mount path")


def resolve_mount(root: Path) -> Path:
    no_links(root)
    suffix = ("qwen2.5", "transformers", "7b-instruct", "1")
    candidates = [p.parent for p in root.rglob("config.json") if p.parent.parts[-4:] == suffix]
    if len(candidates) != 1:
        raise ValueError("one pinned mount required")
    no_links(candidates[0])
    return candidates[0]


def scan_mount(root: Path, pin: dict[str, Any]) -> dict[str, Any]:
    inventory = validate_inventory(pin)
    no_links(root)
    if not root.is_dir():
        raise ValueError("mount directory required")
    paths = sorted(root.iterdir())
    names = {p.name for p in paths}
    missing, extra = sorted(REQUIRED - names), sorted(names - set(inventory))
    records = []
    started = time.monotonic()
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError("linked or non-file mount entry")
        if path.name not in inventory:
            continue
        expected = inventory[path.name]
        size = path.stat().st_size
        digest = hashlib.sha256()
        blob = hashlib.sha1(b"blob " + str(size).encode() + b"\0")  # noqa: S324 - publisher Git identity
        count = 0
        with path.open("rb") as stream:
            while block := stream.read(1024 * 1024):
                count += len(block)
                digest.update(block)
                blob.update(block)
        matched = count == size == expected["size"] and (
            digest.hexdigest() == expected["lfs_sha256"]
            if path.name in SHARDS
            else blob.hexdigest() == expected["git_blob_sha1"]
        )
        records.append(
            {
                "name": path.name,
                "size": count,
                "sha256": digest.hexdigest(),
                "git_blob_sha1": blob.hexdigest() if path.name not in SHARDS else None,
                "publisher_match": matched,
            }
        )
    if names != {p.name for p in root.iterdir()}:
        raise ValueError("mount inventory changed during scan")
    valid = not missing and not extra and all(r["publisher_match"] for r in records)
    return {
        "protocol": "agent_mount_auth_v1",
        "valid": valid,
        "phase5_accepted": False,
        "model_handle": HANDLE,
        "model_id": MODEL,
        "upstream_revision": REVISION,
        "missing": missing,
        "extra": extra,
        "files": records,
        "optional_absent": sorted(OPTIONAL - names),
        "bytes_hashed": sum(r["size"] for r in records),
        "elapsed_seconds": time.monotonic() - started,
        "model_loads": 0,
        "gpu_used": False,
        "automatic_retry": False,
        "scope": "Read-only runtime file byte authentication; no inference or placement proof",
    }


def write_receipt(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
