"""Uploaded worker inventory must cover every file without following links."""
import hashlib
import importlib
from pathlib import Path

import pytest


@pytest.fixture
def verify(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("launch_structured_pair_v3")._verify_package


def package(tmp_path):
    folder = tmp_path / "package"
    folder.mkdir()
    (folder / "worker.py").write_text("synthetic worker")
    inventory = {"worker.py": hashlib.sha256(b"synthetic worker").hexdigest()}
    return folder, inventory


def test_exact_inventory_and_tampered_code(tmp_path, verify):
    folder, inventory = package(tmp_path)
    verify(folder, inventory)
    (folder / "worker.py").write_text("changed worker")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify(folder, inventory)


@pytest.mark.parametrize("target", ["worker.py", "missing.py", "."])
def test_extra_symlink_cannot_hide_from_inventory(tmp_path, target, verify):
    folder, inventory = package(tmp_path)
    (folder / "extra").symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        verify(folder, inventory)


@pytest.mark.parametrize("name", ["../worker.py", "/worker.py"])
def test_inventory_cannot_escape_package(tmp_path, name, verify):
    folder, inventory = package(tmp_path)
    with pytest.raises(ValueError, match="unsafe"):
        verify(folder, {name: inventory["worker.py"]})


def test_empty_inventory_and_linked_root_rejected(tmp_path, verify):
    folder, inventory = package(tmp_path)
    with pytest.raises(ValueError, match="empty inventory"):
        verify(folder, {})
    link = tmp_path / "linked-package"
    link.symlink_to(folder, target_is_directory=True)
    with pytest.raises(ValueError, match="invalid package"):
        verify(link, inventory)
