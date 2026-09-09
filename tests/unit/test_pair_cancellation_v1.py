"""Real spawn cancellation, synthetic backends/memory: no local model or CUDA."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.llm.model_pair_probe_v1 import SyntheticPairBackend, SyntheticPairObserver
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig, Role
from react_agent.llm.pair_cancellation_v1 import (
    BUSY,
    PLAN,
    BusyBackend,
    BusyFactory,
    busy_role,
    matching_baseline,
    run_pair_cancellation,
    run_trial,
)


@dataclass(frozen=True)
class NoGenerateFactory:
    role: Role
    failure: bool = False

    def __call__(self) -> LLMBackend:
        if self.failure:
            raise RuntimeError("synthetic secret load message")
        return NoGenerateBackend(self.role)


class NoGenerateBackend(SyntheticPairBackend):
    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        raise AssertionError("diagnostic must never call underlying model.generate")


def build_pair(trial: str, root: Path, failure: bool = False) -> ModelPair:
    return ModelPair(
        BusyFactory(NoGenerateFactory("agent", failure), "agent", trial, root),
        BusyFactory(NoGenerateFactory("guard"), "guard", trial, root),
        PairConfig(
            ModelIdentity("synthetic-agent", "v1"),
            ModelIdentity("synthetic-guard", "v1"),
            agent_start_seconds=5,
            guard_start_seconds=5,
            agent_call_seconds=0.15,
            guard_call_seconds=0.15,
            terminate_grace_seconds=0.1,
            kill_grace_seconds=1,
        ),
    )


def test_complete_three_trial_suite(tmp_path: Path) -> None:
    out = tmp_path / "run"
    summary = run_pair_cancellation(out, build_pair, SyntheticPairObserver(), {"backend": "stub"})
    assert summary["valid"] and not summary["phase5_accepted"]
    assert summary["model_generation_calls"] == 0
    assert [r["trial"] for r in summary["rows"]] == list(PLAN)
    pids = []
    for trial in PLAN:
        root = out / trial
        row = json.loads((root / "trial.json").read_text())
        assert row["timeout_observed"] and row["reaped"] and row["recovery_valid"]
        closed = json.loads((root / "closed.json").read_text())
        selected = closed["workers"][busy_role(trial)]
        marker = json.loads((root / "busy_entered.json").read_text())
        assert selected["attempts"][-1]["status"] == "TIMEOUT"
        assert marker["pid"] == selected["attempts"][-1]["pid"]
        assert marker["actual_cuda_operation"] is False and marker["devices"] == []
        assert selected["lifecycle"][0]["method"] == (
            "KILL" if trial == "guard_ignore_term" else "TERMINATE"
        )
        assert len(list(root.glob("recovery_*.json"))) == 6
        for worker in closed["workers"].values():
            assert not worker["handle_pending"] and worker["closed"]
            pids.append(worker["lifecycle"][0]["pid"])
    assert len(set(pids)) == 6
    with pytest.raises(FileExistsError):
        run_pair_cancellation(out, build_pair, SyntheticPairObserver(), {})


@pytest.mark.parametrize("mode", ["baseline", "resident", "recovery", "leak", "drift", "no_model"])
def test_observer_failures_stop_suite(tmp_path: Path, mode: str) -> None:
    class Observer(SyntheticPairObserver):
        baseline_calls = 0

        def sample(self, phase: str) -> list[dict[str, int]]:
            rows = super().sample(phase)
            if phase == mode:
                rows[0]["free_bytes"] = -1
            if phase == "baseline":
                self.baseline_calls += 1
                if mode == "drift" and self.baseline_calls == 2:
                    rows[0]["free_bytes"] -= 1024**3
            if mode == "leak" and phase == "recovery":
                rows[0]["free_bytes"] -= 1024**3
            if mode == "no_model" and phase == "resident":
                return super().sample("baseline")
            return rows

    out = tmp_path / "run"
    result = run_pair_cancellation(out, build_pair, Observer(), {})
    assert not result["valid"] and (out / "summary.json").exists()
    if mode != "baseline":
        assert [r["status"] for r in result["rows"][1:]] == ["SKIPPED_AFTER_FAILURE"] * 2
        closed = json.loads((out / PLAN[0] / "closed.json").read_text())
        assert all(not w["handle_pending"] for w in closed["workers"].values())


def test_load_error_retains_class_only(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = run_pair_cancellation(
        out, lambda trial, root: build_pair(trial, root, failure=True), SyntheticPairObserver(), {}
    )
    assert not result["valid"]
    assert "synthetic secret" not in json.dumps(result)
    assert not (out / PLAN[1]).exists()


@pytest.mark.parametrize(
    "mode", ["interrupt", "unexpected_return", "missing_marker", "marker_mismatch"]
)
def test_generation_faults_preserve_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    out = tmp_path / "run"

    def factory(trial: str, root: Path) -> ModelPair:
        instance = build_pair(trial, root)
        original = instance.generate

        def fail(*args: Any, **kw: Any) -> Any:
            if mode == "interrupt":
                raise KeyboardInterrupt()
            if mode == "unexpected_return":
                return None
            try:
                return original(*args, **kw)
            finally:
                marker = root / "busy_entered.json"
                if mode == "missing_marker":
                    marker.unlink()
                else:
                    value = json.loads(marker.read_text())
                    value["pid"] = -1
                    marker.write_text(json.dumps(value))

        monkeypatch.setattr(instance, "generate", fail)
        return instance

    if mode == "interrupt":
        with pytest.raises(KeyboardInterrupt):
            run_pair_cancellation(out, factory, SyntheticPairObserver(), {})
    else:
        assert not run_pair_cancellation(out, factory, SyntheticPairObserver(), {})["valid"]
    assert not json.loads((out / "summary.json").read_text())["valid"]
    closed = json.loads((out / PLAN[0] / "closed.json").read_text())
    assert all(not w["handle_pending"] for w in closed["workers"].values())


@pytest.mark.parametrize("value", [True, -1, float("nan"), float("inf")])
def test_bad_cadence_rejected(tmp_path: Path, value: float) -> None:
    observer = SyntheticPairObserver()
    observer.interval = value
    with pytest.raises(ValueError):
        run_pair_cancellation(tmp_path / "run", build_pair, observer, {})


def test_hf_cadence_not_stub(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        run_pair_cancellation(
            tmp_path / "run", build_pair, SyntheticPairObserver(), {}, actual_cuda=True
        )


def test_busy_refuses_non_host_calls(tmp_path: Path) -> None:
    backend = NoGenerateBackend("agent")
    wrapper = BusyBackend(
        backend, BusyFactory(NoGenerateFactory("agent"), "agent", PLAN[0], tmp_path)
    )
    with pytest.raises(ValueError):
        wrapper.generate([{"role": "user", "content": "ordinary prompt"}], GenerationConfig())
    with pytest.raises(ValueError):
        wrapper.generate([{"role": "user", "content": BUSY}], GenerationConfig(max_new_tokens=1))
    with pytest.raises(ValueError):
        BusyFactory(NoGenerateFactory("agent"), "agent", "unknown", tmp_path)


def test_linked_output_refused(tmp_path: Path) -> None:
    link = tmp_path / "link"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        run_pair_cancellation(link / "run", build_pair, SyntheticPairObserver(), {})


def test_baseline_capacity_and_threshold() -> None:
    rows = SyntheticPairObserver().sample("baseline")
    changed = [dict(r) for r in rows]
    changed[1]["total_bytes"] += 1
    assert not matching_baseline(rows, changed)


def test_pending_cleanup_never_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    instance = build_pair(PLAN[0], tmp_path)
    original = instance.snapshot

    def snapshot() -> dict[str, Any]:
        result = original()
        if result["state"] == "FAILED":
            result["workers"]["guard"]["handle_pending"] = True
        return result

    monkeypatch.setattr(instance, "snapshot", snapshot)
    result = run_trial(
        tmp_path,
        PLAN[0],
        instance,
        SyntheticPairObserver(),
        SyntheticPairObserver().sample("baseline"),
        actual_cuda=False,
    )
    assert not result["valid"] and not result["reaped"]
    assert not list(tmp_path.glob("recovery_*.json"))


@pytest.mark.parametrize("role", ["agent", "guard"])
def test_cuda_busy_device_mapping_with_fake_torch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role: Role
) -> None:
    import sys
    from types import SimpleNamespace

    devices: list[str] = []
    synced: list[int] = []

    class Tensor:
        def __matmul__(self, other: Any) -> Any:
            return self

        def __getitem__(self, key: Any) -> Any:
            return self

        def item(self) -> int:
            return 256

    def ones(shape: Any, *, device: str, dtype: Any) -> Tensor:
        devices.append(device)
        return Tensor()

    fake = SimpleNamespace(
        ones=ones, float16="fp16", cuda=SimpleNamespace(synchronize=synced.append)
    )
    monkeypatch.setitem(sys.modules, "torch", fake)

    def interrupt(seconds: float) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr("react_agent.llm.pair_cancellation_v1.time.sleep", interrupt)
    trial = "agent_busy" if role == "agent" else "guard_busy"
    spec = BusyFactory(NoGenerateFactory(role), role, trial, tmp_path, actual_cuda=True)
    with pytest.raises(KeyboardInterrupt):
        spec().generate([{"role": "user", "content": BUSY}], GenerationConfig())
    expected = [0, 1] if role == "agent" else [1]
    assert devices == [f"cuda:{i}" for i in expected] and synced == expected * 2
    marker = json.loads((tmp_path / "busy_entered.json").read_text())
    assert marker["devices"] == expected and marker["actual_cuda_operation"]


def test_factory_exception_preserves_summary(tmp_path: Path) -> None:
    def factory(trial: str, root: Path) -> ModelPair:
        raise ValueError("synthetic secret")

    result = run_pair_cancellation(tmp_path / "run", factory, SyntheticPairObserver(), {})
    assert not result["valid"] and result["error_class"] == "ValueError"
    assert "synthetic secret" not in json.dumps(result)


@pytest.mark.parametrize("interrupt", [False, True])
def test_cleanup_error_retains_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interrupt: bool
) -> None:
    instance = build_pair(PLAN[0], tmp_path)
    original = instance.close

    def fail() -> None:
        original()
        if interrupt:
            raise KeyboardInterrupt()
        raise RuntimeError("synthetic cleanup error")

    monkeypatch.setattr(instance, "close", fail)
    if interrupt:
        with pytest.raises(KeyboardInterrupt):
            run_trial(
                tmp_path,
                PLAN[0],
                instance,
                SyntheticPairObserver(),
                SyntheticPairObserver().sample("baseline"),
                actual_cuda=False,
            )
        result = json.loads((tmp_path / "trial.json").read_text())
    else:
        result = run_trial(
            tmp_path,
            PLAN[0],
            instance,
            SyntheticPairObserver(),
            SyntheticPairObserver().sample("baseline"),
            actual_cuda=False,
        )
    assert not result["valid"] and result["cleanup_error"]
    assert result["status"] == "CLEANUP_ERROR"
    assert not list(tmp_path.glob("recovery_*.json"))
