"""Exact overlay/bootstrap guards with tiny local fixtures; never actual weights."""

import base64
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("fixture_kernel", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def bundle(tmp_path: Path) -> tuple[Any, Any, Path, dict[str, str]]:
    wrapper = load(ROOT / "notebooks/kaggle/pair_cancel_kernel_v1.py")
    source = (ROOT / "notebooks/kaggle/guard_cancellation_kernel_v1.py").read_bytes()
    wrapper.BASE64_SOURCE = base64.b64encode(source).decode()
    wrapper.BASE_SHA256 = hashlib.sha256(source).hexdigest()
    base = wrapper.load_base(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    (project / "keep.txt").write_text("frozen")
    original = {"keep.txt": hashlib.sha256(b"frozen").hexdigest()}
    wrapper.OVERLAY = {
        name: {
            "base64": base64.b64encode(b"fixture").decode(),
            "sha256": hashlib.sha256(b"fixture").hexdigest(),
        }
        for name in wrapper.OVERLAY_PATHS
    }
    return wrapper, base, project, original


def test_exact_overlay_creates_only_allowed_files(bundle: Any) -> None:
    wrapper, base, project, original = bundle
    expanded = wrapper.install_overlay(base, project, original)
    assert len(expanded) == 14
    base.verify_tree(project, expanded)
    assert (project / "keep.txt").read_text() == "frozen"


@pytest.mark.parametrize("case", ["missing", "extra", "hash", "base64", "overwrite", "link"])
def test_overlay_rejection(bundle: Any, case: str) -> None:
    wrapper, base, project, original = bundle
    name = sorted(wrapper.OVERLAY)[0]
    if case == "missing":
        del wrapper.OVERLAY[name]
    elif case == "extra":
        wrapper.OVERLAY["extra"] = wrapper.OVERLAY[name]
    elif case in ("hash", "base64"):
        wrapper.OVERLAY[name]["sha256" if case == "hash" else "base64"] = "bad"
    elif case == "overwrite":
        wrapper.OVERLAY_PATHS = {"keep.txt"}
        wrapper.OVERLAY = {"keep.txt": wrapper.OVERLAY[name]}
    else:
        (project / "linked").symlink_to(project / "keep.txt")
    with pytest.raises(ValueError):
        wrapper.install_overlay(base, project, original)


def test_base_hash_rejection(tmp_path: Path) -> None:
    wrapper = load(ROOT / "notebooks/kaggle/pair_cancel_kernel_v1.py")
    wrapper.BASE64_SOURCE = base64.b64encode(b"raise RuntimeError('must not import')").decode()
    wrapper.BASE_SHA256 = "0" * 64
    with pytest.raises(ValueError, match="bootstrap source mismatch"):
        wrapper.load_base(tmp_path)
    assert not list(tmp_path.iterdir())
