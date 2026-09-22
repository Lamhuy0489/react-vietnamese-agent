"""Source admission and lazy native dispatch controls; no pretrained execution."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from react_agent.llm import clause_dev_dispatch_v1 as dispatch
from react_agent.validation.clause_dev_release_v1 import admit, digest, safe_name

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def package(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "entry.py").write_text("# synthetic package\n")
    value = dict(
        protocol="clause_dev32_source_v1",
        source_mode="working_tree",
        source_commit=None,
        git_base_commit="a" * 40,
        archive_sha256="b" * 64,
        source_sha256={"entry.py": digest(project / "entry.py")},
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(value))
    return project, manifest, value


def test_working_tree_cpu_and_native_gate(package):
    project, manifest, value = package
    assert admit(project, manifest, digest(manifest), "a" * 40, native=False) == value
    with pytest.raises(ValueError, match="committed source"):
        admit(project, manifest, digest(manifest), "a" * 40, native=True)


def test_committed_admits_exact_bytes(package):
    project, manifest, value = package
    value.update(source_mode="committed", source_commit="a" * 40)
    manifest.write_text(json.dumps(value))
    assert admit(project, manifest, digest(manifest), "a" * 40, native=True) == value


@pytest.mark.parametrize(
    "kind", ["file", "extra", "missing", "manifest", "link", "base", "mode", "field"]
)
def test_tampering_rejected(package, kind):
    project, manifest, value = package
    pin = digest(manifest)
    if kind == "file":
        (project / "entry.py").write_text("changed")
    elif kind == "extra":
        (project / "extra.py").write_text("shadow import")
    elif kind == "missing":
        (project / "entry.py").unlink()
    elif kind == "link":
        (project / "link.py").symlink_to(project / "entry.py")
    elif kind == "manifest":
        manifest.write_text("{}")
    else:
        value.update(
            {{"base": "git_base_commit", "mode": "source_mode", "field": "unexpected"}[kind]: "bad"}
        )
        manifest.write_text(json.dumps(value))
        pin = digest(manifest)
    with pytest.raises(ValueError):
        admit(project, manifest, pin, "a" * 40, native=False)


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/root",
        "a\\b",
        "./entry.py",
        "credential kaggle/a",
        "data/Test/a",
        "data/private/a",
        "tests/a.py",
        "data/pool/a",
    ],
)
def test_private_or_unsafe_paths_rejected(name):
    with pytest.raises(ValueError):
        safe_name(name)


def test_runner_rejects_native_before_dispatch(package, tmp_path, monkeypatch):
    project, manifest, _ = package
    monkeypatch.setattr(dispatch.baseline, "run", lambda *a, **k: pytest.fail("must not dispatch"))
    with pytest.raises(ValueError, match="committed source"):
        dispatch.run(
            tmp_path / "output",
            Path("release"),
            Path("environment"),
            project=project,
            source_manifest=manifest,
            source_sha256=digest(manifest),
            commit="a" * 40,
            backend="hf",
        )
    assert not (tmp_path / "output").exists()


def load(relative):
    spec = importlib.util.spec_from_file_location("dev32_under_test", ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def launcher():
    module = load("notebooks/kaggle/clause_dev32_kernel_v1.py")
    module.SOURCE_MODE = "committed"
    module.SOURCE_COMMIT = "a" * 40
    return module


@pytest.mark.parametrize("mode", ["working_tree", "", "unknown"])
def test_launcher_development_rejected_before_bootstrap(launcher, mode):
    launcher.SOURCE_MODE = mode
    launcher.bootstrap = lambda *a: pytest.fail("must not bootstrap")
    with pytest.raises(ValueError, match="committed release"):
        launcher.main()


def test_launcher_exact_32task_route(launcher, tmp_path):
    mount = tmp_path / "input/qwen2.5/transformers/7b-instruct/1"
    mount.mkdir(parents=True)
    (mount / "config.json").write_text("{}")
    output = tmp_path / "output"
    output.mkdir()
    calls = []
    launcher.native_payload(
        SimpleNamespace(run=lambda *a: calls.append(a)),
        Path("python"),
        Path("project"),
        None,
        Path("guard"),
        Path("snapshot"),
        output,
        tmp_path / "input",
    )
    assert len(calls) == 17
    assert calls[0][4] == "scripts/collect_phase5_tokenizer_metadata.py"
    for shard in range(8):
        run, audit = calls[1 + shard * 2 : 3 + shard * 2]
        assert run[4] == "scripts/run_phase5_clause_dev_native_v1.py"
        assert audit[4] == "scripts/audit_phase5_clause_dev_native_v1.py"
        for call in (run, audit):
            assert call[call.index("--shard") + 1] == str(shard)
            assert call[call.index("--source-sha256") + 1] == digest(
                output / "source_manifest.json"
            )
        assert run[run.index("--backend") + 1] == "hf"
        assert "--resume" not in run and "--condition" not in run


def test_source_manifest_launcher_matches_builder_serialization(launcher, tmp_path):
    from react_agent.llm.agent_mount_v1 import write_receipt

    path = tmp_path / "launcher.json"
    launcher.write_source_manifest(path)
    value = json.loads(path.read_text())
    other = tmp_path / "builder.json"
    write_receipt(other, value)
    assert digest(path) == digest(other)
    with pytest.raises(ValueError, match="fresh"):
        launcher.write_source_manifest(path)


def test_release_validator_rejects_development(package, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    validator = load("scripts/audit_phase5_clause_dev_gpu_v1.py")
    _, manifest, _ = package
    manifest.write_text(json.dumps(dict(valid=True, native_submission_ready=False)))
    with pytest.raises(ValueError, match="accepted release"):
        validator.validate_package(manifest)


def test_native_composition_keeps_observer_config(package, tmp_path, monkeypatch):
    project, manifest, value = package
    value.update(source_mode="committed", source_commit="a" * 40)
    manifest.write_text(json.dumps(value))
    captured = {}

    def binder(function, **bindings):
        captured.update(bindings)
        return lambda *a, **k: {"completed": 0}

    monkeypatch.setattr(dispatch, "bind", binder)
    result = dispatch.run(
        tmp_path / "output",
        Path("release"),
        Path("environment"),
        project=project,
        source_manifest=manifest,
        source_sha256=digest(manifest),
        commit="a" * 40,
        backend="hf",
    )
    assert result["expected"] == 4
    assert captured["run_pair_task"] is dispatch.native_runtime
    assert captured["native_config"]() == dispatch.observer_config(dispatch.native_config())
    assert captured["native_pair"] is dispatch.native_pair


def test_audit_cli_creates_fresh_parent_after_readonly_checks(tmp_path, monkeypatch):
    from react_agent.security_v1.exit_milestones_v1 import runtime_identity

    module = load("scripts/audit_phase5_clause_dev_native_v1.py")
    probe = tmp_path / "probe"
    probe.mkdir()
    saved = {"backend": "stub", "exit_observer": {"runtime": runtime_identity()}}
    (probe / "identity.json").write_text(json.dumps({"run": saved}))
    source = tmp_path / "source.json"
    source.write_text("{}")
    output = tmp_path / "new/audits/shard0.json"
    monkeypatch.setattr(module, "admit", lambda *a, **k: {})
    monkeypatch.setattr(module, "release_identity", lambda *a, **k: (saved, []))
    monkeypatch.setattr(module, "audit_prefix", lambda *a: [{}, {}, {}, {}])
    monkeypatch.setattr(
        "sys.argv",
        [
            "audit",
            "--probe",
            str(probe),
            "--output",
            str(output),
            "--source-manifest",
            str(source),
            "--source-sha256",
            digest(source),
            "--source-commit",
            "a" * 40,
            "--shard",
            "0",
        ],
    )
    before = (probe / "identity.json").read_bytes()
    module.main()
    assert json.loads(output.read_text())["complete"]
    assert (probe / "identity.json").read_bytes() == before
    with pytest.raises(ValueError, match="fresh"):
        module.main()


def test_package_closure_includes_nonimport_identity_pins(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    builder = load("scripts/prepare_phase5_clause_dev_package_v1.py")
    from react_agent.llm.clause_dev_identity_v1 import execution_sources

    explicit = {"src/react_agent/" + name for name in execution_sources()}
    closure = builder.dependency_closure(ROOT, builder.ENTRYPOINTS | explicit)
    assert explicit <= closure
    assert "src/react_agent/validation/constrained_native_audit_v1.py" in closure
    assert not any("private" in p or "/test" in p for p in closure)
