"""Recovery boundaries: no new generation while any delivery is unresolved."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from test_request_worker_host_v1 import PAYLOAD, FakeWorker

from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.request_worker_journal_v1 import RequestWorkerJournal


def test_uncertain_request_blocks_different_task_and_request(tmp_path: Path) -> None:
    worker = FakeWorker(fail_post=True)
    with pytest.raises(APIError, match="NETWORK_ERROR"):
        RequestWorkerJournal(worker, tmp_path, "first")("POST", "/chat/completions", PAYLOAD)
    worker.fail_post = False
    with pytest.raises(APIError, match="SESSION_UNCERTAIN"):
        RequestWorkerJournal(worker, tmp_path, "second")(
            "POST", "/chat/completions", {**PAYLOAD, "request_id": "r2"})
    assert worker.posts == 1


@pytest.mark.parametrize("patch", [
    {"gpu_quiescence_attested": False}, {"quiescence_basis": "unconfirmed"},
    {"state": "CANCELLED", "cancel_requested": True},
])
def test_completion_requires_same_terminal_proof_as_recovery(
    tmp_path: Path, patch: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = FakeWorker()
    original = worker._envelope

    def envelope(payload: dict[str, Any]) -> dict[str, Any]:
        response = original(payload)
        response["request"].update(patch)
        return response

    monkeypatch.setattr(worker, "_envelope", envelope)
    with pytest.raises(APIError, match="REQUEST_UNRESOLVED"):
        RequestWorkerJournal(worker, tmp_path, "task")("POST", "/chat/completions", PAYLOAD)


def test_recovered_result_can_be_read_without_another_post(tmp_path: Path) -> None:
    worker = FakeWorker(fail_post=True)
    journal = RequestWorkerJournal(worker, tmp_path, "task")
    with pytest.raises(APIError):
        journal("POST", "/chat/completions", PAYLOAD)
    recovered = journal.recover_cached(PAYLOAD)
    assert journal("POST", "/chat/completions", PAYLOAD) == recovered
    assert worker.posts == 2


def test_recovered_delivery_allows_next_request_without_rewriting_evidence(tmp_path: Path) -> None:
    worker = FakeWorker(fail_post=True)
    journal = RequestWorkerJournal(worker, tmp_path, "first")
    with pytest.raises(APIError):
        journal("POST", "/chat/completions", PAYLOAD)
    original = {p.name: p.read_bytes() for p in journal.root.glob("*.json")}
    journal.recover_cached(PAYLOAD)
    second = RequestWorkerJournal(worker, tmp_path, "second")
    response = second("POST", "/chat/completions", {**PAYLOAD, "request_id": "r2"})
    assert response["request"]["request_id"] == "r2" and worker.posts == 3
    assert all((journal.root / name).read_bytes() == raw for name, raw in original.items())


def test_recovery_after_host_restart_binds_previously_saved_result(tmp_path: Path) -> None:
    worker = FakeWorker()
    journal = RequestWorkerJournal(worker, tmp_path, "task")
    journal("POST", "/chat/completions", PAYLOAD)
    worker.cached = {**worker.cached, "changed_since_original_delivery": True}
    with pytest.raises(APIError, match="WORKER_RESPONSE_HASH_MISMATCH"):
        RequestWorkerJournal(worker, tmp_path, "recover").recover_cached(PAYLOAD)
    assert not list(journal.root.glob("*.recovered.json"))


def test_recovery_rejects_result_changed_after_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = FakeWorker(fail_post=True)
    journal = RequestWorkerJournal(worker, tmp_path, "task")
    with pytest.raises(APIError):
        journal("POST", "/chat/completions", PAYLOAD)
    original = worker.exchange

    def exchange(method: str, path: str, payload: dict[str, Any] | None) -> Any:
        value = original(method, path, payload)
        if method == "GET":
            worker.cached = {**worker.cached, "changed_after_status": True}
        return value

    monkeypatch.setattr(worker, "exchange", exchange)
    with pytest.raises(APIError, match="WORKER_RESPONSE_HASH_MISMATCH"):
        journal.recover_cached(PAYLOAD)
    assert not list(journal.root.glob("*.recovered.json"))
