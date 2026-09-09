"""Synthetic headers/tiny bytes and saved public receipts; no real model load."""

import copy
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm import agent_runtime_input_v1 as runtime
from react_agent.llm.agent_mount_v1 import MODEL, OPTIONAL, REQUIRED, REVISION, SHARDS
from react_agent.llm.coexistence_placement_v1 import PARAMETERS

ROOT = Path(__file__).resolve().parents[2]


def test_actual_inventory_pin_and_saved_diagnostic() -> None:
    path = ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == runtime.INVENTORY_SHA256
    pin = json.loads(path.read_text())
    scan = json.loads(
        (ROOT / "experiments/manifests/phase5_agent_mount_v1_scan01.json").read_text()
    )
    original = copy.deepcopy(scan)
    admitted = runtime.admit_runtime_scan(scan, pin)
    assert admitted["runtime_files_match"] and not admitted["full_inventory_match"]
    assert admitted["documentation_mismatches"] == ["README.md"]
    assert not admitted["phase5_accepted"] and scan == original


@pytest.mark.parametrize(
    "field,value", [("sha256", "a" * 64), ("size", 6006), ("git_blob_sha1", "a" * 40)]
)
def test_only_exact_document_exception(field: str, value: Any) -> None:
    pin = runtime.read_object(ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json")
    scan = runtime.read_object(ROOT / "experiments/manifests/phase5_agent_mount_v1_scan01.json")
    row = next(r for r in scan["files"] if r["name"] == "README.md")
    row[field] = value
    scan["bytes_hashed"] = sum(r["size"] for r in scan["files"])
    with pytest.raises(ValueError):
        runtime.admit_runtime_scan(scan, pin)


def test_exact_parameter_arithmetic() -> None:
    shapes = runtime.parameter_shapes()
    assert len(shapes) == 339
    assert sum(math.prod(shape) for shape in shapes.values()) == PARAMETERS
    assert shapes["model.layers.27.self_attn.k_proj.weight"] == (512, 3584)


@pytest.fixture
def tiny(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    root = tmp_path / "mount"
    root.mkdir()
    shapes = {f"tensor{i}": (2,) for i in range(4)}
    monkeypatch.setattr(runtime, "parameter_shapes", lambda: shapes)
    index = {"metadata": {"total_size": 16}, "weight_map": {}}
    for i, name in enumerate(sorted(SHARDS)):
        tensor = f"tensor{i}"
        header = json.dumps(
            {tensor: {"dtype": "BF16", "shape": [2], "data_offsets": [0, 4]}}
        ).encode()
        (root / name).write_bytes(struct.pack("<Q", len(header)) + header + b"\0" * 4)
        index["weight_map"][tensor] = name
    for name in REQUIRED | OPTIONAL - SHARDS:
        if name not in SHARDS:
            (root / name).write_text("synthetic")
    (root / "model.safetensors.index.json").write_text(json.dumps(index))
    config = {
        "model_type": "qwen2",
        "architectures": ["Qwen2ForCausalLM"],
        "num_hidden_layers": 28,
        "hidden_size": 3584,
        "intermediate_size": 18944,
        "num_attention_heads": 28,
        "num_key_value_heads": 4,
        "vocab_size": 152064,
        "tie_word_embeddings": False,
        "max_position_embeddings": 32768,
        "use_sliding_window": False,
    }
    (root / "config.json").write_text(json.dumps(config))
    rows = []
    for path in sorted(root.iterdir()):
        data = path.read_bytes()
        rows.append(
            {
                "name": path.name,
                "size": len(data),
                "git_blob_sha1": hashlib.sha1(  # noqa: S324 - synthetic Git fixture
                    b"blob " + str(len(data)).encode() + b"\0" + data
                ).hexdigest(),
                "lfs_sha256": hashlib.sha256(data).hexdigest() if path.name in SHARDS else None,
            }
        )
    pin = tmp_path / "pin.json"
    pin.write_text(json.dumps({"model_id": MODEL, "upstream_revision": REVISION, "files": rows}))
    monkeypatch.setattr(runtime, "INVENTORY_SHA256", hashlib.sha256(pin.read_bytes()).hexdigest())
    return root, pin


def test_live_full_admission_repeatable(tiny: tuple[Path, Path]) -> None:
    root, pin = tiny
    first = runtime.authenticate_runtime(root, pin)
    assert first == runtime.authenticate_runtime(root, pin)
    assert first["full_inventory_match"] and first["parameter_tensors"] == 4
    assert first["serialized_parameter_bytes"] == 16


@pytest.mark.parametrize("name", sorted(REQUIRED | OPTIONAL))
def test_live_all_files_bound(tiny: tuple[Path, Path], name: str) -> None:
    root, pin = tiny
    (root / name).write_bytes(b"tampered")
    with pytest.raises(ValueError):
        runtime.authenticate_runtime(root, pin)


@pytest.mark.parametrize("case", ["pin", "link", "extra", "missing", "optional_absent"])
def test_live_inventory_failures(tiny: tuple[Path, Path], tmp_path: Path, case: str) -> None:
    root, pin = tiny
    if case == "pin":
        pin.write_text(pin.read_text() + " ")
    elif case == "link":
        linked = tmp_path / "linked"
        linked.symlink_to(root, target_is_directory=True)
        root = linked
    elif case == "extra":
        (root / "adapter.py").write_text("unapproved")
    elif case == "missing":
        (root / "config.json").unlink()
    else:
        (root / "README.md").unlink()
        assert runtime.authenticate_runtime(root, pin)["full_inventory_match"]
        return
    with pytest.raises(ValueError):
        runtime.authenticate_runtime(root, pin)


@pytest.mark.parametrize(
    "case",
    [
        "dtype",
        "shape",
        "bool_shape",
        "offset",
        "gap",
        "trailing",
        "truncated",
        "unknown",
        "missing",
        "duplicate_json",
        "huge",
        "short_prefix",
        "metadata",
        "wrong_shard",
        "index_size",
        "index_path",
        "index_missing",
        "index_duplicate",
    ],
)
def test_header_index_rejections(tiny: tuple[Path, Path], case: str) -> None:
    root, _ = tiny
    path = root / sorted(SHARDS)[0]
    header: dict[str, Any] = {"tensor0": {"dtype": "BF16", "shape": [2], "data_offsets": [0, 4]}}
    payload = b"\0" * 4
    if case == "dtype":
        header["tensor0"]["dtype"] = "F32"
    elif case in ("shape", "bool_shape"):
        header["tensor0"]["shape"] = [True] if case == "bool_shape" else [3]
    elif case in ("offset", "gap"):
        header["tensor0"]["data_offsets"] = [0, True] if case == "offset" else [1, 5]
    elif case in ("trailing", "truncated"):
        payload = b"\0" * (5 if case == "trailing" else 3)
    elif case in ("unknown", "wrong_shard"):
        header["other" if case == "unknown" else "tensor1"] = header.pop("tensor0")
    elif case == "missing":
        header = {}
    elif case == "metadata":
        header["__metadata__"] = {"key": 1}
    raw = json.dumps(header).encode()
    if case == "duplicate_json":
        raw = b'{"tensor0":{},"tensor0":{}}'
    path.write_bytes(struct.pack("<Q", len(raw)) + raw + payload)
    if case == "huge":
        path.write_bytes(struct.pack("<Q", runtime.HEADER_LIMIT + 1))
    elif case == "short_prefix":
        path.write_bytes(b"short")
    elif case.startswith("index_"):
        index_path = root / "model.safetensors.index.json"
        index = json.loads(index_path.read_text())
        if case == "index_size":
            index["metadata"]["total_size"] = True
        elif case == "index_path":
            index["weight_map"]["tensor0"] = "../escape"
        elif case == "index_missing":
            del index["weight_map"]["tensor0"]
        index_path.write_text(json.dumps(index) if case != "index_duplicate" else '{"a":1,"a":2}')
    with pytest.raises(ValueError):
        runtime.inspect_tensor_layout(root)
