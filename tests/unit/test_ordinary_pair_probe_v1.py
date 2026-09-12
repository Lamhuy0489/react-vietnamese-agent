"""Ordinary protocol CPU controls; synthetic responses/memory, no model imports."""

import gc
import importlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm import ordinary_pair_probe_v1 as impl
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.guard_snapshot_v1 import (
    CANDIDATE_REVISION,
    REQUIRED,
    GuardSnapshot,
    SnapshotFile,
)
from react_agent.llm.model_pair_hf_v1 import AgentFactoryV2, GuardFactory
from react_agent.llm.model_pair_probe_v1 import SyntheticPairFactory, SyntheticPairObserver
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig


@pytest.fixture(autouse=True)
def release_pairs(monkeypatch: pytest.MonkeyPatch) -> Any:
    yield
    monkeypatch.undo()
    gc.collect()


def pair(root: Path) -> ModelPair:
    return ModelPair(
        SyntheticPairFactory("agent", root),
        SyntheticPairFactory("guard", root),
        PairConfig(
            ModelIdentity("synthetic-agent", "v1"),
            ModelIdentity("synthetic-guard", "v1"),
            agent_start_seconds=5,
            guard_start_seconds=5,
        ),
    )


def read(root: Path, name: str) -> dict[str, Any]:
    return json.loads((root / name).read_text())


def test_real_spawn_six_requests_one_attempt_per_role(tmp_path: Path) -> None:
    root = tmp_path / "run"
    result = impl.run(root, pair(root), SyntheticPairObserver(), {"backend": "stub"})
    assert result["execution_valid"] and result["reaped"] and result["recovery_valid"]
    assert result["calls_submitted"] == result["responses_returned"] == 6
    assert result["actual_model_generation_calls"] == 0
    assert not result["native_validated"] and not result["phase5_accepted"]
    manifest = read(root, "manifest.json")
    assert manifest["inputs_sha256"] == text_hash(canonical_json(impl.inputs()))
    assert manifest["order"] == [[label, role] for label in ("A", "B", "A") for role in impl.ROLES]
    assert not manifest["automatic_retry"] and manifest["benchmark_tasks"] == 0
    assert manifest["test_payloads_parsed"] == 0
    for role in impl.ROLES:
        attempts = read(root, "closed.json")["workers"][role]["attempts"]
        assert len(attempts) == 4
        assert len({attempt["pid"] for attempt in attempts}) == 1
        assert all(attempt["status"] == "OK" for attempt in attempts)
        assert (
            manifest["generation"][role]
            == GenerationConfig(max_new_tokens=512 if role == "agent" else 128).model_dump()
        )
    assert (
        read(root, "call_01_submitted.json")["messages_sha256"]
        == read(root, "call_05_submitted.json")["messages_sha256"]
    )
    assert (
        read(root, "call_02_submitted.json")["messages_sha256"]
        == read(root, "call_06_submitted.json")["messages_sha256"]
    )
    assert (
        read(root, "call_01_submitted.json")["messages_sha256"]
        != read(root, "call_03_submitted.json")["messages_sha256"]
    )
    assert len(list(root.glob("recovery_*.json"))) == 6


@pytest.mark.parametrize(
    "case",
    ["baseline", "invalid_baseline", "resident", "after_call", "recovery", "leak", "no_residency"],
)
def test_observer_failure_closes_and_preserves_counts(tmp_path: Path, case: str) -> None:
    class Observer(SyntheticPairObserver):
        def sample(self, phase: str) -> list[dict[str, int]]:
            if case == phase:
                raise RuntimeError("PRIVATE OBSERVER MESSAGE")
            if case == "invalid_baseline" and phase == "baseline":
                return [{"bad": 1}]
            result = super().sample(phase)
            if case == "leak" and phase == "recovery":
                result[1]["free_bytes"] -= 1024**3
            if case == "no_residency" and phase == "resident":
                return super().sample("baseline")
            return result

    root = tmp_path / "run"
    result = impl.run(root, pair(root), Observer(), {"backend": "stub"})
    assert not result["execution_valid"] and result["reaped"]
    if case == "after_call":
        assert result["calls_submitted"] == result["responses_returned"] == 1
        assert (root / "call_01_returned.json").exists()
    assert all("PRIVATE" not in p.read_text() for p in root.glob("*.json"))


