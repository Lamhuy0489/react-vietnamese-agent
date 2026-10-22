"""Durable delivery uncertainty controls, entirely offline."""
import fcntl
import json
import os
import pickle

import pytest

from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.session_journal_v1 import SessionJournal
from react_agent.llm.structured_session_factory_v1 import StructuredSessionFactory

IDENTITY = {"session_id": "synthetic-session", "role": "guard"}


def test_response_and_duplicate_across_fresh_tasks(tmp_path):
    calls = []
    def transport(*args):
        calls.append(args)
        return {"response": "synthetic"}
    first = SessionJournal(transport, tmp_path, IDENTITY, "one")
    assert first("POST", "/chat/completions", {"request_id": "r1"}) == {"response": "synthetic"}
    second = SessionJournal(transport, tmp_path, IDENTITY, "two")
    with pytest.raises(APIError, match="ALREADY_ATTEMPTED"):
        second("POST", "/chat/completions", {"request_id": "r1"})
    second("POST", "/chat/completions", {"request_id": "r2"})
    assert len(calls) == 2
    assert json.loads((first.root / "r1.started.json").read_text())["task_id"] == "one"
    assert json.loads((first.root / "r2.started.json").read_text())["task_id"] == "two"


@pytest.mark.parametrize("error", [TimeoutError, KeyboardInterrupt, RuntimeError])
def test_failed_post_blocks_new_task_without_logging_error_text(tmp_path, error):
    calls = []
    def broken(*args):
        calls.append(args)
        raise error("SYNTHETIC_SECRET")
    first = SessionJournal(broken, tmp_path, IDENTITY, "one")
    with pytest.raises(error):
        first("POST", "/chat/completions", {"request_id": "r1"})
    second = SessionJournal(broken, tmp_path, IDENTITY, "two")
    with pytest.raises(APIError, match="UNCERTAIN"):
        second("POST", "/chat/completions", {"request_id": "r2"})
    assert len(calls) == 1
    assert all("SYNTHETIC_SECRET" not in p.read_text() for p in first.root.glob("*.json"))


def test_http_530_delivery_failure_is_uncertain_and_never_replayed(tmp_path):
    """A tunnel status cannot prove whether the remote generation ran.

    The v1 worker has no authenticated request-status endpoint, so preserving
    the attempt and refusing every later POST is the only safe behaviour.  In
    particular, a different task/request ID must not turn HTTP 530 into a
    semantic retry or bypass the blocked session.
    """
    calls = []

    def broken(*args):
        calls.append(args)
        raise APIError("HTTP_ERROR", 530)

    first = SessionJournal(broken, tmp_path, IDENTITY, "closure")
    with pytest.raises(APIError, match="HTTP_ERROR") as caught:
        first("POST", "/chat/completions", {"request_id": "r1"})
    assert caught.value.status == 530
    second = SessionJournal(broken, tmp_path, IDENTITY, "next")
    with pytest.raises(APIError, match="UNCERTAIN"):
        second("POST", "/chat/completions", {"request_id": "r2"})
    assert len(calls) == 1
    records = list(first.root.glob("*.json"))
    assert len(records) == 2
    assert all("HTTP_ERROR" not in path.read_text() for path in records)


@pytest.mark.parametrize("terminal", [None, "{", '{"state":"response_received"}'])
def test_process_death_or_partial_write_fails_closed(tmp_path, terminal):
    calls = []
    journal = SessionJournal(lambda *a: calls.append(a), tmp_path, IDENTITY, "one")
    (journal.root / "r1.started.json").write_text('{"state":"started"}')
    if terminal is not None:
        (journal.root / "r1.finished.json").write_text(terminal)
    with pytest.raises(APIError, match="UNCERTAIN"):
        journal("POST", "/chat/completions", {"request_id": "r2"})
    assert not calls


def test_concurrent_session_is_not_queued(tmp_path):
    calls = []
    journal = SessionJournal(lambda *a: calls.append(a), tmp_path, IDENTITY, "one")
    descriptor = os.open(journal.root / ".lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(APIError, match="BUSY"):
            journal("POST", "/chat/completions", {"request_id": "r1"})
    finally:
        os.close(descriptor)
    assert not calls and not list(journal.root.glob("*.json"))


def test_probe_cannot_clear_uncertainty(tmp_path):
    journal = SessionJournal(lambda *a: {"healthy": True}, tmp_path, IDENTITY, "one")
    (journal.root / "r1.started.json").write_text("{")
    assert journal("GET", "/models", None) == {"healthy": True}
    with pytest.raises(APIError, match="UNCERTAIN"):
        journal("POST", "/chat/completions", {"request_id": "r2"})


def test_factory_pickle_has_no_credentials_and_modified_file_rejected(tmp_path, monkeypatch):
    pair = {"models": [{"role": "guard", "id": "guard", "model_revision": "sha256:r",
        "session_id": "s", "source_commit": "c", "api_key": "SYNTHETIC_KEY",
        "endpoint": "https://synthetic.invalid/v1"}]}
    (tmp_path / "pair_endpoints.json").write_text(json.dumps(pair))
    (tmp_path / "guard_live_metadata.json").write_text('{"worker_sha256":"w"}')
    factory = StructuredSessionFactory.from_directory(
        tmp_path, tmp_path / "journal", "task", "guard")
    serialized = pickle.dumps(factory)
    assert b"SYNTHETIC_KEY" not in serialized and b"synthetic.invalid" not in serialized
    assert pickle.loads(serialized) == factory  # noqa: S301 - generated local test object
    (tmp_path / "pair_endpoints.json").write_text("{}")
    with pytest.raises(APIError, match="FILES_CHANGED"):
        factory()
