"""Cancellation entry point constructs bound factories without native model loading."""

import importlib
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.guard_snapshot_v1 import (
    CANDIDATE_REVISION,
    REQUIRED,
    GuardSnapshot,
    SnapshotFile,
)


@pytest.fixture
def entry(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("run_phase5_pair_cancel_worker")


@pytest.fixture
def pin() -> GuardSnapshot:
    return GuardSnapshot(
        upstream_revision=CANDIDATE_REVISION,
        files=tuple(SnapshotFile(name=n, size=1, sha256="a" * 64) for n in sorted(REQUIRED)),
    )


def test_hf_pairs_are_lazy_and_deadlines_unchanged(
    entry: Any, pin: GuardSnapshot, tmp_path: Path
) -> None:
    factory = entry.CancellationPairs(
        tmp_path / "agent", tmp_path / "inventory", tmp_path / "guard", pin
    )
    for trial in ("agent_busy", "guard_busy", "guard_ignore_term"):
        pair = factory(trial, tmp_path / trial)
        assert pair.state == "NEW"
        assert pair.config.agent_start_seconds == 1200 and pair.config.guard_start_seconds == 120
        assert pair.config.agent_call_seconds == 180 and pair.config.guard_call_seconds == 120
        assert pair.config.terminate_grace_seconds == 0.5 and pair.config.kill_grace_seconds == 1
        assert pair.config.agent.model_revision == entry.AGENT_REVISION
        assert pair.config.guard.model_revision == pin.model_revision
        for worker in pair._workers.values():
            assert worker._process is None
        pair.close()


@pytest.mark.parametrize("missing", ["agent_path", "inventory_path", "guard_path", "snapshot"])
def test_incomplete_hf_inputs_rejected(
    entry: Any, pin: GuardSnapshot, tmp_path: Path, missing: str
) -> None:
    args = dict(agent_path=tmp_path, inventory_path=tmp_path, guard_path=tmp_path, snapshot=pin)
    args[missing] = None
    with pytest.raises(ValueError):
        entry.CancellationPairs(**args)


def test_stub_deadlines_distinct(entry: Any, tmp_path: Path) -> None:
    pair = entry.CancellationPairs()("agent_busy", tmp_path)
    assert pair.config.agent_call_seconds == 0.2 and pair.config.guard_call_seconds == 0.2
    assert pair.config.agent.model_id == "synthetic-agent"
    pair.close()


@pytest.mark.parametrize("commit", ["", "bad", "g" * 40])
def test_entry_requires_commit(
    entry: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, commit: str
) -> None:
    monkeypatch.setenv("PAIR_SOURCE_COMMIT", commit)
    monkeypatch.setattr(
        "sys.argv", ["worker", "--backend", "stub", "--output", str(tmp_path / "run")]
    )
    with pytest.raises(ValueError):
        entry.main()
    assert not (tmp_path / "run").exists()
