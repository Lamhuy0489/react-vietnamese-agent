"""Read-only control checks, never a claim about native GPU teardown causes."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.teardown_probe_v1 import (
    MODEL,
    MODES,
    PLAN,
    REVISION,
    STAGES,
    runtime_identity,
    source_hashes,
    worker_config,
)
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.worker_shutdown_audit_v2 import audit_event

METHOD = {
    "fast": "GRACEFUL",
    "bounded": "GRACEFUL",
    "finalizer_block": "TERMINATE",
    "finalizer_ignore_term": "KILL",
    "destructor_block": "TERMINATE",
    "thread_block": "TERMINATE",
}


def timestamp(value: Any) -> float:
    require(
        type(value) in (int, float) and math.isfinite(value) and value > 0, "positive timestamp"
    )
    return float(value)


def audit_case(value: dict[str, Any], mode: str) -> dict[str, Any]:
    require(mode in MODES, "fixed mode")
    for key, expected in dict(
        protocol="teardown_case_v1",
        mode=mode,
        synthetic=True,
        actual_model_loads=0,
        generation_error=None,
        execution_config_sha256=worker_config().identity,
    ).items():
        equal(value[key], expected, "case " + key)
    require(len(value["attempts"]) == 2 and len(value["lifecycle"]) == 1, "attempt/lifecycle count")
    response = ModelResponse(text="public", model_id=MODEL, model_revision=REVISION).model_dump(
        mode="json"
    )
    equal(value["responses"], [response, response], "unchanged synthetic responses")
    event = value["lifecycle"][0]
    audit_event(event)
    equal(event["graceful_shutdown_seconds"], 2.0, "unchanged graceful budget")
    equal(event["method"], METHOD[mode], "expected control exit")
    require(
        event["reaped"] and event["stop_received"] and event["graceful_requested"],
        "observed stop/reap",
    )
    equal(value["writer_pid"], event["pid"], "marker writer PID")
    for index, attempt in enumerate(value["attempts"], 1):
        for key, expected in dict(
            sequence=index,
            status="OK",
            pid=event["pid"],
            cold_start=index == 1,
            reaped=False,
            worker_retained=True,
            execution_config_sha256=worker_config().identity,
            request_sha256=text_hash(canonical_json([])),
            generation_sha256=text_hash(canonical_json(GenerationConfig().model_dump())),
        ).items():
            equal(attempt[key], expected, "attempt " + key)
        for key in ("load_seconds", "generation_seconds", "elapsed_seconds"):
            number = attempt[key]
            require(
                type(number) in (int, float) and math.isfinite(number) and number >= 0,
                "attempt timing " + key,
            )
    started, finished = timestamp(value["close_started"]), timestamp(value["close_finished"])
    stopped = timestamp(value["stop_received_at"])
    require(started <= stopped <= finished, "close/STOP ordering")
    requested = stopped - event["stop_received_seconds"]
    require(started <= requested <= stopped, "requested STOP within close")
    require(event["elapsed_seconds"] <= finished - started + 1e-8, "lifecycle within close")
    returned = value["serve_returned_at"]
    marks = value["stages"]
    equal(
        sorted(marks),
        sorted(s + suffix for s in STAGES for suffix in ("_entered", "_completed")),
        "stage names",
    )
    for name in STAGES:
        entered, completed = marks[name + "_entered"], marks[name + "_completed"]
        if entered is not None:
            require(timestamp(entered) <= finished, "stage within close observation")
        if completed is not None:
            require(
                entered is not None and timestamp(entered) <= timestamp(completed) <= finished,
                "stage order",
            )
    require(
        marks["destructor_entered"] is not None and marks["destructor_entered"] >= stopped,
        "destructor after STOP",
    )
    if mode == "destructor_block":
        equal(returned, -1.0, "serve has not returned")
        require(
            not event["serve_returned"]
            and marks["destructor_completed"] is None
            and marks["finalizer_entered"] is None,
            "destructor block localization",
        )
    else:
        require(
            event["serve_returned"]
            and marks["destructor_completed"] is not None
            and event["serve_returned_after_stop_seconds"] is not None,
            "serve after destructor",
        )
        require(
            stopped <= marks["destructor_completed"] <= timestamp(returned) <= finished,
            "serve order",
        )
        require(
            math.isclose(
                returned - requested,
                event["serve_returned_after_stop_seconds"],
                rel_tol=0,
                abs_tol=1e-8,
            ),
            "serve timing binding",
        )
        require(
            marks["finalizer_entered"] is not None and marks["finalizer_entered"] >= returned,
            "finalizer after serve",
        )
        if mode.startswith("finalizer_"):
            require(marks["finalizer_completed"] is None, "blocked finalizer not completed")
        else:
            require(marks["finalizer_completed"] is not None, "completed finalizer")
    if mode == "bounded":
        require(
            marks["finalizer_completed"] - marks["finalizer_entered"] >= 0.25,
            "bounded delay observed",
        )
    if mode == "thread_block":
        require(
            marks["thread_entered"] is not None
            and marks["thread_entered"] <= stopped
            and marks["thread_completed"] is None,
            "live non-daemon thread",
        )
    else:
        require(
            marks["thread_entered"] is None and marks["thread_completed"] is None,
            "no injected thread",
        )
    if METHOD[mode] != "GRACEFUL":
        require(event["exitcode"] < 0 and finished - started >= 2.0, "bounded forced stop")
    return dict(
        mode=mode,
        pid=event["pid"],
        method=event["method"],
        reaped=event["reaped"],
        stop_received=event["stop_received"],
        serve_returned=event["serve_returned"],
        close_seconds=finished - started,
        stages=marks,
    )


def audit(root: Path) -> dict[str, Any]:
    before = inventory(root)
    expected = [f"cases/r{repeat}_{mode}.json" for repeat in range(1, 4) for mode in MODES]
    equal(sorted(before), sorted(["identity.json", *expected]), "complete fixed schedule")
    equal(
        sorted(p.relative_to(root).as_posix() for p in root.rglob("*")),
        sorted(["identity.json", "cases", *expected]),
        "exact evidence tree",
    )
    identity = read_record(root / "identity.json")
    for key, value in dict(
        protocol="teardown_probe_v1",
        plan=PLAN,
        plan_sha256=hashlib.sha256(canonical_json(PLAN).encode()).hexdigest(),
        source_identity="working_tree_hashes_with_git_base",
        source_sha256=source_hashes(),
        python_runtime=runtime_identity(),
        start_method="spawn",
        synthetic=True,
        actual_model_loads=0,
        gpu_runs=0,
        test_payload_accessed=False,
    ).items():
        equal(identity[key], value, "identity " + key)
    require(
        isinstance(identity["git_base_commit"], str)
        and re.fullmatch(r"[0-9a-f]{40}", identity["git_base_commit"]) is not None,
        "Git base",
    )
    require(
        isinstance(identity["python_version"], str)
        and bool(identity["python_version"])
        and isinstance(identity["python_implementation"], str)
        and bool(identity["python_implementation"]),
        "Python identity",
    )
    rows = []
    for name in expected:
        mode = Path(name).stem.split("_", 1)[1]
        rows.append(dict(key=Path(name).stem, **audit_case(read_record(root / name), mode)))
    equal(inventory(root), before, "read-only audit")
    return dict(
        protocol="teardown_probe_audit_v1",
        valid=True,
        cases=rows,
        methods=dict(Counter(row["method"] for row in rows)),
        raw_sha256=before,
        source_sha256=identity["source_sha256"],
        git_base_commit=identity["git_base_commit"],
        actual_model_loads=0,
        gpu_runs=0,
        native_teardown_cause_identified=False,
        native_lifecycle_validated=False,
        phase5_accepted=False,
    )
