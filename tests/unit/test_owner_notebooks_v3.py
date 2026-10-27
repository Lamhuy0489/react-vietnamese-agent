"""Exports preserve verified script bytes and exclude local discovery secrets."""
import importlib
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return (importlib.import_module("launch_structured_pair_v3"),
            importlib.import_module("export_structured_pair_notebooks_v3"))


@pytest.fixture
def package(tmp_path, monkeypatch, modules):
    builder, exporter = modules
    monkeypatch.setattr(exporter, "ROOT", tmp_path)
    monkeypatch.setattr(exporter, "_check_source_commit", lambda commit: None)
    folder = tmp_path / "build/kaggle/package"
    folder.mkdir(parents=True)
    roles = {}
    for role in ("agent", "guard"):
        member = folder / role
        member.mkdir()
        (member / "worker.py").write_text('print("synthetic")\n')
        builder.save(member / "kernel-metadata.json", {"id": "owner-" + role + "/worker",
            "code_file": "worker.py", "kernel_type": "script", "is_private": True})
        roles[role] = {"kernel": "owner-" + role + "/worker", "code_file": "worker.py",
            "files": {p.name: builder.digest(p) for p in member.iterdir()},
            "cfg": {"model": "synthetic-" + role, "model_source": "synthetic/model/framework/1"}}
    builder.save(folder / "prepared.json", {"source_commit": "a" * 40, "roles": roles})
    (folder / "preflight_v3").mkdir()
    builder.save(folder / "preflight_v3/receipt.json", {
        "prepared_sha256": builder.digest(folder / "prepared.json"), "profile": builder.PROFILE,
        "roles": [{"role": role, "layout": layout} for role in roles
                  for layout in ("code_file_only", "expanded")]})
    (folder / "discovery_private.pem").write_text("SYNTHETIC_SECRET_DO_NOT_SHARE")
    return folder


def test_export_is_exact_and_never_includes_secret(package, modules):
    _, exporter = modules
    result = exporter.export(package)
    assert len(result["roles"]) == 2 and result["submitted"] is False
    for row in result["roles"]:
        notebook = json.loads((exporter.ROOT / row["notebook"]).read_text())
        assert "".join(notebook["cells"][1]["source"]) == 'print("synthetic")\n'
        assert notebook["cells"][1]["outputs"] == []
        with zipfile.ZipFile(exporter.ROOT / row["archive"]) as archive:
            assert len(archive.namelist()) == 3
            assert not any(".pem" in name for name in archive.namelist())
            assert all(b"SYNTHETIC_SECRET_DO_NOT_SHARE" not in archive.read(name)
                       for name in archive.namelist())
    with pytest.raises(ValueError, match="fresh"):
        exporter.export(package)


def test_development_cannot_be_exported_as_frozen(package, modules):
    _, exporter = modules
    path = package / "prepared.json"
    value = json.loads(path.read_text())
    value["source_commit"] = "development"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="source freeze"):
        exporter.export(package)
    assert not (package / "owner_handoff").exists()


def test_tampered_worker_cannot_be_exported(package, modules):
    _, exporter = modules
    (package / "agent/worker.py").write_text("changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        exporter.export(package)
    assert not (package / "owner_handoff").exists()


def test_git_freeze_checks_newline_bytes(tmp_path, monkeypatch, modules):
    builder, _ = modules
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder, "WORKER_FILES", ("worker.py",))
    (tmp_path / "src").mkdir()
    (tmp_path / "src/worker.py").write_bytes(b"source")
    monkeypatch.setattr(builder.subprocess, "check_output", lambda *a, **k: b"source\n")
    with pytest.raises(ValueError, match="does not match"):
        builder._check_source_commit("a" * 40)


def test_invalid_owners_rejected_before_creation(tmp_path, modules):
    builder, _ = modules
    with pytest.raises(ValueError, match="owner names"):
        builder.prepare(tmp_path / "never", "development", owners={"agent": "../escape"})
    assert not (tmp_path / "never").exists()
