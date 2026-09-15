"""Synthetic metadata boundary tests; no native library/model claims."""

import hashlib
import importlib.util
import io
import json
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from react_agent.llm import guard_language_native_v1 as native
from react_agent.llm.guard_snapshot_v1 import CANDIDATE_REVISION, GuardSnapshot, SnapshotFile

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    folder = tmp_path / "bundle"
    folder.mkdir()
    content = {name: b"synthetic" for name in native.FILES}
    content.update(
        {
            "model.safetensors": b"never read these synthetic weights",
            "config.json": b'{"model_type":"qwen2","vocab_size":100}',
            "tokenizer_config.json": b"{}",
            "generation_config.json": b'{"eos_token_id":[2,1]}',
        }
    )
    pin = GuardSnapshot(
        upstream_revision=CANDIDATE_REVISION,
        files=tuple(
            SnapshotFile(name=n, size=len(b), sha256=hashlib.sha256(b).hexdigest())
            for n, b in sorted(content.items())
        ),
    )
    manifest = folder / "guard_bundle.json"
    manifest.write_text(json.dumps(dict(snapshot=pin.model_dump(mode="json"))))
    monkeypatch.setattr(native, "BUNDLE_SHA", native.digest(manifest))
    with tarfile.open(folder / "guard-model.tar", "w") as stream:
        for name, data in content.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            stream.addfile(member, io.BytesIO(data))
    return folder, content


def test_archive_and_expanded_subset_no_weight_read(bundle, tmp_path, monkeypatch):
    folder, content = bundle
    reads = []
    original = tarfile.TarFile.extractfile

    def observe(self, member):
        reads.append(member.name)
        return original(self, member)

    monkeypatch.setattr(tarfile.TarFile, "extractfile", observe)
    first = native.metadata(folder, tmp_path / "first")
    assert set(reads) == native.FILES and not first["model_weights_read"]
    (folder / "guard-model.tar").rename(tmp_path / "retained.tar")
    expanded = folder / "expanded"
    expanded.mkdir()
    for name in native.FILES:
        (expanded / name).write_bytes(content[name])
    second = native.metadata(folder, tmp_path / "second")
    assert first == second and set(p.name for p in (tmp_path / "first").iterdir()) == native.FILES


@pytest.mark.parametrize("fault", ["hash", "missing", "duplicate", "symlink", "manifest", "output"])
def test_admission_rejects_mutations(bundle, tmp_path, fault):
    folder, content = bundle
    target = tmp_path / "output"
    if fault == "manifest":
        (folder / "guard_bundle.json").write_text("{}")
    elif fault == "output":
        target.mkdir()
    else:
        with tarfile.open(folder / "guard-model.tar", "w") as stream:
            for name, data in content.items():
                if fault == "missing" and name == "tokenizer.json":
                    continue
                if fault == "hash" and name == "tokenizer.json":
                    data = b"X" * len(data)
                member = tarfile.TarInfo(name)
                member.size = len(data)
                if fault == "symlink" and name == "tokenizer.json":
                    member.type, member.linkname, member.size = tarfile.SYMTYPE, "outside", 0
                stream.addfile(member, io.BytesIO(data))
                if fault == "duplicate" and name == "tokenizer.json":
                    stream.addfile(member, io.BytesIO(data))
    with pytest.raises(ValueError):
        native.metadata(folder, target)


def test_wrapper_invocation_uses_native_by_default_and_marks_rehearsal():
    path = ROOT / "notebooks/kaggle/guard_language_cpu_kernel_v1.py"
    spec = importlib.util.spec_from_file_location("language_wrapper", path)
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    calls = []
    base = SimpleNamespace(run=lambda *args: calls.append(args))
    args = (base, Path("python"), Path("project"), None, Path("bundle"), Path("out"))
    wrapper.payload(*args)
    wrapper.payload(*args, metadata_only=True)
    assert "--metadata-only" not in calls[0] and calls[1][-1] == "--metadata-only"
    assert "--source-commit" in calls[0] and "--bundle" in calls[0]
    assert "model_sources" not in calls[0]
