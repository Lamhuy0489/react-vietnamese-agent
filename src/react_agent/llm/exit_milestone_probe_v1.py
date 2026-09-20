"""Fixed synthetic controls for the opt-in exit observer, no model inference."""

from __future__ import annotations

import ctypes
import hashlib
import math
import multiprocessing as mp
import re
import time
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.teardown_probe_v1 import (
    MODEL,
    MODES,
    REVISION,
    STAGES,
    Factory,
)
from react_agent.llm.teardown_probe_v1 import (
    source_hashes as baseline_hashes,
)
from react_agent.security_v1.exit_milestones_v1 import (
    MilestoneBackend,
    MilestoneConfig,
    runtime_identity,
)
from react_agent.validation.context_stress_audit_v1 import equal, inventory, read_record
from react_agent.validation.exit_milestones_v1 import audit_milestones
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.teardown_probe_audit_v1 import METHOD

PLAN = {
    "protocol": "exit_milestone_probe_v1",
    "modes": list(MODES),
    "repetitions": 3,
    "calls_per_worker": 2,
    "synthetic": True,
}
BOUNDARY = dict(
    fast="observed_stages_returned",
    bounded="observed_stages_returned",
    finalizer_block="finalizers_entered_only",
    finalizer_ignore_term="finalizers_entered_only",
    destructor_block="target_entered_only",
    thread_block="threads_entered_only",
)


def config() -> MilestoneConfig:
    return MilestoneConfig(
        MODEL,
        REVISION,
        timeout_seconds=10.0,
        graceful_shutdown_seconds=2.0,
        terminate_grace_seconds=0.2,
        kill_grace_seconds=1.0,
    )


def source_hashes() -> dict[str, str]:
    root = Path(__file__).resolve().parents[3]
    names = (
        "src/react_agent/security_v1/exit_milestones_v1.py",
        "src/react_agent/validation/exit_milestones_v1.py",
        "src/react_agent/llm/exit_milestone_probe_v1.py",
        "scripts/phase5_exit_milestones_v1.py",
        "docs/architecture/phase5_exit_milestones_v1_contract.md",
    )
    for name in names:
        no_links(root / name)
    return {
        **baseline_hashes(),
        **{name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names},
    }


