"""Explicit single retransmission to a pinned, non-evicting idempotent worker.

This host maintenance operation is separate from the frozen experiment runner.
It never creates a new request ID or changes a prompt. The original journal is
preserved; only a verified terminal response may append a recovered record.
"""

from __future__ import annotations

from typing import Any

from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.request_worker_journal_v1 import RequestWorkerJournal, _write_new
from react_agent.serving.structured_api_v1 import canonical, sha

# These exact deployed bundles contain QuiescentLifecycle's locked admission,
# full-payload conflict check and no-eviction request ledger. Other bundles need
# a separate review. In particular, this does not authorize retry across boots.
IDEMPOTENT_WORKERS = frozenset({
    "21f66f981e6d9f075b07bc306b0ef802f09b221c5ae4539b06a26f5cf5e521c6",
    "bdce7c2065d39ae4ecca4521cc2c44c80cf8fb740f6bf70eba27c04d743fba68",
})


def reconcile_unknown_once(
    journal: RequestWorkerJournal, payload: dict[str, Any],
) -> dict[str, Any]:
    """Resend exact bytes once after UNKNOWN, with same-boot deduplication.

    UNKNOWN alone is not terminal proof. A delayed original may arrive after
    the status query: the same-ID/hash worker admission still executes at most
    once. A running request, changed boot, failed delivery or unverified terminal
    remains blocked. The retry claim survives host interruption and cannot be
    reset by selecting a different report directory.
    """
    if journal.identity.get("worker_sha256") not in IDEMPOTENT_WORKERS:
        raise APIError("IDEMPOTENCY_NOT_REVIEWED")
    request_id = payload.get("request_id")
    if not isinstance(request_id, str):
        raise APIError("JOURNAL_REQUEST_ID_REQUIRED")
    digest = sha(canonical(payload).encode())
    with journal._exclusive():
        prior = journal._scan().get(request_id)
        if prior is None:
            raise APIError("REQUEST_NOT_ATTEMPTED")
        started, finished, recovered = prior
        if (started is None or finished is None or recovered is not None
                or finished.get("state") != "uncertain"
                or started.get("task_id") != journal.task_id):
            raise APIError("RETRANSMISSION_NOT_ALLOWED")
        journal._validate_record(started, request_id=request_id, digest=digest, state="started")
        journal._validate_record(finished, request_id=request_id, digest=digest, state="uncertain")
        health = journal.transport.exchange("GET", "/models", None)
        if (health.status != 200 or health.payload.get("identity") != journal.identity
                or health.payload.get("status") != "READY"):
            raise APIError("WORKER_BOOT_CHANGED_OR_UNREADY")
        status = journal.transport.exchange("GET", f"/requests/{request_id}", None)
        if (status.status != 404
                or status.payload != {"error": {"code": "REQUEST_UNKNOWN"}}):
            raise APIError("UNKNOWN_REQUIRED", status.status)
        claims = journal.root.parent / "_retransmissions" / journal.root.name
        if any(p.is_symlink() for p in (claims, *claims.parents)):
            raise APIError("UNSAFE_RECOVERY_PATH")
        claims.mkdir(parents=True, exist_ok=True)
        claim = claims / f"{request_id}.claim.json"
        record = {"protocol": "phase5_same_request_retransmission_v1",
                  "identity": journal.identity, "task_id": journal.task_id,
                  "request_id": request_id, "request_sha256": digest,
                  "original_started_sha256": sha(canonical(started).encode()),
                  "original_finished_sha256": sha(canonical(finished).encode()),
                  "max_retransmissions": 1, "semantic_retry_authorized": False}
        try:
            _write_new(claim, record)
        except FileExistsError:
            raise APIError("RETRANSMISSION_BUDGET_EXHAUSTED") from None
        # Claim is durable before network I/O. If this operation is interrupted,
        # only the existing cached-recovery route may subsequently be used.
        exchange = journal.transport.exchange("POST", "/chat/completions", payload)
        journal._validate_completion(request_id, digest, exchange.status, exchange.payload)
        _write_new(claims / f"{request_id}.result.json", {
            **record, "http_status": exchange.status, "response": exchange.payload,
            "response_sha256": sha(canonical(exchange.payload).encode()),
            "execution_resolved": True,
        })
        journal._save_finished(request_id, digest, "recovered", exchange.status,
                               exchange.payload, recovered=True)
        return exchange.payload
