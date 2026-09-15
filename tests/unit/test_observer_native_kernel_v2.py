"""Exact launcher routing and embedded source authentication without Kaggle or weights."""

import base64
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def wrapper():
    spec = importlib.util.spec_from_file_location(
        "observer_kernel", ROOT / "notebooks/kaggle/observer_native_kernel_v2.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_route_metadata_runner_audit_in_order(wrapper, tmp_path):
    mount = tmp_path / "qwen2.5/transformers/7b-instruct/1"
    mount.mkdir(parents=True)
    (mount / "config.json").write_text("{}")
    calls = []
    wrapper.native_payload(
        SimpleNamespace(run=lambda *a: calls.append(a)),
        Path("python"),
        Path("project"),
        None,
        Path("guard"),
        Path("snapshot"),
        Path("output"),
        tmp_path,
    )
    assert [c[4] for c in calls] == [
        "scripts/collect_phase5_tokenizer_metadata.py",
        "scripts/run_phase5_guard_observer_v2.py",
        "scripts/audit_phase5_observer_native_v2.py",
    ]
    assert "--shard" not in calls[1] and "--condition" not in calls[1]
    assert calls[1][calls[1].index("--backend") + 1] == "hf"
    assert calls[1][calls[1].index("--output") + 1] == "output/observer"
    assert calls[2][calls[2].index("--probe") + 1] == "output/observer"


def test_missing_mount_stops_before_any_command(wrapper, tmp_path):
    def forbidden(*args):
        raise AssertionError("must not run")

    with pytest.raises(ValueError, match="one pinned"):
        wrapper.native_payload(
            SimpleNamespace(run=forbidden),
            Path("python"),
            Path("project"),
            None,
            Path("guard"),
            Path("snapshot"),
            Path("output"),
            tmp_path,
        )


def test_archive_and_bootstrap_hashes(wrapper, tmp_path):
    payload = b"example archive bytes"
    wrapper.ARCHIVE = base64.b64encode(payload).decode()
    wrapper.ARCHIVE_SHA = hashlib.sha256(payload).hexdigest()
    wrapper.source_archive(tmp_path / "source.tar.gz")
    assert (tmp_path / "source.tar.gz").read_bytes() == payload
    wrapper.ARCHIVE_SHA = "0" * 64
    with pytest.raises(ValueError, match="archive mismatch"):
        wrapper.source_archive(tmp_path / "bad.tar.gz")
    wrapper.BASE_SOURCE = base64.b64encode(b"raise AssertionError('do not execute')").decode()
    wrapper.BASE_SHA = "0" * 64
    with pytest.raises(ValueError, match="bootstrap source mismatch"):
        wrapper.bootstrap(tmp_path)
