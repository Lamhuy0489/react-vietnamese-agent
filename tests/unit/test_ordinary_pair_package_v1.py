"""Ordinary package integrity/routing, with explicit fake native execution."""

import hashlib
import importlib
import json
import subprocess
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def builder(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("prepare_phase5_ordinary_pair")


@pytest.fixture
def wrapper(builder: ModuleType) -> ModuleType:
    return builder.load(ROOT / builder.TEMPLATE)


def test_exact_overlay_and_previous_source_pins(builder: ModuleType, wrapper: ModuleType) -> None:
    prior = builder.check_pins()
    assert len(wrapper.OVERLAY_PATHS) == 56
    assert set(prior["overlay_sha256"]) < wrapper.OVERLAY_PATHS
    for name in wrapper.OVERLAY_PATHS:
        assert (ROOT / name).is_file()
        assert not any(s in name.lower() for s in ("credential", "/private/", "/test", "/pool/"))
    assert "docs/evaluation/tokenizer_config_v1_source.json" not in wrapper.OVERLAY_PATHS
    assert "scripts/run_phase5_ordinary_pair.py" in wrapper.OVERLAY_PATHS


@pytest.mark.parametrize("fault", ["hash", "missing", "extra", "overwrite"])
def test_exact_overlay_mutations(wrapper: ModuleType, tmp_path: Path, fault: str) -> None:
    helper = importlib.import_module("test_policy_native_compat_v1")
    helper.test_overlay_rejects_mutations(wrapper, tmp_path, fault)


@pytest.mark.parametrize("case", ["valid", "dirty_selected", "untracked", "dirty_unrelated"])
def test_selected_git_bytes_required(
    builder: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()  # noqa: S603,S607

    git("init", "-q")
    selected = tmp_path / "selected.py"
    selected.write_text("# public synthetic source\n")
    git("add", "selected.py")
    git(
        "-c",
        "user.name=synthetic",
        "-c",
        "user.email=synthetic@example.invalid",
        "commit",
        "-qm",
        "synthetic fixture",
    )
    commit = git("rev-parse", "HEAD")
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    names = {"selected.py"}
    if case == "dirty_selected":
        selected.write_text("# changed\n")
    elif case == "untracked":
        (tmp_path / "untracked.py").write_text("# untracked\n")
        names.add("untracked.py")
    elif case == "dirty_unrelated":
        (tmp_path / "report.md").write_text("unrelated user report\n")
    if case in ("dirty_selected", "untracked"):
        with pytest.raises((ValueError, subprocess.CalledProcessError)):
            builder.committed_sources(names, commit)
    else:
        assert builder.committed_sources(names, commit) == {
            "selected.py": hashlib.sha256(selected.read_bytes()).hexdigest()
        }


@pytest.mark.parametrize("failure", [None, "collector", "runner", "audit"])
def test_native_payload_order_and_no_retry(
    wrapper: ModuleType,
    tmp_path: Path,
    failure: str | None,
) -> None:
    project, output, inputs = (tmp_path / name for name in ("project", "output", "input"))
    pubs = project / "docs/evaluation/publisher_policy_v1"
    pubs.mkdir(parents=True)
    output.mkdir()
    for role in ("agent", "guard"):
        (pubs / f"{role}_generation_config.json").write_text("{}")
    agent = inputs / "models/qwen-lm/qwen2.5/transformers/7b-instruct/1"
    agent.mkdir(parents=True)
    (agent / "config.json").write_text("{}")
    calls: list[tuple[Any, ...]] = []
    scripts = [
        "scripts/collect_phase5_tokenizer_metadata.py",
        "scripts/run_phase5_ordinary_pair.py",
        "scripts/audit_phase5_ordinary_tokenizer.py",
    ]
    index = {"collector": 0, "runner": 1, "audit": 2}.get(failure)

    def run(*args: Any) -> None:
        calls.append(args)
        if index is not None and args[4] == scripts[index]:
            raise RuntimeError("synthetic failure")

    wrapper.SOURCE_COMMIT = "a" * 40
    arguments = (
        SimpleNamespace(run=run),
        Path("python"),
        project,
        None,
        "b" * 40,
        tmp_path / "guard",
        tmp_path / "snapshot.json",
        output,
        inputs,
    )
    if failure:
        with pytest.raises(RuntimeError, match="synthetic"):
            wrapper.run_payload(*arguments)
        assert len(calls) == index + 1
    else:
        wrapper.run_payload(*arguments)
        assert len(calls) == 3
        assert calls[0][6] == str(agent)
        assert "hf" in calls[1] and str(output / "ordinary_probe") in calls[1]
        assert str(output / "ordinary_native_audit.json") in calls[2]
        assert "a" * 40 in calls[2] and "--agent-pad-token-id" not in calls[2]
    assert [c[4] for c in calls] == scripts[: len(calls)]
    assert all(c[3] == "b" * 40 for c in calls)  # base-runtime identity is not wrapper identity


@pytest.mark.parametrize("count", [0, 2])
def test_requires_unique_mount_before_any_call(
    wrapper: ModuleType, tmp_path: Path, count: int
) -> None:
    for index in range(count):
        root = tmp_path / str(index) / "qwen2.5/transformers/7b-instruct/1"
        root.mkdir(parents=True)
        (root / "config.json").write_text("{}")
    calls: list[Any] = []
    with pytest.raises(ValueError, match="one pinned"):
        wrapper.run_payload(
            SimpleNamespace(run=lambda *args: calls.append(args)),
            Path("python"),
            tmp_path,
            None,
            "a" * 40,
            tmp_path / "guard",
            tmp_path / "snapshot",
            tmp_path,
            tmp_path,
        )
    assert not calls


def test_pinned_dataset_remains_original(builder: ModuleType) -> None:
    prior = builder.check_pins()
    assert prior["bundle_manifest_sha256"] == (
        "b14976413b72898b6c0c1b8c46c1ebb0f62f63633f647ab2064fbc048262240f"
    )
    qa = json.loads((ROOT / builder.TOKENIZER_QA).read_text())
    assert qa["full_suite_passed"] == 2288 and qa["new_gpu_runs"] == 0
