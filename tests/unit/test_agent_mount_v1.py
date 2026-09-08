"""Tiny synthetic files only; no weights, credentials or benchmark input."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.agent_mount_v1 import (
    MODEL,
    OPTIONAL,
    REQUIRED,
    REVISION,
    SHARDS,
    resolve_mount,
    scan_mount,
    validate_inventory,
)


@pytest.fixture
def sample(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    root = tmp_path / "qwen2.5/transformers/7b-instruct/1"
    root.mkdir(parents=True)
    rows = []
    for name in sorted(REQUIRED | OPTIONAL):
        data = ("synthetic-" + name).encode()
        (root / name).write_bytes(data)
        rows.append(
            {
                "name": name,
                "size": len(data),
                "git_blob_sha1": hashlib.sha1(  # noqa: S324 - synthetic Git blob fixture
                    b"blob " + str(len(data)).encode() + b"\0" + data
                ).hexdigest(),
                "lfs_sha256": hashlib.sha256(data).hexdigest() if name in SHARDS else None,
            }
        )
    return root, {"model_id": MODEL, "upstream_revision": REVISION, "files": rows}


@pytest.mark.parametrize("name", sorted(REQUIRED | OPTIONAL))
def test_tamper(sample: tuple[Path, dict[str, Any]], name: str) -> None:
    root, pin = sample
    assert scan_mount(root, pin)["valid"]
    data = (root / name).read_bytes()
    (root / name).write_bytes(bytes([data[0] ^ 1]) + data[1:])
    result = scan_mount(root, pin)
    assert not result["valid"]
    assert [r["name"] for r in result["files"] if not r["publisher_match"]] == [name]


@pytest.mark.parametrize("kind", ["missing", "optional", "extra", "link", "directory", "root_link"])
def test_inventory(sample: tuple[Path, dict[str, Any]], kind: str, tmp_path: Path) -> None:
    root, pin = sample
    if kind in {"missing", "optional"}:
        (root / ("config.json" if kind == "missing" else "README.md")).unlink()
    elif kind == "extra":
        (root / "unexpected.py").write_text("synthetic")
    elif kind == "link":
        (root / "link").symlink_to(root / "config.json")
    elif kind == "directory":
        (root / "nested").mkdir()
    else:
        link = tmp_path / "linked"
        link.symlink_to(root, target_is_directory=True)
        root = link
    if kind in {"link", "directory", "root_link"}:
        with pytest.raises(ValueError):
            scan_mount(root, pin)
    else:
        assert scan_mount(root, pin)["valid"] is (kind == "optional")


@pytest.mark.parametrize("kind", ["duplicate", "path", "size", "sha", "model", "revision"])
def test_bad_pin(sample: tuple[Path, dict[str, Any]], kind: str) -> None:
    _, pin = sample
    if kind == "duplicate":
        pin["files"].append(pin["files"][0])
    elif kind == "path":
        pin["files"][0]["name"] = "../escape"
    elif kind == "size":
        pin["files"][0]["size"] = True
    elif kind == "sha":
        pin["files"][0]["git_blob_sha1"] = "bad"
    else:
        pin["model_id" if kind == "model" else "upstream_revision"] = "other"
    with pytest.raises(ValueError):
        validate_inventory(pin)


@pytest.mark.parametrize("nested,corrupt", [(False, False), (True, False), (True, True)])
def test_exact_standalone(
    sample: tuple[Path, dict[str, Any]], tmp_path: Path, nested: bool, corrupt: bool
) -> None:
    root, pin = sample
    project = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "mount_packager", project / "scripts/prepare_phase5_agent_mount.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = (project / "src/react_agent/llm/agent_mount_v1.py").read_text()
    if nested:
        target = tmp_path / "models/provider"
        target.mkdir(parents=True)
        (tmp_path / "qwen2.5").rename(target / "qwen2.5")
        root = target / "qwen2.5/transformers/7b-instruct/1"
    assert resolve_mount(tmp_path) == root
    if corrupt:
        (root / "config.json").write_text("modified")
    kernel = tmp_path / "kernel.py"
    kernel.write_text(module.render(source, pin, "a" * 40, "b" * 64))
    output = tmp_path / "receipt.json"
    run = subprocess.run(  # noqa: S603 - own rendered source and synthetic temp paths
        [sys.executable, "-I", str(kernel), "--input-root", str(tmp_path), "--output", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == (1 if corrupt else 0), run.stderr
    result = json.loads(output.read_text())
    assert result["valid"] is not corrupt
    assert result["model_loads"] == 0 and not result["gpu_used"]
    assert result["identity"]["verifier_sha256"] == hashlib.sha256(source.encode()).hexdigest()
