"""Constrained launcher and precommit gates without native libraries or weights."""

import base64
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    spec = importlib.util.spec_from_file_location("package_under_test", ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def wrapper():
    module = load("notebooks/kaggle/exit_pair_probe_kernel_v1.py")
    module.SOURCE_MODE = "committed"
    module.SOURCE_COMMIT = "a" * 40
    return module


def invoke(wrapper, root, run):
    wrapper.native_payload(
        SimpleNamespace(run=run), Path("python"), Path("project"), None,
        Path("guard"), Path("snapshot"), Path("output"), root,
    )


def test_native_route(wrapper, tmp_path):
    mount = tmp_path / "qwen2.5/transformers/7b-instruct/1"
    mount.mkdir(parents=True)
    (mount / "config.json").write_text("{}")
    calls = []
    invoke(wrapper, tmp_path, lambda *args: calls.append(args))
    assert [c[4] for c in calls] == [
        "scripts/collect_phase5_tokenizer_metadata.py",
        "scripts/run_phase5_exit_native_probe_v1.py",
        "scripts/audit_phase5_exit_native_probe_v1.py",
    ]
    assert all(c[3] == "a" * 40 for c in calls)
    assert calls[1][calls[1].index("--backend") + 1] == "hf"
    assert calls[1][calls[1].index("--output") + 1] == "output/observer"
    assert calls[2][calls[2].index("--probe") + 1] == "output/observer"
    assert "--shard" not in calls[1] and "--condition" not in calls[1]


@pytest.mark.parametrize("mounts", [0, 2])
def test_ambiguous_or_missing_mount(wrapper, tmp_path, mounts):
    for i in range(mounts):
        mount = tmp_path / str(i) / "qwen2.5/transformers/7b-instruct/1"
        mount.mkdir(parents=True)
        (mount / "config.json").write_text("{}")
    calls = []
    with pytest.raises(ValueError, match="one pinned"):
        invoke(wrapper, tmp_path, lambda *args: calls.append(args))
    assert not calls


@pytest.mark.parametrize("mode", ["working_tree", "__SOURCE_MODE__", "", "other"])
def test_development_blocks_native_and_main_before_side_effects(wrapper, tmp_path, mode):
    wrapper.SOURCE_MODE = mode
    calls = []
    wrapper.bootstrap = lambda *args: calls.append(args)
    with pytest.raises(ValueError, match="committed release required"):
        invoke(wrapper, tmp_path, lambda *args: calls.append(args))
    with pytest.raises(ValueError, match="committed release required"):
        wrapper.main()
    assert not calls


@pytest.mark.parametrize("commit", ["a" * 39, "A" * 40, "z" * 40, ""])
def test_invalid_source_identity(wrapper, commit):
    wrapper.SOURCE_COMMIT = commit
    with pytest.raises(ValueError, match="frozen source required"):
        wrapper.require_committed()


def test_embedded_bytes_authenticated_before_use(wrapper, tmp_path):
    payload = b"archive bytes"
    wrapper.ARCHIVE = base64.b64encode(payload).decode()
    wrapper.ARCHIVE_SHA = hashlib.sha256(payload).hexdigest()
    wrapper.source_archive(tmp_path / "good.tar.gz")
    assert (tmp_path / "good.tar.gz").read_bytes() == payload
    wrapper.ARCHIVE_SHA = "0" * 64
    with pytest.raises(ValueError, match="archive mismatch"):
        wrapper.source_archive(tmp_path / "bad.tar.gz")
    assert not (tmp_path / "bad.tar.gz").exists()
    wrapper.BASE_SOURCE = base64.b64encode(b"raise AssertionError('must not execute')").decode()
    wrapper.BASE_SHA = "0" * 64
    with pytest.raises(ValueError, match="bootstrap source mismatch"):
        wrapper.bootstrap(tmp_path)
    assert not (tmp_path / "bootstrap.py").exists()


@pytest.fixture
def builder(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return load("scripts/prepare_phase5_exit_pair_package_v1.py")


def test_development_hashes_current_bytes(builder, tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    source = tmp_path / "source.py"
    source.write_text("working-tree bytes")
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    assert builder.selected_sources({"source.py"}, "a" * 40, development=True) == {
        "source.py": expected,
    }
    source.write_text("changed")
    assert builder.selected_sources({"source.py"}, "a" * 40, development=True) != {
        "source.py": expected,
    }


def test_release_does_not_fallback_to_working_tree(builder, monkeypatch):
    def reject(names, commit):
        assert names == {"source.py"} and commit == "a" * 40
        raise ValueError("uncommitted selected source")

    monkeypatch.setattr(builder, "committed_sources", reject)
    with pytest.raises(ValueError, match="uncommitted selected source"):
        builder.selected_sources({"source.py"}, "a" * 40, development=False)


def test_development_rejects_linked_sources(builder, tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    (tmp_path / "real.py").write_text("bytes")
    (tmp_path / "source.py").symlink_to(tmp_path / "real.py")
    with pytest.raises(ValueError):
        builder.selected_sources({"source.py"}, "a" * 40, development=True)
