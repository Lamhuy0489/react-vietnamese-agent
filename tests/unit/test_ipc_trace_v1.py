"""Tracker instrumentation forwards exactly once and cannot certify OS cleanup."""

import gc
import json
import multiprocessing as mp
import multiprocessing.resource_tracker as tracker
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.ipc_trace_v1 import TrackerTrace, read_trace


@pytest.fixture
def trace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TrackerTrace:
    # Restore hooks only after each test has disposed its own live test resources.
    monkeypatch.setattr(tracker, "register", tracker.register)
    monkeypatch.setattr(tracker, "unregister", tracker.unregister)
    return TrackerTrace(tmp_path / "trace.jsonl", "control")


def test_real_event_registration_and_gc(trace: TrackerTrace) -> None:
    event = mp.get_context("spawn").Event()
    observed = read_trace(trace.path)
    assert observed["register_calls"] == 5 and observed["unregister_calls"] == 0
    assert len(observed["unmatched_registrations"]) == 5
    del event
    gc.collect()
    observed = read_trace(trace.path)
    assert observed["register_calls"] == observed["unregister_calls"] == 5
    assert observed["unmatched_registrations"] == []
    assert observed["ipc_cleanup_verified"] is False


def test_forwarding_exactly_once_without_cleanup_side_effects(
    trace: TrackerTrace, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str, str]] = []
    monkeypatch.setattr(tracker._resource_tracker, "_send", lambda *a: calls.append(a))
    tracker.register("private-resource-name", "semaphore")
    assert calls == [("REGISTER", "private-resource-name", "semaphore")]
    assert len(read_trace(trace.path)["unmatched_registrations"]) == 1
    tracker.unregister("private-resource-name", "semaphore")
    assert calls[-1] == ("UNREGISTER", "private-resource-name", "semaphore")
    assert len(calls) == 2
    data = trace.path.read_text()
    assert "private-resource-name" not in data
    assert "test_forwarding_exactly_once_without_cleanup_side_effects" in data
    assert "locals" not in data and '"source"' not in data


def test_upstream_failure_not_recorded_as_success(
    trace: TrackerTrace, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: Any) -> None:
        raise OSError("synthetic upstream failure")

    monkeypatch.setattr(tracker._resource_tracker, "_send", fail)
    with pytest.raises(OSError):
        tracker.register("name", "semaphore")
    assert read_trace(trace.path)["register_calls"] == 0


def test_no_nested_instrumentation(trace: TrackerTrace) -> None:
    with pytest.raises(RuntimeError):
        TrackerTrace(trace.path.parent / "nested.jsonl", "owner")
    assert not (trace.path.parent / "nested.jsonl").exists()


def test_owner_check(trace: TrackerTrace, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getpid", lambda: trace.pid + 1)
    with pytest.raises(RuntimeError):
        trace.record("PROBE_DONE")


@pytest.mark.parametrize("mode", ["role", "missing_parent", "existing", "symlink"])
def test_trace_path_rejections(tmp_path: Path, mode: str) -> None:
    path = tmp_path / "trace.jsonl"
    role = "owner"
    if mode == "role":
        role = "raw secret"
    elif mode == "missing_parent":
        path = tmp_path / "missing/trace.jsonl"
    elif mode == "existing":
        path.write_text("preserved")
    else:
        target = tmp_path / "target"
        target.write_text("preserved")
        path.symlink_to(target)
    with pytest.raises((ValueError, FileExistsError)):
        TrackerTrace(path, role)
    if mode == "existing":
        assert path.read_text() == "preserved"


@pytest.mark.parametrize(
    "mode",
    [
        "sequence",
        "pid",
        "role",
        "protocol",
        "digest",
        "stack",
        "frame",
        "duplicate",
        "unmatched",
        "action",
        "installation",
        "truncated",
    ],
)
def test_reader_rejects_corruption(trace: TrackerTrace, tmp_path: Path, mode: str) -> None:
    event = mp.get_context("spawn").Event()
    del event
    gc.collect()
    rows = [json.loads(line) for line in trace.path.read_text().splitlines()]
    if mode in ("sequence", "pid"):
        rows[1][mode] = -1
    elif mode in ("role", "protocol", "action"):
        rows[1][mode] = "INVALID"
    elif mode == "digest":
        rows[1]["name_sha256"] = "x" * 64
    elif mode == "stack":
        rows[1]["stack"] = []
    elif mode == "frame":
        rows[1]["stack"][0]["locals"] = "secret"
    elif mode == "duplicate":
        rows[2]["name_sha256"] = rows[1]["name_sha256"]
    elif mode == "unmatched":
        rows[1]["action"] = "UNREGISTER"
    elif mode == "installation":
        rows[0]["action"] = "PROBE_DONE"
    path = tmp_path / "corrupt.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows))
    if mode == "truncated":
        path.write_text(path.read_text()[:-3])
    with pytest.raises(ValueError):
        read_trace(path)


def test_real_spawn_transport_controls(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    output = tmp_path / "probe"
    completed = subprocess.run(  # noqa: S603 - fixed local diagnostic, synthetic inputs
        [
            sys.executable,
            "scripts/run_phase5_pair_ipc_worker.py",
            "--backend",
            "stub",
            "--output",
            str(output),
        ],
        cwd=root,
        env=dict(os.environ, PAIR_SOURCE_COMMIT="a" * 40),
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert completed.returncode == 0, completed.stderr
    assert "leaked semaphore" not in completed.stderr
    assert "PAIR_IPC_WORKER_COMPLETE backend=stub valid=True" in completed.stdout
    parent = read_trace(output / "tracker/owner.jsonl")
    assert parent["register_calls"] == parent["unregister_calls"] == 90
    assert parent["unmatched_registrations"] == []
    assert len(list((output / "tracker").glob("*.jsonl"))) == 7
    pids = {parent["pid"]}
    for path in (output / "tracker").glob("*.jsonl"):
        row = read_trace(path)
        if row["role"] == "owner":
            continue
        assert row["register_calls"] == row["unregister_calls"] == 0
        pids.add(row["pid"])
        assert '"action": "FACTORY_READY"' in path.read_text()
    assert len(pids) == 7


def test_real_killed_child_registration_is_visible(tmp_path: Path) -> None:
    # Isolated owner exits naturally so its own resource tracker can clean the
    # intentionally orphaned positive control. No manual unlink/unregister.
    code = (
        "import multiprocessing as mp,os,signal\n"
        "from pathlib import Path\n"
        "from react_agent.llm.ipc_trace_v1 import TrackerTrace\n"
        f"trace=TrackerTrace(Path({str(tmp_path / 'positive.jsonl')!r}), 'control')\n"
        "lock=mp.get_context('spawn').Lock()\n"
        "os.kill(os.getpid(), signal.SIGTERM)\n"
    )
    result = subprocess.run(  # noqa: S603 - fixed synthetic positive-control program
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=15
    )
    assert result.returncode == -15
    assert "1 leaked semaphore" in result.stderr
    observed = read_trace(tmp_path / "positive.jsonl")
    assert observed["register_calls"] == 1 and observed["unregister_calls"] == 0
    assert len(observed["unmatched_registrations"]) == 1
    assert observed["ipc_cleanup_verified"] is False
