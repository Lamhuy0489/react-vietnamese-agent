"""Real spawn transport with synthetic backends/memory; no native model execution."""

import json
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.context_stress_probe_v1 import (
    SyntheticStressFactory,
    run_context_probe,
    validate_completion,
)
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig


def pair(root: Path) -> ModelPair:
    return ModelPair(
        SyntheticStressFactory("agent", root),
        SyntheticStressFactory("guard", root),
        PairConfig(
            ModelIdentity("synthetic-agent", "v1"),
            ModelIdentity("synthetic-guard", "v1"),
            agent_start_seconds=5,
            guard_start_seconds=5,
        ),
    )


def test_two_sequential_synthetic_calls_reaped(tmp_path: Path) -> None:
    out = tmp_path / "run"
    p = pair(out)
    result = run_context_probe(out, p, SyntheticPairObserver(), {"backend": "stub"})
    assert result["valid"] and result["reaped"] and result["calls_completed"] == 2
    assert not result["native_stress_verified"] and result["actual_model_generation_calls"] == 0
    assert len(list(out.glob("recovery_*.json"))) == 6
    assert not result["phase5_accepted"]
    assert all(
        not w["handle_pending"]
        for w in json.loads((out / "closed.json").read_text())["workers"].values()
    )
    assert not list(out.glob("*_stress"))


@pytest.mark.parametrize(
    "case", ["baseline", "resident", "after_call", "recovery", "leak", "no_residency"]
)
def test_observer_failures_close_workers(tmp_path: Path, case: str) -> None:
    class Observer(SyntheticPairObserver):
        def sample(self, phase: str) -> list[dict[str, int]]:
            if case == phase:
                raise RuntimeError("PRIVATE OBSERVER TEXT")
            rows = super().sample(phase)
            if case == "leak" and phase == "recovery":
                rows[1]["free_bytes"] -= 1024**3
            if case == "no_residency" and phase == "resident":
                return super().sample("baseline")
            return rows

    out = tmp_path / "run"
    r = run_context_probe(out, pair(out), Observer(), {"backend": "stub"})
    assert not r["valid"] and r["reaped"] and not r["native_stress_verified"]
    assert all("PRIVATE" not in p.read_text() for p in out.rglob("*.json"))


@pytest.mark.parametrize("case", ["generate", "interrupt", "wrong_ack"])
def test_call_errors_cleanup_and_preserve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    out = tmp_path / "run"
    p = pair(out)

    def fail(*args: Any, **kw: Any) -> Any:
        if case == "interrupt":
            raise KeyboardInterrupt()
        if case == "wrong_ack":
            from react_agent.llm.base import ModelResponse

            return ModelResponse(
                text="PRIVATE WRONG OUTPUT", model_id="synthetic-agent", model_revision="v1"
            )
        raise RuntimeError("PRIVATE MODEL ERROR")

    monkeypatch.setattr(p, "generate", fail)
    if case == "interrupt":
        with pytest.raises(KeyboardInterrupt):
            run_context_probe(out, p, SyntheticPairObserver(), {"backend": "stub"})
        result = json.loads((out / "summary.json").read_text())
    else:
        result = run_context_probe(out, p, SyntheticPairObserver(), {"backend": "stub"})
    assert result["reaped"] and not result["valid"]
    assert all("PRIVATE" not in f.read_text() for f in out.rglob("*.json"))


def test_hf_requires_durable_native_completion(tmp_path: Path) -> None:
    out = tmp_path / "run"
    r = run_context_probe(out, pair(out), SyntheticPairObserver(), {"backend": "hf"})
    assert not r["valid"] and r["reaped"] and not r["native_stress_verified"]


@pytest.mark.parametrize(
    "key",
    [
        "pid",
        "role",
        "protocol",
        "stage",
        "model_generation_calls",
        "separate_final_forwards",
        "input_tokens",
        "new_tokens",
        "cache_length_after_generation",
        "cache_length_after_final_forward",
        "full_boundary_cache_observed",
        "generated_text_retained",
    ],
)
def test_completion_mutation_rejected(key: str) -> None:
    value = {
        "protocol": "context_stress_v1",
        "stage": "completed",
        "pid": 42,
        "role": "agent",
        "model_generation_calls": 1,
        "separate_final_forwards": 1,
        "summary": {
            "input_tokens": 4096,
            "new_tokens": 512,
            "cache_length_after_generation": 4607,
            "cache_length_after_final_forward": 4608,
            "full_boundary_cache_observed": True,
            "generated_text_retained": False,
        },
    }
    snapshot = {"events": [{"pid": 42, "role": "agent", "stage": "ready"}]}
    validate_completion(value, "agent", snapshot)
    if key in value:
        value[key] = "bad"
    else:
        value["summary"][key] = "bad"  # type: ignore[index]
    with pytest.raises(ValueError):
        validate_completion(value, "agent", snapshot)
