"""Synthetic PID/stack fixtures; no real GPU output or Test payloads."""

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from react_agent.validation.pair_ipc_audit_v1 import audit_probe, audit_traces


def save(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


@pytest.fixture
def sample(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, ...]:
    monkeypatch.syspath_prepend(str(Path(__file__).parent))
    fixture = importlib.import_module("test_pair_cancellation_audit_v1")
    probe = tmp_path / "probe"
    probe.mkdir()
    path, pin, commit = fixture.sample.__wrapped__(probe)
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["identity"].pop("agent_adapter")
    manifest["identity"].update(instrumentation="ipc_tracker_trace_v1", python_version="3.12.9")
    fixture.write(path / "manifest.json", manifest)
    measurements = audit_probe(path, pin, commit, "3.12.9")
    traces = tmp_path / "tracker"
    traces.mkdir()
    identity = {
        "protocol": "ipc_tracker_trace_v1",
        "pid": 50,
        "role": "owner",
        "action": "INSTALLED",
        "python_version": "3.12.9",
        "implementation": "CPython",
        "tracker_source_sha256": "d" * 64,
    }
    frame = {
        "module": "react_agent.security_v1.warm_guard",
        "file": "warm_guard.py",
        "function": "__init__",
        "line": 130,
    }
    rows = [identity]
    for i in range(90):
        for action in ("REGISTER", "UNREGISTER"):
            rows.append(
                identity
                | {
                    "action": action,
                    "name_sha256": f"{i:064x}",
                    "resource_type": "semaphore",
                    "stack": [frame],
                }
            )
    rows.append(identity | {"action": "PROBE_DONE", "valid": True, "gc_collected": 0})
    for i, r in enumerate(rows, 1):
        r["sequence"] = i
    save(traces / "owner.jsonl", rows)
    for measurement in measurements["measurements"]:
        for role, worker in measurement["workers"].items():
            base = identity | {"pid": worker["pid"], "role": role}
            modules = {
                n: {"version": v, "source_sha256": "e" * 64}
                for n, v in (
                    ("torch", "2.10.0+cu128"),
                    ("transformers", "5.5.0"),
                    ("multiprocessing.synchronize", None),
                )
            }
            rows = [
                base | {"sequence": 1},
                base | {"sequence": 2, "action": "FACTORY_ENTER"},
                base | {"sequence": 3, "action": "FACTORY_READY", "modules": modules},
            ]
            save(traces / f"{measurement['trial']}_{role}.jsonl", rows)
    return path, pin, commit, traces, measurements


def test_complete_synthetic_audit(sample: tuple[Any, ...]) -> None:
    _, _, _, traces, measurements = sample
    result = audit_traces(traces, measurements, "3.12.9")
    assert result["transport_registrations"] == 90
    assert result["transport_unmatched"] == result["unmatched_registrations"] == []
    assert result["ipc_cleanup_verified"] is False


def test_child_unmatched_is_diagnostic_evidence_not_automatic_failure(
    sample: tuple[Any, ...],
) -> None:
    _, _, _, traces, measurements = sample
    path = traces / "agent_busy_agent.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows.append(
        rows[0]
        | {
            "sequence": 4,
            "action": "REGISTER",
            "resource_type": "semaphore",
            "name_sha256": "f" * 64,
            "stack": [
                {
                    "module": "synthetic.library",
                    "file": "fake.py",
                    "function": "create_lock",
                    "line": 1,
                }
            ],
        }
    )
    save(path, rows)
    result = audit_traces(traces, measurements, "3.12.9")
    assert len(result["unmatched_registrations"]) == 1
    assert result["unmatched_registrations"][0]["pid"] == 100
    assert result["transport_unmatched"] == []


@pytest.mark.parametrize(
    "mode",
    [
        "pid",
        "role",
        "python",
        "tracker",
        "implementation",
        "factory",
        "version",
        "digest",
        "missing",
        "extra",
        "done",
        "gc",
        "transport",
        "cross_pid",
        "cross_resource",
    ],
)
def test_reject_inconsistent_trace(sample: tuple[Any, ...], mode: str) -> None:
    _, _, _, traces, measurements = sample
    path = traces / "agent_busy_agent.jsonl"
    if mode in ("done", "gc", "transport"):
        path = traces / "owner.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if mode in ("pid", "role", "cross_pid"):
        for row in rows:
            row["role" if mode == "role" else "pid"] = (
                "guard" if mode == "role" else 50 if mode == "cross_pid" else 999
            )
    elif mode in ("python", "tracker", "implementation"):
        key = {
            "python": "python_version",
            "tracker": "tracker_source_sha256",
            "implementation": "implementation",
        }[mode]
        rows[0][key] = "a" * 64 if mode == "tracker" else "invalid"
    elif mode == "factory":
        rows[-1]["action"] = "FACTORY_ERROR"
    elif mode in ("version", "digest"):
        rows[-1]["modules"]["torch"]["version" if mode == "version" else "source_sha256"] = "bad"
    elif mode == "missing":
        path.unlink()
    elif mode == "extra":
        (traces / "extra.jsonl").write_text("")
    elif mode == "done":
        rows[-1]["valid"] = False
    elif mode == "gc":
        rows[-1]["gc_collected"] = -1
    elif mode == "transport":
        rows[1]["stack"][0]["module"] = "unknown"
    elif mode == "cross_resource":
        rows.append(
            rows[0]
            | {
                "sequence": 4,
                "action": "REGISTER",
                "resource_type": "semaphore",
                "name_sha256": "0" * 64,
                "stack": [{"module": "fake", "file": "fake.py", "function": "fake", "line": 1}],
            }
        )
    if mode != "missing":
        save(path, rows)
    with pytest.raises(ValueError):
        audit_traces(traces, measurements, "3.12.9")


@pytest.mark.parametrize("field", ["instrumentation", "source_commit", "python_version"])
def test_probe_identity_is_bound(sample: tuple[Any, ...], field: str) -> None:
    path, pin, commit, _, _ = sample
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["identity"][field] = "invalid"
    (path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        audit_probe(path, pin, commit, "3.12.9")
