"""Durable probe tests using real spawned synthetic backends and fake memory."""

import json
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.model_pair_probe_v1 import (
    MIN_RESIDENT,
    PairCUDAObserver,
    SyntheticPairFactory,
    SyntheticPairObserver,
    run_pair_probe,
    validate_memory,
)
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig


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


def test_durable_probe(tmp_path: Path) -> None:
    output = tmp_path / "run"
    instance = pair(output)
    result = run_pair_probe(output, instance, SyntheticPairObserver(), {"backend": "synthetic"})
    assert result["valid"] and result["calls_completed"] == 2 and result["reaped"]
    assert not result["phase5_accepted"]
    assert len(list(output.glob("recovery_*.json"))) == 6
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["min_resident_bytes"] == list(MIN_RESIDENT)
    assert not manifest["automatic_retry"]
    agent = json.loads((output / "agent_call.json").read_text())
    assert "response_sha256" in agent and "synthetic transport response" not in json.dumps(agent)
    closed = json.loads((output / "closed.json").read_text())
    assert all(not w["handle_pending"] for w in closed["workers"].values())
    with pytest.raises(ValueError):
        run_pair_probe(output, instance, SyntheticPairObserver(), {})


@pytest.mark.parametrize(
    "case", ["baseline", "resident", "after_call", "recovery", "leak", "no_residency"]
)
def test_observer_failure_preserves_and_closes(tmp_path: Path, case: str) -> None:
    class Observer(SyntheticPairObserver):
        def sample(self, phase: str) -> list[dict[str, int]]:
            if phase == case:
                return [{"device": 0, "free_bytes": -1, "total_bytes": 1}]
            rows = super().sample(phase)
            if case == "leak" and phase == "recovery":
                rows[1]["free_bytes"] -= 1024**3
            if case == "no_residency" and phase == "resident":
                return super().sample("baseline")
            return rows

    output = tmp_path / "run"
    result = run_pair_probe(output, pair(output), Observer(), {"backend": "synthetic"})
    assert not result["valid"] and result["reaped"]
    assert (output / "summary.json").exists() and (output / "closed.json").exists()
    if case in {"baseline", "resident", "no_residency"}:
        assert result["calls_completed"] == 0


@pytest.mark.parametrize("case", ["generation", "interrupt"])
def test_generation_failure_and_interrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    output = tmp_path / "run"
    instance = pair(output)

    def fail(*args: Any, **kw: Any) -> Any:
        if case == "interrupt":
            raise KeyboardInterrupt()
        raise RuntimeError("synthetic secret")

    monkeypatch.setattr(instance, "generate", fail)
    if case == "interrupt":
        with pytest.raises(KeyboardInterrupt):
            run_pair_probe(output, instance, SyntheticPairObserver(), {})
    else:
        assert not run_pair_probe(output, instance, SyntheticPairObserver(), {})["valid"]
    closed = json.loads((output / "closed.json").read_text())
    assert all(not w["handle_pending"] for w in closed["workers"].values())
    assert not json.loads((output / "summary.json").read_text())["valid"]


@pytest.mark.parametrize("bad", [True, -1, float("nan"), float("inf")])
def test_bad_interval(tmp_path: Path, bad: float) -> None:
    observer = SyntheticPairObserver()
    observer.interval = bad
    with pytest.raises(ValueError):
        run_pair_probe(tmp_path / "run", pair(tmp_path), observer, {})


@pytest.mark.parametrize("case", ["duplicate", "bool", "too_free", "missing", "extra"])
def test_memory_validation(case: str) -> None:
    rows = SyntheticPairObserver().sample("baseline")
    if case == "duplicate":
        rows[1]["device"] = 0
    elif case == "bool":
        rows[0]["device"] = False
    elif case == "too_free":
        rows[0]["free_bytes"] = rows[0]["total_bytes"] + 1
    elif case == "missing":
        del rows[0]["free_bytes"]
    else:
        rows[0]["extra"] = 1
    with pytest.raises(ValueError):
        validate_memory(rows)


def test_cuda_observer_fake_operation(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    from types import SimpleNamespace

    devices = []

    def ones(count: int, *, device: str) -> Any:
        devices.append(device)
        return SimpleNamespace(sum=lambda: SimpleNamespace(item=lambda: count))

    cuda = SimpleNamespace(
        device_count=lambda: 2,
        get_device_name=lambda i: "Tesla T4",
        synchronize=lambda i: None,
        empty_cache=lambda: None,
        mem_get_info=lambda i: (10, 20),
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=cuda, ones=ones))
    observer = PairCUDAObserver()
    assert devices == ["cuda:0", "cuda:1"]
    assert observer.sample("baseline") == [
        {"device": i, "free_bytes": 10, "total_bytes": 20} for i in (0, 1)
    ]
