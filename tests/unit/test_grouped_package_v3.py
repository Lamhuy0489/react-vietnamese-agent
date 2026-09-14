"""Regression coverage for the incomplete-overlay/editable-import false positive."""

import hashlib
import importlib
import io
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def builder(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("prepare_phase5_grouped_package_v3")


def test_closure_includes_lazy_imports_and_excludes_pool_initializer(builder):
    names = builder.dependency_closure(ROOT, builder.ENTRYPOINTS)
    assert "src/react_agent/__init__.py" in names
    assert "src/react_agent/llm/grouped_dev_runner_v2.py" in names
    assert "src/react_agent/security_v1/sql_pair_runtime_v1.py" in names
    assert "src/react_agent/llm/native_agent_only_v1.py" in names
    assert "src/react_agent/validation/grouped_dev_native_audit_v2.py" in names
    assert "src/react_agent/validation/__init__.py" not in names
    assert not any("clean_pool" in n or "/private/" in n for n in names)


@pytest.mark.parametrize("layout", ["archive", "expanded"])
def test_roundtrip_uses_exact_root_and_hashes(builder, tmp_path, layout):
    root, mount, target = (tmp_path / n for n in ("root", "mount", "target"))
    (root / "configs").mkdir(parents=True)
    (root / "configs/first.yaml").write_text("first")
    (root / "pyproject.toml").write_text("project")
    files = builder.file_hashes(root)
    archive = tmp_path / "input.tar.gz"
    builder.make_archive(root, files, archive)
    second = tmp_path / "second.tar.gz"
    builder.make_archive(root, files, second)
    assert archive.read_bytes() == second.read_bytes()
    base = builder.load(ROOT / builder.BASE)
    mount.mkdir()
    if layout == "archive":
        (mount / "source.tar.gz").write_bytes(archive.read_bytes())
    else:
        base.extract(archive, mount / "generated/source", files)
    base.materialize(
        mount, "source.tar.gz", builder.digest(archive), "pyproject.toml", target, files
    )
    assert builder.file_hashes(target) == files
    assert (target / "pyproject.toml").is_file()
    (target / "unexpected").write_text("extra")
    with pytest.raises(ValueError, match="inventory"):
        base.verify_tree(target, files)


@pytest.mark.parametrize("fault", ["traversal", "symlink", "hardlink", "private", "duplicate"])
def test_unsafe_archive_rejected_before_extraction(builder, tmp_path, fault):
    archive = tmp_path / "bad.tar"
    name = {"traversal": "../escape", "private": "data/private/gt.json"}.get(fault, "safe")
    member = tarfile.TarInfo(name)
    member.size = 1
    if fault in {"symlink", "hardlink"}:
        member.type = tarfile.SYMTYPE if fault == "symlink" else tarfile.LNKTYPE
        member.linkname = "../escape"
        member.size = 0
    with tarfile.open(archive, "w") as stream:
        stream.addfile(member, io.BytesIO(b"x"))
        if fault == "duplicate":
            stream.addfile(member, io.BytesIO(b"x"))
    base = builder.load(ROOT / builder.BASE)
    with pytest.raises(ValueError):
        base.extract(archive, tmp_path / "result", {"safe": hashlib.sha256(b"x").hexdigest()})
    assert not (tmp_path / "result").exists()


def test_origin_check_rejects_development_fallback(builder, tmp_path):
    checker = importlib.import_module("check_phase5_grouped_package_v3")
    # Same root error as v2: a configs subtree with no actual complete package.
    with pytest.raises(ValueError, match="development import leaked"):
        checker.module_origins(tmp_path / "expanded/configs")
    origins = checker.module_origins(ROOT)
    assert origins["react_agent"] == "src/react_agent/__init__.py"


def test_origin_check_rejects_foreign_namespace(builder, tmp_path, monkeypatch):
    checker = importlib.import_module("check_phase5_grouped_package_v3")
    monkeypatch.setitem(
        sys.modules, "react_agent.foreign", SimpleNamespace(__file__=None, __path__=[str(tmp_path)])
    )
    with pytest.raises(ValueError, match="development import leaked"):
        checker.module_origins(ROOT)


@pytest.mark.parametrize("failure", [None, 0, 1, 2])
def test_native_dispatch_is_shard_bound_and_never_retries(builder, tmp_path, failure):
    wrapper = builder.load(ROOT / builder.TEMPLATE)
    wrapper.SOURCE_COMMIT, wrapper.SHARD = "a" * 40, 3
    inputs = tmp_path / "input"
    agent = inputs / "qwen2.5/transformers/7b-instruct/1"
    agent.mkdir(parents=True)
    (agent / "config.json").write_text("{}")
    seen = []

    def run(*args):
        assert args[3] == "a" * 40
        seen.append(args[4:])
        if len(seen) - 1 == failure:
            raise RuntimeError("synthetic infrastructure failure")

    args = (
        SimpleNamespace(run=run),
        Path("python"),
        tmp_path / "project",
        None,
        tmp_path / "guard",
        tmp_path / "snapshot",
        tmp_path / "output",
        inputs,
    )
    if failure is not None:
        with pytest.raises(RuntimeError):
            wrapper.native_payload(*args)
        assert len(seen) == failure + 1
    else:
        wrapper.native_payload(*args)
        assert len(seen) == 3
        assert seen[1][0] == "scripts/run_phase5_grouped_dev.py"
        for command in seen[1:]:
            assert command[command.index("--shard") + 1] == "3"
        assert "--resume" not in seen[1]
