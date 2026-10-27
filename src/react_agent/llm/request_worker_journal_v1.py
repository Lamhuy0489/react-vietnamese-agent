"""Durable, fail-closed host journal for request-worker v3.

The journal is scoped to the static worker identity, while each record also
contains the boot instance id.  Consequently a fresh worker boot cannot evade
an uncertain request by selecting a new directory.  Recovery is explicit: a
terminal status is checked first, then the identical request is sent only to
retrieve the worker's cached result.  No semantic retry is authorized.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Protocol

from react_agent.llm.http_diagnostic_v1 import APIError
from react_agent.llm.request_reconciliation_v3 import verify_terminal_status
from react_agent.llm.request_worker_transport_v1 import WorkerExchange
from react_agent.serving.structured_api_v1 import canonical, sha

PROTOCOL = "react-vn-request-worker-journal-v1"
REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
TERMINAL = frozenset({"SUCCEEDED", "FAILED", "CANCELLED"})


class WorkerTransport(Protocol):
    @property
    def identity(self) -> Mapping[str, str] | None: ...

    def exchange(self, method: str, path: str,
                 payload: dict[str, Any] | None) -> WorkerExchange: ...

    def __call__(self, method: str, path: str,
                 payload: dict[str, Any] | None) -> dict[str, Any]: ...


def _write_new(path: Path, value: dict[str, Any]) -> None:
    """Create and fsync one immutable private record."""
    with path.open("x", encoding="utf-8") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(canonical(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise APIError("SESSION_UNCERTAIN")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError, RecursionError):
        raise APIError("SESSION_UNCERTAIN") from None
    if not isinstance(value, dict):
        raise APIError("SESSION_UNCERTAIN")
    return value


def _request_digest(payload: dict[str, Any]) -> str:
    return sha(canonical(payload).encode("utf-8"))


def _copy(value: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(canonical(value))
    if not isinstance(result, dict):
        raise APIError("SESSION_UNCERTAIN")
    return result


class RequestWorkerJournal:
    """One immutable request ledger around :class:`RequestWorkerHTTPS`."""

    def __init__(self, transport: WorkerTransport, root: Path, task_id: str) -> None:
        if transport.identity is None:
            raise ValueError("transport must be probed before journal creation")
        if not isinstance(task_id, str) or not 1 <= len(task_id) <= 256:
            raise ValueError("explicit task identity required")
        self.transport = transport
        self.identity = dict(transport.identity)
        self.task_id = task_id
        scope = {key: self.identity[key] for key in sorted(self.identity) if key != "instance_id"}
        self.scope_identity = scope
        self.root = root.resolve() / sha(canonical(scope).encode("utf-8"))
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise ValueError("journal directory must not be a link")
        self._cache: dict[str, dict[str, Any]] = {}

    @contextmanager
    def _exclusive(self) -> Iterator[None]:
        descriptor = os.open(self.root / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise APIError("SESSION_BUSY") from None
            yield
        finally:
            os.close(descriptor)

    def _paths(self, request_id: str) -> tuple[Path, Path]:
        return (self.root / f"{request_id}.started.json",
                self.root / f"{request_id}.finished.json")

    def _validate_record(self, record: dict[str, Any], *, request_id: str,
                         digest: str, state: str | None = None) -> None:
        if (record.get("protocol") != PROTOCOL or record.get("identity") != self.identity
                or record.get("request_id") != request_id
                or record.get("request_sha256") != digest
                or (state is not None and record.get("state") != state)):
            raise APIError("SESSION_UNCERTAIN")

    def _scan(self) -> dict[str, tuple[dict[str, Any] | None, dict[str, Any] | None,
                                         dict[str, Any] | None]]:
        """Validate every prior record before admitting any new POST."""
        result: dict[str, tuple[dict[str, Any] | None, dict[str, Any] | None,
                                 dict[str, Any] | None]] = {}
        for path in self.root.iterdir():
            if path.name == ".lock":
                continue
            if path.is_symlink() or not path.is_file():
                raise APIError("SESSION_UNCERTAIN")
            match = re.fullmatch(
                r"([A-Za-z0-9_-]{1,80})\.(started|finished|recovered)\.json", path.name)
            if match is None:
                raise APIError("SESSION_UNCERTAIN")
            request_id, kind = match.groups()
            started, finished, recovered = result.get(request_id, (None, None, None))
            record = _read(path)
            if kind == "started":
                if started is not None:
                    raise APIError("SESSION_UNCERTAIN")
                result[request_id] = (record, finished, recovered)
            elif kind == "finished":
                if finished is not None:
                    raise APIError("SESSION_UNCERTAIN")
                result[request_id] = (started, record, recovered)
            else:
                if recovered is not None:
                    raise APIError("SESSION_UNCERTAIN")
                result[request_id] = (started, finished, record)
        for request_id, (started, finished, recovered) in result.items():
            if not started or finished is None:
                raise APIError("SESSION_UNCERTAIN")
            digest = started.get("request_sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise APIError("SESSION_UNCERTAIN")
            self._validate_record(started, request_id=request_id, digest=digest, state="started")
            if finished.get("state") not in {"uncertain", "response_received", "recovered"}:
                raise APIError("SESSION_UNCERTAIN")
            self._validate_record(finished, request_id=request_id, digest=digest)
            if finished.get("state") in {"response_received", "recovered"}:
                if (type(finished.get("http_status")) is not int
                        or not 200 <= finished["http_status"] <= 599
                        or not isinstance(finished.get("response_sha256"), str)
                        or not re.fullmatch(r"[0-9a-f]{64}", finished["response_sha256"])):
                        raise APIError("SESSION_UNCERTAIN")
            if recovered is not None:
                if recovered.get("state") != "recovered":
                    raise APIError("SESSION_UNCERTAIN")
                self._validate_record(recovered, request_id=request_id, digest=digest)
                if (type(recovered.get("http_status")) is not int
                        or not 200 <= recovered["http_status"] <= 599
                        or not isinstance(recovered.get("response_sha256"), str)
                        or not re.fullmatch(r"[0-9a-f]{64}", recovered["response_sha256"])):
                    raise APIError("SESSION_UNCERTAIN")
        return result

    def _validate_completion(self, request_id: str, digest: str,
                             exchange_status: int, response: dict[str, Any]) -> None:
        if response.get("identity") != self.identity:
            raise APIError("WORKER_RESPONSE_IDENTITY")
        status = response.get("request")
        if (not isinstance(status, dict)
                or status.get("instance_id") != self.identity["instance_id"]):
            raise APIError("WORKER_REQUEST_IDENTITY")
        if status.get("request_id") != request_id or status.get("request_sha256") != digest:
            raise APIError("WORKER_REQUEST_HASH_MISMATCH")
        if status.get("state") not in TERMINAL or status.get("engine_returned") is not True:
            raise APIError("REQUEST_UNRESOLVED")
        if status.get("engine_active") is not False or status.get("durable") is not True:
            raise APIError("REQUEST_UNRESOLVED")
        if status.get("instance_retired") is not False:
            raise APIError("WORKER_INSTANCE_RETIRED")
        try:
            verify_terminal_status(identity=self.identity, request_id=request_id,
                                   request_sha256=digest, response=response)
        except ValueError as exc:
            raise APIError("REQUEST_UNRESOLVED") from exc
        code = status.get("http_status")
        result = response.get("result")
        expected = status.get("response_sha256")
        if (type(code) is not int or code != exchange_status or not isinstance(result, dict)
                or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected)
                or sha(canonical(result).encode("utf-8")) != expected):
            raise APIError("WORKER_RESPONSE_HASH_MISMATCH")

    def _save_finished(self, request_id: str, digest: str, state: str,
                       status: int, response: dict[str, Any], *, recovered: bool = False) -> None:
        started, finished = self._paths(request_id)
        if recovered:
            finished = finished.with_name(finished.name.replace(".finished.", ".recovered."))
        del started  # Keep the named pair obvious at call sites; never overwrite started.
        _write_new(finished, {"protocol": PROTOCOL, "identity": self.identity,
            "task_id": self.task_id, "request_id": request_id, "request_sha256": digest,
            "state": state, "http_status": status,
            "response_sha256": sha(canonical(response).encode("utf-8"))})

    def __call__(self, method: str, path: str,
                 payload: dict[str, Any] | None) -> dict[str, Any]:
        if (method, path) == ("GET", "/models"):
            return self.transport(method, path, payload)
        if method != "POST" or path != "/chat/completions" or not isinstance(payload, dict):
            raise APIError("JOURNAL_ROUTE_REFUSED")
        request_id = payload.get("request_id")
        if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
            raise APIError("JOURNAL_REQUEST_ID_REQUIRED")
        digest = _request_digest(payload)
        with self._exclusive():
            records = self._scan()
            # A different task/request ID must not bypass lost-delivery evidence.
            if any(finished is None or (
                    finished.get("state") == "uncertain" and recovered is None)
                    for _, finished, recovered in records.values()):
                raise APIError("SESSION_UNCERTAIN")
            prior = records.get(request_id)
            if prior is not None:
                started, finished, recovered = prior
                if started is None:
                    raise APIError("SESSION_UNCERTAIN")
                self._validate_record(started, request_id=request_id, digest=digest,
                                      state="started")
                if recovered is not None:
                    if request_id in self._cache:
                        return _copy(self._cache[request_id])
                    raise APIError("RESULT_RECOVERY_REQUIRED")
                if (finished is not None
                        and finished.get("state") in {"uncertain", "response_received"}):
                    if request_id in self._cache:
                        return _copy(self._cache[request_id])
                    raise APIError("RESULT_RECOVERY_REQUIRED")
                if finished is not None and finished.get("state") == "recovered":
                    if request_id not in self._cache:
                        raise APIError("RESULT_RECOVERY_REQUIRED")
                    return _copy(self._cache[request_id])
                raise APIError("SESSION_UNCERTAIN")
            started_path, _ = self._paths(request_id)
            _write_new(started_path, {"protocol": PROTOCOL, "identity": self.identity,
                "task_id": self.task_id, "request_id": request_id,
                "request_sha256": digest, "state": "started"})
            try:
                exchange = self.transport.exchange("POST", "/chat/completions", payload)
                self._validate_completion(request_id, digest, exchange.status, exchange.payload)
            except BaseException:
                try:
                    self._save_finished(request_id, digest, "uncertain", 0, {})
                except OSError:
                    pass
                raise
            self._save_finished(request_id, digest, "response_received",
                                exchange.status, exchange.payload)
            self._cache[request_id] = _copy(exchange.payload)
            return _copy(exchange.payload)

    def recover_cached(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Resolve a prior attempt only after status and request hashes agree."""
        request_id = payload.get("request_id") if isinstance(payload, dict) else None
        if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
            raise APIError("JOURNAL_REQUEST_ID_REQUIRED")
        digest = _request_digest(payload)
        with self._exclusive():
            records = self._scan()
            prior = records.get(request_id)
            if prior is None:
                raise APIError("REQUEST_NOT_ATTEMPTED")
            started, finished, recovered = prior
            if started is None:
                raise APIError("SESSION_UNCERTAIN")
            self._validate_record(started, request_id=request_id, digest=digest,
                                  state="started")
            if (finished is None
                    or finished.get("state") not in {
                        "uncertain", "response_received", "recovered"}):
                raise APIError("SESSION_UNCERTAIN")
            status_exchange = self.transport.exchange("GET", f"/requests/{request_id}", None)
            if status_exchange.status != 200:
                raise APIError("STATUS_UNAVAILABLE", status_exchange.status)
            status_response = status_exchange.payload
            try:
                verified = verify_terminal_status(identity=self.identity, request_id=request_id,
                                                  request_sha256=digest, response=status_response)
            except ValueError as exc:
                raise APIError("REQUEST_UNRESOLVED") from exc
            exchange = self.transport.exchange("POST", "/chat/completions", payload)
            self._validate_completion(request_id, digest, exchange.status, exchange.payload)
            actual = exchange.payload["request"]
            if any(actual.get(key) != verified[key] for key in (
                    "state", "http_status", "response_sha256")):
                raise APIError("WORKER_RESPONSE_HASH_MISMATCH")
            recorded = recovered or finished
            if recorded.get("state") in {"response_received", "recovered"} and (
                    recorded["response_sha256"] != sha(canonical(exchange.payload).encode())
                    or recorded["http_status"] != exchange.status):
                raise APIError("WORKER_RESPONSE_HASH_MISMATCH")
            if recovered is None:
                self._save_finished(request_id, digest, "recovered", exchange.status,
                                    exchange.payload, recovered=True)
            self._cache[request_id] = _copy(exchange.payload)
            return _copy(exchange.payload)
