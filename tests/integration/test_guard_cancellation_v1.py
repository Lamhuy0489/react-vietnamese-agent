"""Actual spawned CPU cancellation; no CUDA/model inference or benchmark data."""

import functools
import json
from pathlib import Path

import pytest

from react_agent.llm.guard_cancellation_v1 import (
    PLAN,
    ResidentFactory,
    StubObserver,
    run_cancellation,
)
from react_agent.security_v1.warm_guard import WarmGuardConfig


@pytest.mark.parametrize("failure", ["", "load_error", "busy_error", "recovery"])
def test_process_cases(tmp_path: Path, failure: str) -> None:
    output = tmp_path / "probe"
    config = WarmGuardConfig("synthetic-resident-stub", "v1", timeout_seconds=2)
    result = run_cancellation(
        output,
        functools.partial(ResidentFactory, failure=failure),
        StubObserver(recovery_failure=failure == "recovery"),
        config,
        {"backend": "stub", "source_commit": "a" * 40},
    )
    assert result["valid"] is (failure == "")
    assert not result["phase5_accepted"] and result["model_generation_calls"] == 0
    assert [r["trial"] for r in result["rows"]] == list(PLAN)
    if not failure:
        assert [len(r["attempts"]) for r in result["rows"]] == [1, 2, 2]
        assert all(r["reaped"] and len(r["after_samples"]) == 6 for r in result["rows"])
        for row in result["rows"][1:]:
            assert row["attempts"][-1]["status"] == "TIMEOUT"
            assert row["attempts"][-1]["elapsed_seconds"] < 6
        assert result["rows"][-1]["lifecycle"][-1]["method"] == "KILL"
        assert result["rows"][-1]["lifecycle"][-1]["exitcode"] == -9
        marker = json.loads((output / "ignore_term_timeout/busy_entered.json").read_text())
        assert marker["ignore_sigterm"] and not marker["actual_cuda_operation"]
    else:
        assert result["rows"][-1]["status"] == "SKIPPED_AFTER_FAILURE"
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["timeout_seconds"] == 2 and not manifest["automatic_retry"]
    assert manifest["sample_interval_seconds"] == 0
    with pytest.raises(FileExistsError):
        run_cancellation(output, ResidentFactory, StubObserver(), config, {})


class BrokenObserver(StubObserver):
    def sample(self, phase: str) -> dict[str, int]:
        if phase == "after":
            raise RuntimeError("synthetic observer failure")
        return super().sample(phase)


def test_observer_failure_preserves_trial(tmp_path: Path) -> None:
    result = run_cancellation(
        tmp_path / "probe",
        ResidentFactory,
        BrokenObserver(),
        WarmGuardConfig("synthetic-resident-stub", "v1", timeout_seconds=2),
        {"backend": "stub"},
    )
    assert not result["valid"]
    assert result["rows"][0]["status"] == "OBSERVER_ERROR"
    assert result["rows"][0]["reaped"]
    assert (tmp_path / "probe/resident_close/trial.json").is_file()
