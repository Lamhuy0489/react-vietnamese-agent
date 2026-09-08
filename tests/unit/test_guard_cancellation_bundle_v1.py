"""The new two-file overlay cannot modify the frozen runtime or import memory."""

import base64
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture
def kernel() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "notebooks/kaggle/guard_cancellation_kernel_v1.py"
    spec = importlib.util.spec_from_file_location("cancel_bundle_qa", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("change", ["", "extra", "missing", "hash", "overwrite", "link"])
def test_overlay(kernel: ModuleType, tmp_path: Path, change: str) -> None:
    original = {}
    for name in ("src/react_agent/llm/base.py", "scripts/previous.py"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("frozen bytes")
        original[name] = kernel.digest(path)
    contents = b"synthetic overlay"
    overlay = {
        name: {
            "base64": base64.b64encode(contents).decode(),
            "sha256": hashlib.sha256(contents).hexdigest(),
        }
        for name in kernel.OVERLAY_PATHS
    }
    name = sorted(overlay)[0]
    if change == "extra":
        overlay["knowledge/memory.py"] = overlay[name]
    elif change == "missing":
        overlay.pop(name)
    elif change == "hash":
        overlay[name]["sha256"] = "a" * 64
    elif change == "overwrite":
        (tmp_path / name).write_text("frozen prior source")
        original[name] = kernel.digest(tmp_path / name)
    elif change == "link":
        (tmp_path / name).symlink_to(tmp_path / "scripts/previous.py")
    kernel.OVERLAY = overlay
    if change:
        with pytest.raises(ValueError):
            kernel.install_overlay(tmp_path, original)
    else:
        expanded = kernel.install_overlay(tmp_path, original)
        assert len(expanded) == len(original) + 2
        kernel.verify_tree(tmp_path, expanded)
        assert (tmp_path / name).read_bytes() == contents
        with pytest.raises(ValueError):
            kernel.install_overlay(tmp_path, original)
    assert all(kernel.digest(tmp_path / p) == h for p, h in original.items())
