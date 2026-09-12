"""Policy/attention worker topology and bounded real-spawn CPU controls."""

import hashlib
import importlib
import json
import os
import pickle
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest
from test_request_pair_v1 import config, forbidden_load

from react_agent.llm import request_policy_pair_v1 as impl
from react_agent.llm.efficient_requests_v1 import EfficientRequestFactory
from react_agent.llm.model_pair_v1 import PairConfig, ReadyFactory
from react_agent.llm.request_policy_v1 import RequestPolicyFactory
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory

ROOT = Path(__file__).resolve().parents[2]


def test_lazy_topology_and_pickle(tmp_path: Path) -> None:
    policy, attention = tmp_path / "policy", tmp_path / "attention"
    pair = impl.policy_pair(forbidden_load, forbidden_load, config(), attention, policy)
    try:
        assert pair.state == "NEW" and pair.config == config()
        assert not policy.exists() and not attention.exists()
        for role, worker in pair._workers.items():
            ready = worker.factory
            assert type(ready) is ReadyFactory
            progress = ready.factory
            assert type(progress) is ThreadProgressFactory
            observer = progress.factory
            assert type(observer) is RequestPolicyFactory
            assert observer.output == policy / role
            adapter = observer.attention
            assert type(adapter) is EfficientRequestFactory
            assert adapter.role == role and adapter.output == attention / role
            assert adapter.native_factory is forbidden_load
            assert pickle.loads(pickle.dumps(ready)) == ready  # noqa: S301 — self-created data
            assert not worker.attempts
    finally:
        pair.close()


@pytest.mark.parametrize("side", ["agent", "guard"])
@pytest.mark.parametrize("kind", ["ready", "progress", "attention", "policy", "noncallable"])
def test_prewrapped_refusal_before_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, side: str, kind: str
) -> None:
    raw: dict[str, Any] = dict(agent=forbidden_load, guard=forbidden_load)
    adapter = EfficientRequestFactory(forbidden_load, "agent", tmp_path / "a")
    raw[side] = dict(
        ready=ReadyFactory(forbidden_load),
        progress=ThreadProgressFactory(forbidden_load),
        attention=adapter,
        policy=RequestPolicyFactory(adapter, tmp_path / "p"),
        noncallable=None,
    )[kind]
    monkeypatch.setattr(impl, "ModelPair", lambda *a: forbidden_load())
    with pytest.raises(ValueError, match="unwrapped"):
        impl.policy_pair(
            raw["agent"], raw["guard"], config(), tmp_path / "attention", tmp_path / "policy"
        )


@pytest.mark.parametrize("side", ["agent", "guard"])
def test_identity_refusal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, side: str) -> None:
    identities = dict(agent=config().agent, guard=config().guard)
    identities[side] = impl.ModelIdentity("different", "different")
    monkeypatch.setattr(impl, "ModelPair", lambda *a: forbidden_load())
    with pytest.raises(ValueError, match="identities"):
        impl.policy_pair(
            forbidden_load,
            forbidden_load,
            PairConfig(**identities),
            tmp_path / "attention",
            tmp_path / "policy",
        )


@pytest.mark.parametrize(
    "case",
    [
        "same",
        "nested_policy",
        "nested_attention",
        "existing_policy",
        "existing_attention",
        "symlink",
    ],
)
def test_fresh_disjoint_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str) -> None:
    attention, policy = tmp_path / "attention", tmp_path / "policy"
    if case == "same":
        policy = attention
    elif case == "nested_policy":
        policy = attention / "policy"
    elif case == "nested_attention":
        attention = policy / "attention"
    elif case == "existing_policy":
        policy.mkdir()
    elif case == "existing_attention":
        attention.mkdir()
    elif case == "symlink":
        link = tmp_path / "linked"
        link.symlink_to(tmp_path, target_is_directory=True)
        attention = link / "attention"
    monkeypatch.setattr(impl, "ModelPair", lambda *a: forbidden_load())
    with pytest.raises(ValueError):
        impl.policy_pair(forbidden_load, forbidden_load, config(), attention, policy)


@pytest.mark.parametrize("error", [RuntimeError, KeyboardInterrupt])
def test_harness_substitution_restored_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Any
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    harness = importlib.import_module("check_phase5_request_policy_pair")
    original = harness.base.request_pair

    def fail(root: Path) -> Any:
        assert harness.base.request_pair is harness.composed
        raise error("synthetic")

    monkeypatch.setattr(harness.base, "run", fail)
    with pytest.raises(error):
        harness.run(tmp_path / "new")
    assert harness.base.request_pair is original


def test_synthetic_factory_refuses_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    harness = importlib.import_module("check_phase5_request_policy_pair")
    factory = harness.SyntheticPolicyFactory(harness.base.SyntheticNativeFactory("agent", tmp_path))
    with pytest.raises(ValueError, match="daemon spawn"):
        factory()
    assert not list(tmp_path.iterdir())


def test_native_progress_real_spawn(tmp_path: Path) -> None:
    wheel = ROOT / "build/kaggle/worker_progress_v1_wheels/tqdm-4.67.3-py3-none-any.whl"
    if not wheel.is_file():
        pytest.skip("optional cached pinned tqdm wheel; selected standalone rehearsal required")
    assert hashlib.sha256(wheel.read_bytes()).hexdigest() == (
        "ee1e4c0e59148062281c49d80b25b67771a127c85fc9676d3be5f243206826bf"
    )
    dependency = tmp_path / "dependency"
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith(("tqdm/", "tqdm-4.67.3.dist-info/")):
                assert ".." not in Path(name).parts and not Path(name).is_absolute()
                archive.extract(name, dependency)
    output = tmp_path / "rehearsal"
    env = os.environ | {"PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(dependency)))}
    command = [
        sys.executable,
        str(ROOT / "scripts/check_phase5_request_policy_pair.py"),
        "--output",
        str(output),
    ]
    result = subprocess.run(  # noqa: S603 — fixed local CLI and test-owned paths
        command, env=env, capture_output=True, text=True, timeout=90, check=False
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads((output / "summary.json").read_text())
    assert receipt["valid"] and receipt["synthetic"] and not receipt["phase5_accepted"]
    assert receipt["model_loads"] == receipt["native_model_calls"] == receipt["gpu_runs"] == 0
    assert len(set(receipt["worker_pids"])) == 7
    assert len(receipt["policy_rows"]) == 3
    for role in ("agent", "guard"):
        audit = receipt["policy_rows"][0]["audits"][role]
        assert [r["input_tokens"] for r in audit["policy_requests"]] == [1, 4096, 1]
        assert [r["min_length"] for r in audit["policy_requests"]] == [0, 0, 0]
        assert [r["output_tokens"] for r in audit["attention"]["requests"]] == [1, 3, 1]
        assert not audit["source_authenticated"] and not audit["publisher_metadata_authenticated"]
    for name, sha in receipt["raw_sha256"].items():
        assert hashlib.sha256((output / "transport" / name).read_bytes()).hexdigest() == sha
    assert all(r["all_handles_reaped"] and r["no_retry_attempt"] for r in receipt["control_rows"])
    prior = (output / "summary.json").read_bytes()
    refused = subprocess.run(  # noqa: S603 — fixed local CLI and test-owned paths
        command, env=env, capture_output=True, text=True, timeout=10, check=False
    )
    assert refused.returncode != 0 and (output / "summary.json").read_bytes() == prior