@pytest.mark.parametrize("position", [1, 2, 3, 6])
@pytest.mark.parametrize("interrupt", [False, True])
def test_no_retry_on_failure_or_interrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, position: int, interrupt: bool
) -> None:
    root = tmp_path / "run"
    instance = pair(root)
    original = instance.generate
    count = 0

    def generate(*args: Any, **kwargs: Any) -> Any:
        nonlocal count
        count += 1
        if count == position:
            raise (
                KeyboardInterrupt("PRIVATE INTERRUPT")
                if interrupt
                else RuntimeError("PRIVATE FAILURE")
            )
        return original(*args, **kwargs)

    monkeypatch.setattr(instance, "generate", generate)
    if interrupt:
        with pytest.raises(KeyboardInterrupt):
            impl.run(root, instance, SyntheticPairObserver(), {"backend": "stub"})
        result = read(root, "summary.json")
    else:
        result = impl.run(root, instance, SyntheticPairObserver(), {"backend": "stub"})
    assert result["calls_submitted"] == count == position
    assert result["responses_returned"] == position - 1
    assert result["reaped"] and not result["execution_valid"]
    assert result["status"] == ("INTERRUPTED" if interrupt else "ERROR")
    assert read(root, "error.json")["error_class"] == (
        "KeyboardInterrupt" if interrupt else "RuntimeError"
    )
    assert all("PRIVATE" not in p.read_text() for p in root.glob("*.json"))


def test_different_a_is_not_retried_or_filtered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "run"
    instance = pair(root)
    original = instance.generate
    count = 0

    def generate(role: Any, messages: Any, config: Any) -> ModelResponse:
        nonlocal count
        count += 1
        assert messages == impl.inputs()["B" if count in (3, 4) else "A"][role]
        response = original(role, messages, config)
        messages.clear()
        config.max_new_tokens = 1
        return response.model_copy(update={"text": f"PRIVATE RESPONSE {count}"})

    monkeypatch.setattr(instance, "generate", generate)
    result = impl.run(root, instance, SyntheticPairObserver(), {"backend": "stub"})
    assert result["execution_valid"] and count == 6
    assert result["repeated_a_equal"] == {"agent": False, "guard": False}
    assert all("PRIVATE RESPONSE" not in p.read_text() for p in root.glob("*.json"))


@pytest.mark.parametrize("case", ["existing", "same", "nested", "symlink"])
def test_output_refusal(tmp_path: Path, case: str) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    if case == "existing":
        first.mkdir()
    elif case == "same":
        second = first
    elif case == "nested":
        second = first / "child"
    else:
        first.symlink_to(second)
    with pytest.raises(ValueError):
        impl.fresh_roots(first, second)


@pytest.mark.parametrize("case", ["backend", "identity", "interval", "started"])
def test_invalid_run_does_not_create_output(tmp_path: Path, case: str) -> None:
    root = tmp_path / "run"
    instance = pair(root)
    observer = SyntheticPairObserver()
    identity = {"backend": "stub"}
    if case == "backend":
        identity["backend"] = "unknown"
    elif case == "identity":
        identity["backend"] = "hf"
    elif case == "interval":
        observer.interval = float("nan")
    else:
        instance.close()
    try:
        with pytest.raises(ValueError):
            impl.run(root, instance, observer, identity)
        assert not root.exists()
    finally:
        instance.close()


def snapshot() -> GuardSnapshot:
    return GuardSnapshot(
        upstream_revision=CANDIDATE_REVISION,
        files=tuple(SnapshotFile(name=name, size=1, sha256="a" * 64) for name in sorted(REQUIRED)),
    )


