"""Exact inventory, extraction, manifest and isolated-process bootstrap checks."""

import importlib.util
import io
import json
import tarfile
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


@pytest.fixture
def kernel() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "notebooks/kaggle/guard_probe_kernel.py"
    spec = importlib.util.spec_from_file_location("kernel_for_guard_qa", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "name",
    [
        "../file",
        "/absolute/file",
        "a/../b",
        "a//b",
        "a\\b",
        "",
        ".",
        "data/private/gt.json",
        "data/pool/a",
        "data/reviews/a",
        "data/test.jsonl",
        "credential kaggle/key",
        "C:/file",
    ],
)
def test_bad_paths(kernel: ModuleType, name: str) -> None:
    with pytest.raises(ValueError):
        kernel.relative_name(name)


@pytest.mark.parametrize("change", ["extra_file", "extra_dir", "symlink", "changed", "missing"])
def test_exact_tree(kernel: ModuleType, tmp_path: Path, change: str) -> None:
    root = tmp_path / "source"
    root.mkdir()
    file = root / "module.py"
    file.write_text("synthetic source")
    expected = {file.name: kernel.digest(file)}
    kernel.verify_tree(root, expected)
    if change == "extra_file":
        (root / "extra.py").write_text("extra")
    elif change == "extra_dir":
        (root / "extra").mkdir()
    elif change == "symlink":
        (root / "link").symlink_to(file)
    elif change == "changed":
        file.write_text("changed")
    else:
        file.rename(tmp_path / "moved")
    with pytest.raises(ValueError):
        kernel.verify_tree(root, expected)


@pytest.mark.parametrize("change", ["traversal", "link", "duplicate", "extra", "empty_dir"])
def test_unsafe_tar(kernel: ModuleType, tmp_path: Path, change: str) -> None:
    archive = tmp_path / "source.tar"
    with tarfile.open(archive, "w") as stream:
        first = tarfile.TarInfo("module.py")
        first.size = 1
        stream.addfile(first, io.BytesIO(b"x"))
        item = tarfile.TarInfo(
            {"traversal": "../outside", "duplicate": "module.py"}.get(change, "extra")
        )
        if change == "link":
            item.type = tarfile.SYMTYPE
            item.linkname = "module.py"
        if change == "empty_dir":
            item.type = tarfile.DIRTYPE
        stream.addfile(item)
    with pytest.raises(ValueError):
        kernel.extract(archive, tmp_path / "unpack", {"module.py": "a" * 64})
    assert not (tmp_path / "outside").exists()


def test_archive_and_expanded_equivalence(kernel: ModuleType, tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "pyproject.toml").write_text("synthetic marker")
    expected = {"pyproject.toml": kernel.digest(source / "pyproject.toml")}
    mount = tmp_path / "mount"
    mount.mkdir()
    archive = mount / "source.tar"
    with tarfile.open(archive, "w") as stream:
        stream.add(source / "pyproject.toml", arcname="pyproject.toml")
    archive_hash = kernel.digest(archive)
    kernel.materialize(
        mount, archive.name, archive_hash, "pyproject.toml", tmp_path / "out1", expected
    )
    archive.rename(tmp_path / "saved.tar")
    kernel.extract(tmp_path / "saved.tar", mount / "generated", expected)
    kernel.materialize(
        mount, archive.name, archive_hash, "pyproject.toml", tmp_path / "out2", expected
    )
    assert (tmp_path / "out1/pyproject.toml").read_bytes() == (
        tmp_path / "out2/pyproject.toml"
    ).read_bytes()


def test_manifest_binding(kernel: ModuleType, tmp_path: Path) -> None:
    path = tmp_path / "guard_bundle.json"
    path.write_text(json.dumps({"source": "synthetic"}))
    digest = kernel.digest(path)
    assert kernel.manifest(tmp_path, digest)[1] == {"source": "synthetic"}
    with pytest.raises(ValueError):
        kernel.manifest(tmp_path, "a" * 64)
    (tmp_path / "duplicate").mkdir()
    (tmp_path / "duplicate/guard_bundle.json").write_text(path.read_text())
    with pytest.raises(ValueError):
        kernel.manifest(tmp_path, digest)


def test_frozen_import_environment(
    kernel: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def record(*args: Any, **kwargs: Any) -> None:
        calls.append((args, kwargs))

    monkeypatch.setenv("PYTHONPATH", "/unwanted-development-import")
    monkeypatch.setenv("VIRTUAL_ENV", "/unwanted-development-venv")
    monkeypatch.setattr(kernel.subprocess, "run", record)
    kernel.run(tmp_path / "python", tmp_path / "project", None, "a" * 40, "script.py")
    environment = calls[0][1]["env"]
    assert environment["PYTHONPATH"] == str(tmp_path / "project/src")
    assert "VIRTUAL_ENV" not in environment
    assert environment["PYTHONNOUSERSITE"] == "1"
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert environment["HF_HUB_OFFLINE"] == "1"
