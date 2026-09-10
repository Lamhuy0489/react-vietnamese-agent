"""Synthetic receipt/ordering mutations; native package exercised in exact preflight."""

import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from react_agent.llm.worker_progress_v1 import STD_SHA256, VERSION
from react_agent.validation.pair_progress_audit_v1 import audit_progress


@pytest.fixture
def progress(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, ...]:
    monkeypatch.syspath_prepend(str(Path(__file__).parent))
    fixture = importlib.import_module("test_pair_ipc_audit_v1")
    probe, _, commit, traces, result = fixture.sample.__wrapped__(tmp_path, monkeypatch)
    from react_agent.validation.pair_ipc_audit_v1 import audit_traces

    tracker = audit_traces(traces, result, "3.12.9")
    owner = tracker["observations"]["owner.jsonl"]["pid"]
    (tmp_path / "progress_identity.json").write_text(
        json.dumps(
            {
                "protocol": "pair_progress_v1",
                "source_commit": commit,
                "owner_pid": owner,
            }
        )
    )
    policies = tmp_path / "progress_policy"
    policies.mkdir()
    for name, row in tracker["observations"].items():
        if name == "owner.jsonl":
            continue
        (policies / (Path(name).stem + ".json")).write_text(
            json.dumps(
                {
                    "pid": row["pid"],
                    "role": row["role"],
                    "policy": {
                        "protocol": "worker_thread_progress_v1",
                        "tqdm_version": VERSION,
                        "tqdm_std_sha256": STD_SHA256,
                        "lock": "threading.RLock",
                        "scope": "one daemon spawn worker; no descendant processes",
                    },
                }
            )
        )
        path = traces / name
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[-1]["modules"].update(
            {
                "tqdm": {"version": VERSION, "source_sha256": "e" * 64},
                "tqdm.std": {"version": None, "source_sha256": STD_SHA256},
            }
        )
        fixture.save(path, rows)
    probe.rename(tmp_path / "pair_cancellation")
    for path in (tmp_path / "pair_cancellation").glob("*/ready.json"):
        value = json.loads(path.read_text())
        value["pair"]["owner_pid"] = owner
        path.write_text(json.dumps(value))
    return tmp_path, tracker, commit


def test_progress_receipts_bind_all_workers(progress: tuple[Any, ...]) -> None:
    result = audit_progress(*progress)
    assert result["prevention_observed"] and result["owner_balanced"]
    assert result["policy_receipts_verified"] == 6
    assert not result["ipc_cleanup_verified"]


@pytest.mark.parametrize(
    "mode", ["pid", "role", "policy", "missing", "extra", "owner", "version", "hash"]
)
def test_progress_rejects_mismatches(progress: tuple[Any, ...], mode: str) -> None:
    root, _, _ = progress
    path = root / "progress_policy/agent_busy_agent.json"
    value = json.loads(path.read_text())
    if mode in ("pid", "role", "policy"):
        value[mode] = "wrong"
        path.write_text(json.dumps(value))
    elif mode == "missing":
        path.unlink()
    elif mode == "extra":
        (path.parent / "extra.json").write_text("{}")
    elif mode == "owner":
        (root / "progress_identity.json").write_text("{}")
    else:
        path = root / "tracker/agent_busy_agent.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        item = rows[-1]["modules"]["tqdm" if mode == "version" else "tqdm.std"]
        item["version" if mode == "version" else "source_sha256"] = "wrong"
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    with pytest.raises(ValueError):
        audit_progress(*progress)


def test_nonzero_creation_is_preserved_as_miss(progress: tuple[Any, ...]) -> None:
    _, tracker, _ = progress
    tracker["observations"]["agent_busy_agent.jsonl"]["register_calls"] = 1
    assert not audit_progress(*progress)["prevention_observed"]


@pytest.fixture
def worker(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    return importlib.import_module("run_phase5_pair_progress_worker")


def test_policy_before_load_and_receipt_bound(
    worker: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    events = []
    path = tmp_path / "policy.json"

    def configure() -> dict[str, str]:
        events.append("configure")
        return {"protocol": "synthetic"}

    def load() -> Any:
        assert json.loads(path.read_text())["pid"] == os.getpid()
        events.append("load")
        return SimpleNamespace(model_id="synthetic")

    monkeypatch.setattr(worker, "configure_worker_progress", configure)
    factory = worker.ProgressReceiptFactory(load, path, "agent")
    assert not events and not path.exists()
    assert factory().model_id == "synthetic"
    assert events == ["configure", "load"]


def test_progress_failure_never_loads(
    worker: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail() -> Any:
        raise ValueError("unsupported")

    def load() -> Any:
        raise AssertionError("must not load")

    monkeypatch.setattr(worker, "configure_worker_progress", fail)
    with pytest.raises(ValueError):
        worker.ProgressReceiptFactory(load, tmp_path / "policy.json", "agent")()
    assert not list(tmp_path.iterdir())


def test_pairs_wrap_only_lazy_factories(worker: Any, tmp_path: Path) -> None:
    traces, policies = tmp_path / "traces", tmp_path / "policies"
    traces.mkdir()
    policies.mkdir()
    pair = worker.ProgressPairs(worker.CancellationPairs(), traces, policies)(
        "agent_busy", tmp_path
    )
    try:
        for role, backend in pair._workers.items():
            assert backend._process is None
            assert isinstance(backend.factory, worker.TracedFactory)
            assert isinstance(backend.factory.factory, worker.ProgressReceiptFactory)
            assert backend.factory.factory.role == role
        assert not list(traces.iterdir()) and not list(policies.iterdir())
    finally:
        pair.close()
