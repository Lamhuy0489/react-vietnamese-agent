"""Recompute hash-match claims from saved scan records, without touching weights."""

from __future__ import annotations

import math
import re
from typing import Any

from react_agent.llm.agent_mount_v1 import (
    HANDLE,
    MODEL,
    OPTIONAL,
    REQUIRED,
    REVISION,
    SHARDS,
    validate_inventory,
)


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def classify_scan(
    scan: dict[str, Any], pin: dict[str, Any], identity: dict[str, str]
) -> dict[str, Any]:
    inventory = validate_inventory(pin)
    require(scan["identity"] == identity, "scan identity")
    for key, value in {
        "protocol": "agent_mount_auth_v1",
        "model_handle": HANDLE,
        "model_id": MODEL,
        "upstream_revision": REVISION,
        "gpu_used": False,
        "automatic_retry": False,
        "model_loads": 0,
        "phase5_accepted": False,
    }.items():
        require(type(scan[key]) is type(value) and scan[key] == value, "fixed scan field: " + key)
    require(scan["missing"] == [] and scan["extra"] == [], "incomplete or extra inventory")
    rows = scan["files"]
    names = [r["name"] for r in rows]
    require(
        names == sorted(set(names)) and REQUIRED.issubset(names) and set(names).issubset(inventory),
        "unique sorted runtime coverage",
    )
    require(scan["optional_absent"] == sorted(OPTIONAL - set(names)), "optional coverage")
    mismatches = []
    for row in rows:
        name = row["name"]
        require(type(row["size"]) is int and row["size"] > 0, "observed size")
        require(
            isinstance(row["sha256"], str)
            and re.fullmatch("[0-9a-f]{64}", row["sha256"]) is not None,
            "observed SHA256",
        )
        if name in SHARDS:
            require(row["git_blob_sha1"] is None, "shard hash encoding")
            same = row["sha256"] == inventory[name]["lfs_sha256"]
        else:
            require(
                isinstance(row["git_blob_sha1"], str)
                and re.fullmatch("[0-9a-f]{40}", row["git_blob_sha1"]) is not None,
                "observed Git blob",
            )
            same = row["git_blob_sha1"] == inventory[name]["git_blob_sha1"]
        same = same and row["size"] == inventory[name]["size"]
        require(row["publisher_match"] is same, "forged file match")
        if not same:
            mismatches.append(name)
    require(
        type(scan["bytes_hashed"]) is int and scan["bytes_hashed"] == sum(r["size"] for r in rows),
        "byte count",
    )
    elapsed = scan["elapsed_seconds"]
    require(
        type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed > 0, "scan duration"
    )
    require(scan["valid"] is (not mismatches), "full match claim")
    runtime_match = not (REQUIRED & set(mismatches))
    return {
        "protocol": "agent_mount_scan_audit_v1",
        "audit_integrity_valid": True,
        "full_inventory_match": not mismatches,
        "runtime_files_match": runtime_match,
        "runtime_files": len(REQUIRED),
        "observed_files": len(rows),
        "mismatches": mismatches,
        "bytes_hashed_on_kaggle": scan["bytes_hashed"],
        "scan_seconds": elapsed,
        "mount_admitted_for_loader": False,
        "phase5_accepted": False,
        "model_loads": 0,
        "gpu_used": False,
        "limits": "Checks trusted worker hash records, not a second scan of weights. "
        "Full mismatch is retained; a versioned mount contract is required before loading.",
    }
