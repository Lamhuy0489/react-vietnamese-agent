"""Dropped and delayed requests against the real worker admission implementation."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.request_worker_journal_v1 import RequestWorkerJournal
from react_agent.llm.request_worker_transport_v1 import WorkerExchange
from react_agent.serving.quiescent_engine_v3 import EngineOutcome
from react_agent.serving.request_http_v3 import QuiescentHTTP
from react_agent.serving.structured_api_v1 import ServiceError, canonical

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from reconcile_phase5_request_v1 import IDEMPOTENT_WORKERS, reconcile_unknown_once  # noqa: E402

BODY = {"model": "synthetic", "request_id": "one",
        "messages": [{"role": "user", "content": "synthetic public input"}]}


class Transport:
    def __init__(self, root: Path) -> None:
        self.calls = 0
        self.posts = 0
        self.drop = True
        self.late_original = False
        self.changed_boot = False
        self.app = QuiescentHTTP(api_key="x" * 32, identity={
            "session_id": "session", "source_commit": "a" * 40,
            "worker_sha256": sorted(IDEMPOTENT_WORKERS)[0],
            "model_revision": "sha256:" + "b" * 64,
        }, role="agent", model="synthetic", root=root, engine=self.engine)
        self.identity = dict(self.app._identity)

    def engine(self, spec: Any, stop: Any) -> EngineOutcome:
        self.calls += 1
        return EngineOutcome({"answer": "fixed result"}, 200, True, True)

    def exchange(self, method: str, path: str, payload: Any) -> WorkerExchange:
        if method == "POST":
            self.posts += 1
            if self.drop:
                raise APIError("NETWORK_ERROR")
            if self.late_original:
                self.app.lifecycle.complete(self.identity["instance_id"], BODY)
        try:
            body, code = self.app.dispatch(method, "/v1" + path, "Bearer " + "x" * 32,
                "different-boot" if self.changed_boot else self.identity["instance_id"],
                canonical(payload).encode() if payload is not None else b"")
            if self.changed_boot and path == "/models":
                body["identity"]["instance_id"] = "different-boot"
            return WorkerExchange(code, body)
        except ServiceError as exc:
            return WorkerExchange(exc.status, {"error": {"code": exc.code}})

    def __call__(self, method: str, path: str, payload: Any) -> dict[str, Any]:
        return self.exchange(method, path, payload).payload


def pending(tmp_path: Path) -> tuple[Transport, RequestWorkerJournal]:
    transport = Transport(tmp_path / "worker")
    journal = RequestWorkerJournal(transport, tmp_path / "journal", "task")
    with pytest.raises(APIError, match="NETWORK_ERROR"):
        journal("POST", "/chat/completions", BODY)
    transport.drop = False
    return transport, journal


@pytest.mark.parametrize("late_original", [False, True])
def test_exact_retransmission_executes_once_and_keeps_originals(tmp_path, late_original):
    transport, journal = pending(tmp_path)
    original = {p: p.read_bytes() for p in journal.root.glob("*.json")}
    transport.late_original = late_original
    result = reconcile_unknown_once(journal, BODY)
    assert result["result"] == {"answer": "fixed result"}
    assert transport.calls == 1 and transport.posts == 2
    assert all(p.read_bytes() == raw for p, raw in original.items())
    recovered = json.loads(next(journal.root.glob("*.recovered.json")).read_text())
    assert recovered["task_id"] == "task" and recovered["state"] == "recovered"
    transport.late_original = False
    journal("POST", "/chat/completions", {**BODY, "request_id": "two"})
    assert transport.calls == 2


def test_changed_payload_never_reaches_worker(tmp_path):
    transport, journal = pending(tmp_path)
    with pytest.raises(APIError, match="SESSION_UNCERTAIN"):
        reconcile_unknown_once(journal, {**BODY, "seed": 43})
    assert transport.posts == 1 and transport.calls == 0


def test_changed_boot_never_retransmits(tmp_path):
    transport, journal = pending(tmp_path)
    transport.changed_boot = True
    with pytest.raises(APIError, match="WORKER_BOOT_CHANGED_OR_UNREADY"):
        reconcile_unknown_once(journal, BODY)
    assert transport.posts == 1


def test_second_network_failure_exhausts_budget_and_blocks_new_task(tmp_path):
    transport, journal = pending(tmp_path)
    transport.drop = True
    with pytest.raises(APIError, match="NETWORK_ERROR"):
        reconcile_unknown_once(journal, BODY)
    transport.drop = False
    restarted = RequestWorkerJournal(transport, tmp_path / "journal", "task")
    with pytest.raises(APIError, match="RETRANSMISSION_BUDGET_EXHAUSTED"):
        reconcile_unknown_once(restarted, BODY)
    with pytest.raises(APIError, match="SESSION_UNCERTAIN"):
        restarted("POST", "/chat/completions", {**BODY, "request_id": "two"})
    assert transport.posts == 2 and not list(journal.root.glob("*.recovered.json"))


def test_terminal_result_requires_cached_recovery_not_unknown_retry(tmp_path):
    transport, journal = pending(tmp_path)
    transport.app.lifecycle.complete(transport.identity["instance_id"], BODY)
    with pytest.raises(APIError, match="UNKNOWN_REQUIRED"):
        reconcile_unknown_once(journal, BODY)
    assert transport.posts == 1 and transport.calls == 1


def test_wrong_task_or_unreviewed_worker_is_refused(tmp_path):
    transport, journal = pending(tmp_path)
    wrong = RequestWorkerJournal(transport, tmp_path / "journal", "another")
    with pytest.raises(APIError, match="RETRANSMISSION_NOT_ALLOWED"):
        reconcile_unknown_once(wrong, BODY)
    journal.identity["worker_sha256"] = "c" * 64
    with pytest.raises(APIError, match="IDEMPOTENCY_NOT_REVIEWED"):
        reconcile_unknown_once(journal, BODY)
    assert transport.posts == 1
