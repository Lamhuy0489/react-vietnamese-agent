"""Lazy topology and actual daemon-spawn synthetic request composition."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import pickle
import subprocess
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace as NS
from typing import Any

import pytest

from react_agent.llm import request_pair_v1 as impl
from react_agent.llm.base import GenerationConfig
from react_agent.llm.efficient_requests_v1 import EfficientRequestFactory
from react_agent.llm.model_pair_v1 import PairConfig, ReadyFactory
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory

ROOT = Path(__file__).resolve().parents[2]


def forbidden_load() -> Any:
    raise AssertionError("planning must not load models")


def config() -> PairConfig:
    return PairConfig(
        impl.ModelIdentity(impl.MODEL, impl.AGENT_REVISION),
        impl.ModelIdentity(impl.MODEL_ID, impl.GUARD_REVISION),
    )


def test_lazy_exact_composition_and_pickle(tmp_path: Path) -> None:
    root = tmp_path / "attention"
    pair = impl.request_pair(forbidden_load, forbidden_load, config(), root)
    try:
        assert pair.state == "NEW" and not root.exists()
        assert pair.config == config()
        for role, worker in pair._workers.items():
            ready = worker.factory
            assert type(ready) is ReadyFactory
            progress = ready.factory
            assert type(progress) is ThreadProgressFactory
            attention = progress.factory
            assert type(attention) is EfficientRequestFactory
            assert attention.native_factory is forbidden_load and attention.role == role
            assert attention.output == root / role
            assert pickle.loads(pickle.dumps(ready)) == ready  # noqa: S301 — self-created factory
            assert not worker.attempts
    finally:
        pair.close()


@pytest.mark.parametrize("side", ["agent", "guard"])
@pytest.mark.parametrize("wrapper", ["ready", "progress", "attention", "noncallable"])
def test_refuse_prewrapped_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, side: str, wrapper: str
) -> None:
    factories: dict[str, Any] = dict(agent=forbidden_load, guard=forbidden_load)
    factories[side] = {
        "ready": ReadyFactory(forbidden_load),
        "progress": ThreadProgressFactory(forbidden_load),
        "attention": EfficientRequestFactory(forbidden_load, "agent", tmp_path / "other"),
        "noncallable": None,
    }[wrapper]
    monkeypatch.setattr(impl, "ModelPair", lambda *a: forbidden_load())
    with pytest.raises(ValueError, match="unwrapped"):
        impl.request_pair(factories["agent"], factories["guard"], config(), tmp_path / "out")


@pytest.mark.parametrize("side", ["agent", "guard"])
def test_wrong_identity_before_pair_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, side: str
) -> None:
    values = dict(agent=config().agent, guard=config().guard)
    values[side] = impl.ModelIdentity("wrong", "wrong")
    monkeypatch.setattr(impl, "ModelPair", lambda *a: forbidden_load())
    with pytest.raises(ValueError, match="identities"):
        impl.request_pair(forbidden_load, forbidden_load, PairConfig(**values), tmp_path / "out")


@pytest.mark.parametrize("mode", ["existing", "symlink", "parent_symlink"])
def test_path_refusal(tmp_path: Path, mode: str) -> None:
    real = tmp_path / "real"
    real.mkdir()
    out = real
    if mode != "existing":
        link = tmp_path / "link"
        link.symlink_to(real, target_is_directory=True)
        out = link if mode == "symlink" else link / "child"
    with pytest.raises(ValueError):
        impl.request_pair(forbidden_load, forbidden_load, config(), out)


def test_ready_bypasses_adapter_and_progress_precedes_native(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    import react_agent.llm.worker_progress_v1 as progress
    from react_agent.llm.model_pair_v1 import READY_ACK, READY_COMMAND

    monkeypatch.setattr(progress, "configure_worker_progress", lambda: events.append("progress"))

    def native() -> Any:
        assert events == ["progress"]
        events.append("native")
        return NS(model_id="fake", model_revision="v1")

    # Factory exact-native admission is independently covered; replace only that
    # boundary for this ordering control, not production factory or transport.
    def attention(factory: Any, role: str, output: Path) -> Any:
        def create() -> Any:
            value = factory()
            value.generate = lambda *a: forbidden_load()
            return value

        return create

    monkeypatch.setattr(
        impl,
        "EfficientRequestFactory",
        type("Factory", (), {"__new__": staticmethod(lambda cls, *a: attention(*a))}),
    )
    pair = impl.request_pair(native, native, config(), tmp_path / "attention")
    try:
        ready = pair._workers["agent"].factory()
        assert (
            ready.generate([dict(role="user", content=READY_COMMAND)], GenerationConfig()).text
            == READY_ACK
        )
        assert events == ["progress", "native"]
    finally:
        pair.close()


def test_rehearsal_native_tqdm_real_spawn(tmp_path: Path) -> None:
    wheel = ROOT / "build/kaggle/worker_progress_v1_wheels/tqdm-4.67.3-py3-none-any.whl"
    if not wheel.is_file():
        pytest.skip("optional cached pinned tqdm wheel; selected standalone rehearsal required")
    assert hashlib.sha256(wheel.read_bytes()).hexdigest() == (
        "ee1e4c0e59148062281c49d80b25b67771a127c85fc9676d3be5f243206826bf"
    )
    dependency = tmp_path / "dependency"
    # Authenticate the cached wheel before extracting only safe package members.
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith(("tqdm/", "tqdm-4.67.3.dist-info/")):
                assert ".." not in Path(name).parts and not Path(name).is_absolute()
                archive.extract(name, dependency)
    output = tmp_path / "rehearsal"
    env = os.environ | {"PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(dependency)))}
    command = [
        sys.executable,
        str(ROOT / "scripts/check_phase5_request_pair.py"),
        "--output",
        str(output),
    ]
    result = subprocess.run(  # noqa: S603 — fixed local CLI and pytest-owned paths
        command, env=env, capture_output=True, text=True, timeout=90, check=False
    )
    assert result.returncode == 0, result.stderr
    value = json.loads((output / "summary.json").read_text())
    assert value["valid"] and value["synthetic"] and not value["phase5_accepted"]
    assert value["native_model_calls"] == value["model_loads"] == value["gpu_runs"] == 0
    assert len(set(value["worker_pids"])) == 7
    assert [r["case"] for r in value["rows"]] == [
        "success",
        "reversed",
        "agent_error",
        "guard_error",
    ]
    for role in ("agent", "guard"):
        rows = value["rows"][0]["audits"][role]["requests"]
        assert [r["input_tokens"] for r in rows] == [1, 4096, 1]
        assert [r["output_tokens"] for r in rows] == [1, 3, 1]
    prior = (output / "summary.json").read_bytes()
    refused = subprocess.run(  # noqa: S603 — same fixed local CLI
        command, env=env, capture_output=True, text=True, timeout=10, check=False
    )
    assert refused.returncode != 0 and (output / "summary.json").read_bytes() == prior


def test_synthetic_factory_refuses_owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = importlib.import_module("check_phase5_request_pair")
    with pytest.raises(ValueError, match="daemon spawn"):
        module.SyntheticNativeFactory("agent", tmp_path)()
    assert list(tmp_path.iterdir()) == []
