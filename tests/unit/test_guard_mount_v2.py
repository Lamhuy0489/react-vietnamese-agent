"""Bounded handling of Kaggle's materialized Git global PAX header."""

import importlib.util
import tarfile
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture
def kernel() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "notebooks/kaggle/guard_probe_kernel_v2.py"
    spec = importlib.util.spec_from_file_location("guard_mount_v2_qa", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("layout", ["archive", "expanded", "expanded_pax"])
def test_same_executable_bytes(kernel: ModuleType, tmp_path: Path, layout: str) -> None:
    mount = tmp_path / "mount"
    source = tmp_path / "source"
    source.mkdir()
    mount.mkdir()
    (source / "pyproject.toml").write_text("synthetic source")
    expected = {"pyproject.toml": kernel.digest(source / "pyproject.toml")}
    archive = tmp_path / "original.tar.gz"
    with tarfile.open(archive, "w:gz", pax_headers={"comment": "a" * 40}) as stream:
        stream.add(source / "pyproject.toml", arcname="pyproject.toml")
    sha = kernel.digest(archive)
    if layout == "archive":
        archive.rename(mount / "source.tar.gz")
    else:
        kernel.extract(archive, mount / "source", expected)
        if layout == "expanded_pax":
            (mount / "source/pax_global_header").write_text("52 comment=" + "a" * 40 + "\n")
    kernel.materialize(
        mount,
        "source.tar.gz",
        sha,
        "pyproject.toml",
        tmp_path / "out",
        expected,
        source_commit="a" * 40,
    )
    kernel.verify_tree(tmp_path / "out", expected)
    assert not (tmp_path / "out/pax_global_header").exists()
    assert (source / "pyproject.toml").read_bytes() == (
        tmp_path / "out/pyproject.toml"
    ).read_bytes()


@pytest.mark.parametrize(
    "change",
    [
        "changed",
        "wrong_commit",
        "no_commit",
        "bad_commit",
        "link",
        "extra",
        "nested",
        "directory",
        "model",
    ],
)
def test_reject_unbound_extras(kernel: ModuleType, tmp_path: Path, change: str) -> None:
    root = tmp_path / "mount/source"
    root.mkdir(parents=True)
    (root / "pyproject.toml").write_text("synthetic source")
    expected = {"pyproject.toml": kernel.digest(root / "pyproject.toml")}
    header = root / "pax_global_header"
    header.write_text("52 comment=" + "a" * 40 + "\n")
    commit = "a" * 40
    archive = "source.tar.gz"
    if change == "changed":
        header.write_text("arbitrary extra text")
    elif change == "wrong_commit":
        commit = "b" * 40
    elif change == "no_commit":
        commit = ""
    elif change == "bad_commit":
        commit = "z" * 40
    elif change == "link":
        header.rename(tmp_path / "saved")
        header.symlink_to(tmp_path / "saved")
    elif change == "extra":
        (root / "extra.py").write_text("unlisted")
    elif change == "nested":
        (root / "nested").mkdir()
        header.rename(root / "nested/pax_global_header")
    elif change == "directory":
        header.rename(tmp_path / "saved")
        header.mkdir()
    elif change == "model":
        archive = "guard-model.tar"
    with pytest.raises(ValueError):
        kernel.materialize(
            tmp_path / "mount",
            archive,
            "f" * 64,
            "pyproject.toml",
            tmp_path / "out",
            expected,
            source_commit=commit or None,
        )
    assert not (tmp_path / "out").exists()