def test_native_factory_lazy_topology(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Fake content identity only for constructor wiring; never authenticate these bytes or load.
    pin = snapshot()
    monkeypatch.setattr(GuardSnapshot, "model_revision", property(lambda self: impl.GUARD_REVISION))
    out, attention, policy = (tmp_path / name for name in ("out", "attention", "policy"))
    instance = impl.native_pair(
        tmp_path / "agent", tmp_path / "inventory", tmp_path / "guard", pin, out, attention, policy
    )
    try:
        assert instance.state == "NEW" and instance.config == impl.native_config()
        for role, worker in instance._workers.items():
            factory = worker.factory.factory.factory.attention.native_factory
            if role == "agent":
                assert type(factory) is AgentFactoryV2
                assert factory.metrics_path == out / "agent_hf_metrics.jsonl"
            else:
                assert type(factory) is GuardFactory
                assert factory.hf.snapshot is pin
                assert factory.hf.metrics_path == out / "guard_hf_metrics.jsonl"
            assert not worker.attempts
        assert not any(path.exists() for path in (out, attention, policy))
    finally:
        instance.close()


def test_native_snapshot_rejected_before_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("transport must not be constructed")

    monkeypatch.setattr(impl, "policy_pair", forbidden)
    with pytest.raises(ValueError, match="snapshot"):
        impl.native_pair(
            tmp_path / "agent",
            tmp_path / "inventory",
            tmp_path / "guard",
            snapshot(),
            tmp_path / "out",
            tmp_path / "a",
            tmp_path / "p",
        )


@pytest.mark.parametrize("source_index", [0, 1, 2])
@pytest.mark.parametrize("nested_output", [False, True])
def test_native_inputs_disjoint_before_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source_index: int, nested_output: bool
) -> None:
    monkeypatch.setattr(GuardSnapshot, "model_revision", property(lambda self: impl.GUARD_REVISION))
    paths = [tmp_path / "agent", tmp_path / "inventory", tmp_path / "guard"]
    out = paths[source_index] / "output" if nested_output else paths[source_index].parent / "parent"
    if not nested_output:
        paths[source_index] = out / "input"
    with pytest.raises(ValueError, match="overlap"):
        impl.native_pair(*paths, snapshot(), out, tmp_path / "a", tmp_path / "p")
    assert not out.exists()


def test_native_deadline_change_rejected(tmp_path: Path) -> None:
    config = impl.native_config()
    instance = ModelPair(
        SyntheticPairFactory("agent", tmp_path),
        SyntheticPairFactory("guard", tmp_path),
        PairConfig(config.agent, config.guard, agent_call_seconds=181),
    )
    try:
        with pytest.raises(ValueError, match="deadlines"):
            impl.run(tmp_path / "out", instance, SyntheticPairObserver(), {"backend": "hf"})
    finally:
        instance.close()


def test_cleanup_failure_never_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "out"
    instance = pair(root)
    original = instance.close

    def fail() -> None:
        original()
        raise RuntimeError("PRIVATE CLEANUP ERROR")

    monkeypatch.setattr(instance, "close", fail)
    result = impl.run(root, instance, SyntheticPairObserver(), {"backend": "stub"})
    assert result["cleanup_error"] and result["reaped"] and not result["execution_valid"]
    assert not list(root.glob("recovery_*.json"))
    assert read(root, "cleanup_error.json")["error_class"] == "RuntimeError"
    assert all("PRIVATE" not in p.read_text() for p in root.glob("*.json"))


@pytest.mark.parametrize(
    "case", ["commit", "missing_native", "native_in_stub", "existing", "nested"]
)
def test_cli_refusal_precedes_native_imports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    try:
        cli = importlib.import_module("run_phase5_ordinary_pair")
    finally:
        sys.path.pop(0)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("native initialization forbidden")

    for name in ("verify_gpu_environment", "PairCUDAObserver", "native_pair", "resolve_mount"):
        monkeypatch.setattr(cli, name, forbidden)
    out = tmp_path / "out"
    args = ["runner", "--output", str(out)]
    monkeypatch.setenv("PAIR_SOURCE_COMMIT", "a" * 40)
    if case == "commit":
        monkeypatch.delenv("PAIR_SOURCE_COMMIT")
    elif case == "missing_native":
        args += ["--backend", "hf"]
    elif case == "native_in_stub":
        args += ["--snapshot", "missing"]
    elif case == "existing":
        out.mkdir()
    else:
        args += [
            "--backend",
            "hf",
            "--policy-output",
            str(out / "p"),
            "--attention-output",
            str(tmp_path / "a"),
            "--guard-path",
            "missing",
            "--snapshot",
            "missing",
        ]
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(ValueError):
        cli.main()
    assert not (out / "manifest.json").exists()