def run_case(mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("fixed synthetic mode required")
    ctx = mp.get_context("spawn")
    marks: dict[str, Any] = {
        stage + suffix: ctx.RawValue(ctypes.c_double, -1.0)
        for stage in STAGES
        for suffix in ("_entered", "_completed")
    }
    marks["writer_pid"], marks["thread_ready"] = ctx.RawValue(ctypes.c_int, 0), ctx.Event()
    backend = MilestoneBackend(Factory(mode, marks), config())
    responses, failure = [], None
    try:
        for _ in range(2):
            responses.append(backend.generate([], GenerationConfig()).model_dump(mode="json"))
    except (RuntimeError, TimeoutError, ValueError, OSError) as exc:
        failure = type(exc).__name__
    finally:
        close_started = time.monotonic()
        backend.close()
        close_finished = time.monotonic()
    return dict(
        protocol="exit_milestone_case_v1",
        mode=mode,
        synthetic=True,
        generation_error=failure,
        responses=responses,
        attempts=backend.attempts,
        lifecycle=backend.lifecycle_events,
        milestones=backend.exit_milestones(),
        close_started=close_started,
        close_finished=close_finished,
        serve_returned_at=float(backend._serve_returned.value),
        stop_received_at=float(backend._stop_received.value),
    )


def audit_case(record: dict[str, Any], mode: str, runtime: dict[str, str]) -> str:
    require(mode in MODES, "fixed mode")
    equal(
        sorted(record),
        sorted(
            (
                "protocol",
                "mode",
                "synthetic",
                "generation_error",
                "responses",
                "attempts",
                "lifecycle",
                "milestones",
                "close_started",
                "close_finished",
                "serve_returned_at",
                "stop_received_at",
            )
        ),
        "case fields",
    )
    equal(record["protocol"], "exit_milestone_case_v1", "case protocol")
    equal(record["mode"], mode, "fixed mode")
    equal(record["synthetic"], True, "synthetic control")
    equal(record["generation_error"], None, "generation failure retained")
    expected = ModelResponse(text="public", model_id=MODEL, model_revision=REVISION)
    equal(record["responses"], [expected.model_dump(mode="json")] * 2, "unchanged responses")
    require(len(record["lifecycle"]) == 1 and len(record["attempts"]) == 2, "coverage")
    event = record["lifecycle"][0]
    equal(event["graceful_shutdown_seconds"], 2.0, "unchanged graceful budget")
    equal(event["method"], METHOD[mode], "same exit as frozen CPU controls")
    require(event["stop_received"] and event["graceful_requested"], "STOP observed")
    for sequence, attempt in enumerate(record["attempts"], 1):
        for name, expected_value in dict(
            sequence=sequence,
            status="OK",
            pid=event["pid"],
            cold_start=sequence == 1,
            worker_retained=True,
            reaped=False,
            execution_config_sha256=config().identity,
            request_sha256=text_hash(canonical_json([])),
            generation_sha256=text_hash(canonical_json(GenerationConfig().model_dump())),
        ).items():
            equal(attempt[name], expected_value, "attempt " + name)
        for name in ("load_seconds", "generation_seconds", "elapsed_seconds"):
            value = attempt[name]
            require(
                type(value) in (int, float) and math.isfinite(value) and value >= 0,
                "attempt timing",
            )
    started, ended = record["close_started"], record["close_finished"]
    require(
        type(started) is float
        and type(ended) is float
        and math.isfinite(started)
        and math.isfinite(ended)
        and 0 < started <= ended,
        "close timing",
    )
    boundary = audit_milestones(
        record["milestones"],
        event,
        runtime=runtime,
        config_sha256=config().identity,
        observed_until=ended,
    )
    equal(boundary, BOUNDARY[mode], "control boundary")
    events = record["milestones"]["events"]
    require(events["target_enter"]["at"] <= started, "target before close")
    stopped = record["stop_received_at"]
    require(
        type(stopped) is float and math.isfinite(stopped) and started <= stopped <= ended,
        "stop timestamp",
    )
    requested = stopped - event["stop_received_seconds"]
    require(started <= requested <= stopped, "request within close")
    require(event["elapsed_seconds"] <= ended - started + 1e-8, "lifecycle within close")
    if mode not in {"fast", "bounded"}:
        require(event["exitcode"] < 0 and ended - started >= 2.0, "forced exit after budget")
    if mode == "destructor_block":
        equal(record["serve_returned_at"], -1.0, "serve not returned")
        equal(event["serve_returned"], False, "no serve return")
    else:
        require(
            started <= record["serve_returned_at"] <= events["target_return"]["at"],
            "serve/target return ordering",
        )
        require(
            event["serve_returned_after_stop_seconds"] is not None
            and math.isclose(
                record["serve_returned_at"] - requested,
                event["serve_returned_after_stop_seconds"],
                rel_tol=0,
                abs_tol=1e-8,
            ),
            "serve timing binding",
        )
    if mode == "thread_block":
        require(events["threads_enter"]["non_daemon_threads"] >= 1, "live Python thread")
    return boundary


def run(output: Path, git_base: str) -> None:
    no_links(output)
    if output.exists() or re.fullmatch(r"[0-9a-f]{40}", git_base) is None:
        raise ValueError("fresh output and actual Git base required")
    source, runtime = source_hashes(), runtime_identity()
    output.mkdir(parents=True)
    (output / "cases").mkdir()
    write_receipt(
        output / "identity.json",
        dict(
            plan=PLAN,
            source_sha256=source,
            runtime=runtime,
            git_base_commit=git_base,
            source_identity="working_tree_hashes_with_git_base",
            config_sha256=config().identity,
            model_inference_runs=0,
            gpu_runs=0,
            test_payload_accessed=False,
            private_ground_truth_accessed=False,
        ),
    )
    for repeat in range(1, 4):
        for mode in MODES:
            record = run_case(mode)
            key = f"r{repeat}_{mode}"
            write_receipt(output / "cases" / (key + ".json"), record)
            print(key, record["lifecycle"][-1]["method"], flush=True)
    equal(source_hashes(), source, "source unchanged during controls")


def audit(root: Path) -> dict[str, Any]:
    no_links(root)
    # Reject linked descendants before reading identity or any case payload.
    hashes = inventory(root)
    identity = read_record(root / "identity.json")
    equal(identity["plan"], PLAN, "fixed schedule")
    equal(identity["source_sha256"], source_hashes(), "exact sources")
    equal(identity["runtime"], runtime_identity(), "runtime")
    equal(identity["config_sha256"], config().identity, "config")
    equal(identity["source_identity"], "working_tree_hashes_with_git_base", "source kind")
    require(re.fullmatch(r"[0-9a-f]{40}", identity["git_base_commit"]) is not None, "Git base")
    for name, expected in dict(
        model_inference_runs=0,
        gpu_runs=0,
        test_payload_accessed=False,
        private_ground_truth_accessed=False,
    ).items():
        equal(identity[name], expected, "scope " + name)
    equal(
        sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_dir()),
        ["cases"],
        "exact raw directories",
    )
    expected_paths = ["identity.json"]
    summary = []
    previous_close = 0.0
    for repeat in range(1, 4):
        for mode in MODES:
            path = f"cases/r{repeat}_{mode}.json"
            expected_paths.append(path)
            record = read_record(root / path)
            boundary = audit_case(record, mode, identity["runtime"])
            require(
                record["milestones"]["events"]["target_enter"]["at"] > previous_close,
                "serial workers do not overlap",
            )
            previous_close = record["close_finished"]
            summary.append(
                dict(
                    case=path,
                    boundary=boundary,
                    method=record["lifecycle"][0]["method"],
                    close_seconds=record["close_finished"] - record["close_started"],
                )
            )
    equal(sorted(hashes), sorted(expected_paths), "exact raw inventory")
    return dict(
        protocol="exit_milestone_audit_v1",
        valid=True,
        cases=summary,
        source_sha256=source_hashes(),
        raw_sha256=hashes,
        plan_sha256=hashlib.sha256(canonical_json(PLAN).encode()).hexdigest(),
        native_cause_identified=False,
        phase5_accepted=False,
    )
