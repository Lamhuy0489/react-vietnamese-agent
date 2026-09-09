"""Synthetic saved scan claims; no model bytes or network."""

import copy
from typing import Any

import pytest

from react_agent.llm.agent_mount_v1 import MODEL, OPTIONAL, REQUIRED, REVISION, SHARDS
from react_agent.validation.agent_mount_audit_v1 import classify_scan


def fixture() -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    files = [
        {
            "name": n,
            "size": 3,
            "git_blob_sha1": "a" * 40,
            "lfs_sha256": "b" * 64 if n in SHARDS else None,
        }
        for n in sorted(REQUIRED | OPTIONAL)
    ]
    pin = {"model_id": MODEL, "upstream_revision": REVISION, "files": files}
    identity = {"source_commit": "c" * 40}
    rows = [
        {
            "name": r["name"],
            "size": 3,
            "sha256": "b" * 64,
            "git_blob_sha1": None if r["name"] in SHARDS else "a" * 40,
            "publisher_match": True,
        }
        for r in files
    ]
    scan = {
        "protocol": "agent_mount_auth_v1",
        "model_handle": "qwen-lm/qwen2.5/transformers/7b-instruct/1",
        "model_id": MODEL,
        "upstream_revision": REVISION,
        "identity": identity,
        "gpu_used": False,
        "automatic_retry": False,
        "model_loads": 0,
        "phase5_accepted": False,
        "valid": True,
        "missing": [],
        "extra": [],
        "optional_absent": [],
        "files": rows,
        "bytes_hashed": 42,
        "elapsed_seconds": 1.0,
    }
    return scan, pin, identity


@pytest.mark.parametrize("name", [None, "README.md", "config.json", sorted(SHARDS)[0]])
def test_classification(name: str | None) -> None:
    scan, pin, identity = fixture()
    if name:
        row = next(r for r in scan["files"] if r["name"] == name)
        row["sha256" if name in SHARDS else "git_blob_sha1"] = "d" * (64 if name in SHARDS else 40)
        row["publisher_match"] = False
        scan["valid"] = False
    result = classify_scan(scan, pin, identity)
    assert result["full_inventory_match"] is (name is None)
    assert result["runtime_files_match"] is (name is None or name == "README.md")
    assert not result["mount_admitted_for_loader"] and not result["phase5_accepted"]


@pytest.mark.parametrize(
    "kind",
    [
        "identity",
        "duplicate",
        "count",
        "flag",
        "digest",
        "size",
        "gpu",
        "nan",
        "missing",
        "extra",
        "summary",
    ],
)
def test_tampered_claim(kind: str) -> None:
    scan, pin, identity = fixture()
    scan = copy.deepcopy(scan)
    if kind == "identity":
        scan["identity"] = {}
    elif kind == "duplicate":
        scan["files"].append(scan["files"][0])
    elif kind == "count":
        scan["bytes_hashed"] = 1
    elif kind == "flag":
        scan["files"][0]["publisher_match"] = False
    elif kind == "digest":
        scan["files"][0]["sha256"] = "bad"
    elif kind == "size":
        scan["files"][0]["size"] = True
    elif kind == "gpu":
        scan["gpu_used"] = True
    elif kind == "nan":
        scan["elapsed_seconds"] = float("nan")
    elif kind in {"missing", "extra"}:
        scan[kind] = ["config.json"]
    else:
        scan["valid"] = False
    with pytest.raises(ValueError):
        classify_scan(scan, pin, identity)
