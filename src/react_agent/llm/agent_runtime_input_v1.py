"""Live byte and tensor-layout admission; no torch, downloads, or model prompts."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.llm.agent_mount_v1 import REQUIRED, SHARDS, no_links, scan_mount
from react_agent.llm.coexistence_placement_v1 import (
    HIDDEN,
    INTERMEDIATE,
    KV_WIDTH,
    LAYERS,
    VOCAB,
    validate_agent_geometry,
)
from react_agent.validation.agent_mount_audit_v1 import classify_scan

INVENTORY_SHA256 = "9023d04a65f44a4e4beef29efba9f1ca088e2af1990cc82e586f457d4c5c43b3"
README_SHA256 = "0981c06fb21db45eca831ebafa68861b654587566a8e3071aece79cf60329b71"
README_BLOB = "19613c71726c705978eb7fed4ce46c8625418a5b"
HEADER_LIMIT = 2 * 1024**2


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_object(path: Path) -> dict[str, Any]:
    no_links(path)
    with path.open("rb") as stream:
        raw = stream.read(HEADER_LIMIT + 1)
    if len(raw) > HEADER_LIMIT:
        raise ValueError("metadata size limit")
    result = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(result, dict):
        raise ValueError("JSON object required")
    return result


def parameter_shapes() -> dict[str, tuple[int, ...]]:
    shapes = {
        "model.embed_tokens.weight": (VOCAB, HIDDEN),
        "model.norm.weight": (HIDDEN,),
        "lm_head.weight": (VOCAB, HIDDEN),
    }
    for i in range(LAYERS):
        prefix = f"model.layers.{i}."
        for projection, width in (("q", HIDDEN), ("k", KV_WIDTH), ("v", KV_WIDTH)):
            shapes[prefix + f"self_attn.{projection}_proj.weight"] = (width, HIDDEN)
            shapes[prefix + f"self_attn.{projection}_proj.bias"] = (width,)
        shapes[prefix + "self_attn.o_proj.weight"] = (HIDDEN, HIDDEN)
        for name in ("gate", "up"):
            shapes[prefix + f"mlp.{name}_proj.weight"] = (INTERMEDIATE, HIDDEN)
        shapes[prefix + "mlp.down_proj.weight"] = (HIDDEN, INTERMEDIATE)
        for name in ("input_layernorm", "post_attention_layernorm"):
            shapes[prefix + name + ".weight"] = (HIDDEN,)
    return shapes


def inspect_tensor_layout(root: Path) -> dict[str, Any]:
    """Validate header/index geometry without reading tensor payload into memory."""
    no_links(root)
    expected = parameter_shapes()
    index = read_object(root / "model.safetensors.index.json")
    mapping = index.get("weight_map")
    if not isinstance(mapping, dict) or set(mapping) != set(expected):
        raise ValueError("exact parameter index required")
    if any(type(v) is not str for v in mapping.values()) or set(mapping.values()) != SHARDS:
        raise ValueError("exact four local shards required")
    total = 2 * sum(math.prod(shape) for shape in expected.values())
    metadata = index.get("metadata")
    if (
        not isinstance(metadata, dict)
        or type(metadata.get("total_size")) is not int
        or metadata["total_size"] != total
    ):
        raise ValueError("index parameter byte count mismatch")
    seen: set[str] = set()
    for name in sorted(SHARDS):
        path = root / name
        no_links(path)
        with path.open("rb") as stream:
            prefix = stream.read(8)
            if len(prefix) != 8:
                raise ValueError("missing safetensors header length")
            length = struct.unpack("<Q", prefix)[0]
            if not 2 <= length <= HEADER_LIMIT:
                raise ValueError("safetensors header size limit")
            raw = stream.read(length)
        if len(raw) != length or not raw.startswith(b"{"):
            raise ValueError("invalid safetensors header")
        header = json.loads(raw, object_pairs_hook=unique_object)
        if not isinstance(header, dict):
            raise ValueError("tensor header object required")
        details = header.pop("__metadata__", {})
        if not isinstance(details, dict) or any(not isinstance(v, str) for v in details.values()):
            raise ValueError("invalid safetensors metadata")
        ranges = []
        for tensor, info in header.items():
            if tensor in seen or tensor not in expected or mapping[tensor] != name:
                raise ValueError("duplicate, unknown or misindexed tensor")
            if not isinstance(info, dict) or set(info) != {"dtype", "shape", "data_offsets"}:
                raise ValueError("invalid tensor description")
            shape, offsets = info["shape"], info["data_offsets"]
            if (
                info["dtype"] not in ("BF16", "F16")
                or not isinstance(shape, list)
                or any(type(d) is not int for d in shape)
                or tuple(shape) != expected[tensor]
                or not isinstance(offsets, list)
                or len(offsets) != 2
                or any(type(d) is not int for d in offsets)
                or offsets[0] < 0
                or offsets[1] - offsets[0] != 2 * math.prod(shape)
            ):
                raise ValueError("tensor dtype/shape/offset mismatch")
            ranges.append(tuple(offsets))
            seen.add(tensor)
        end = 0
        for start, stop in sorted(ranges):
            if start != end:
                raise ValueError("tensor data gap or overlap")
            end = stop
        if end != path.stat().st_size - 8 - length:
            raise ValueError("unindexed or truncated tensor bytes")
    if seen != set(expected):
        raise ValueError("incomplete tensor coverage")
    return {"parameter_tensors": len(seen), "serialized_parameter_bytes": total}


def admit_runtime_scan(scan: dict[str, Any], pin: dict[str, Any]) -> dict[str, Any]:
    """Pure classification helper, NOT sufficient authority to load a model."""
    identity = {"inventory_sha256": INVENTORY_SHA256}
    classified = classify_scan(scan | {"identity": identity}, pin, identity)
    mismatches = classified["mismatches"]
    if mismatches:
        row = (
            next(r for r in scan["files"] if r["name"] == "README.md")
            if (mismatches == ["README.md"])
            else {}
        )
        if (
            row.get("size") != 6005
            or row.get("sha256") != README_SHA256
            or row.get("git_blob_sha1") != README_BLOB
        ):
            raise ValueError("unapproved mount mismatch")
    files = [{k: r[k] for k in ("name", "size", "sha256")} for r in scan["files"]]
    identity_value = {
        "protocol": "agent_runtime_input_v1",
        "inventory": INVENTORY_SHA256,
        "files": files,
    }
    return {
        "protocol": "agent_runtime_input_v1",
        "inventory_sha256": INVENTORY_SHA256,
        "content_sha256": hashlib.sha256(canonical_json(identity_value).encode()).hexdigest(),
        "full_inventory_match": classified["full_inventory_match"],
        "documentation_mismatches": mismatches,
        "runtime_files_match": True,
        "runtime_files": len(REQUIRED),
        "files": files,
        "phase5_accepted": False,
    }


def authenticate_runtime(root: Path, inventory_path: Path) -> dict[str, Any]:
    """Loaders must call this on the live trusted read-only mount, not a receipt."""
    no_links(inventory_path)
    if hashlib.sha256(inventory_path.read_bytes()).hexdigest() != INVENTORY_SHA256:
        raise ValueError("publisher inventory pin mismatch")
    pin = read_object(inventory_path)
    receipt = admit_runtime_scan(scan_mount(root, pin), pin)
    validate_agent_geometry(read_object(root / "config.json"))
    receipt.update(inspect_tensor_layout(root))
    return receipt
