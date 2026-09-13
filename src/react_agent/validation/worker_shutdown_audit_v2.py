"""Deterministic consistency checks for synthetic acknowledged-shutdown evidence."""

import math
from typing import Any

from react_agent.validation.guard_probe_audit_v2 import require


def audit_event(event: dict[str, Any]) -> None:
    require(event["schema_version"] == "worker_shutdown_v2", "shutdown schema")
    require(type(event["sequence"]) is int and event["sequence"] > 0, "event sequence")
    for key in ("reaped", "graceful_requested", "stop_received", "serve_returned"):
        require(type(event[key]) is bool, "boolean " + key)
    for key in ("elapsed_seconds", "graceful_shutdown_seconds"):
        value = event[key]
        require(type(value) in (int, float) and math.isfinite(value) and value > 0, key)
    for key in ("stop_received_seconds", "serve_returned_after_stop_seconds"):
        value = event[key]
        if value is not None:
            require(
                type(value) in (int, float)
                and math.isfinite(value)
                and 0 <= value <= event["elapsed_seconds"],
                key,
            )
            require(event["graceful_requested"], "timing requires stop request")
    require(
        event["stop_received"] == (event["stop_received_seconds"] is not None),
        "stop acknowledgement/timing",
    )
    returned_after = event["serve_returned_after_stop_seconds"]
    if returned_after is not None:
        require(event["serve_returned"], "return timing requires observation")
    if event["stop_received"] and returned_after is not None:
        require(event["stop_received_seconds"] <= returned_after, "stop before return")
    method, code, pid = event["method"], event["exitcode"], event["pid"]
    require(method in {"GRACEFUL", "EXITED", "TERMINATE", "KILL", "NOT_STARTED"}, "method")
    if method == "NOT_STARTED":
        require(pid is None and code is None and event["reaped"], "unstarted process")
        require(not event["graceful_requested"] and not event["serve_returned"], "no unstarted ACK")
    else:
        require(type(pid) is int and pid > 0, "worker PID")
        require((type(code) is int) if event["reaped"] else code is None, "exit/reaped")
    if method == "GRACEFUL":
        require(
            event["reaped"] and code == 0 and event["stop_received"] and returned_after is not None,
            "acknowledged normal exit",
        )
