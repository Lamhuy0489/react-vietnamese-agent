"""Validate fixed milestone records; classify observed boundary, never native cause."""

from __future__ import annotations

import math
from typing import Any

from react_agent.security_v1.exit_milestones_v1 import EVENTS, PHASES
from react_agent.validation.context_stress_audit_v1 import equal
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.worker_shutdown_audit_v2 import audit_event


def audit_milestones(
    record: dict[str, Any],
    lifecycle: dict[str, Any],
    *,
    runtime: dict[str, str],
    config_sha256: str,
    observed_until: float,
) -> str:
    equal(
        sorted(record),
        sorted(("protocol", "runtime", "execution_config_sha256", "events")),
        "milestone fields",
    )
    equal(record["protocol"], "exit_milestones_v1", "milestone protocol")
    equal(record["runtime"], runtime, "interpreter identity")
    equal(record["execution_config_sha256"], config_sha256, "config identity")
    audit_event(lifecycle)
    require(lifecycle["reaped"], "milestones require reaped worker")
    require(type(observed_until) is float and math.isfinite(observed_until), "observation end")
    events = record["events"]
    equal(sorted(events), sorted(EVENTS), "fixed events")
    latest = 0.0
    previous_finished = True
    boundary = "unobserved"
    raised = False
    for phase in PHASES:
        entered, returned, error = (events[phase + "_" + e] for e in ("enter", "return", "error"))
        require(not (returned is not None and error is not None), "exclusive completion")
        if entered is None:
            require(returned is None and error is None, "completion without entry")
            previous_finished = False
            continue
        require(previous_finished, "phase entered before predecessor completed")
        for event in (entered, returned if returned is not None else error):
            if event is None:
                continue
            equal(sorted(event), sorted(("at", "pid", "non_daemon_threads")), "event fields")
            require(type(event["pid"]) is int and event["pid"] > 0, "event PID type")
            equal(event["pid"], lifecycle["pid"], "event PID binding")
            count, stamp = event["non_daemon_threads"], event["at"]
            require(type(count) is int and count >= 0, "thread count")
            require(type(stamp) is float and math.isfinite(stamp), "timestamp type")
            require(0 < stamp <= observed_until and stamp >= latest, "milestone order")
            latest = stamp
        previous_finished = returned is not None or error is not None
        raised = raised or error is not None
        boundary = phase + ("_completed" if previous_finished else "_entered_only")
    if boundary == "threads_completed":
        boundary = "observed_stages_raised" if raised else "observed_stages_returned"
    if lifecycle["method"] == "GRACEFUL":
        require(boundary == "observed_stages_returned", "graceful requires full observation")
    return boundary
