"""Synthetic post-serve controls around the unchanged observed-shutdown worker."""

from __future__ import annotations

import ctypes
import hashlib
import inspect
import multiprocessing as mp
import os
import platform
import re
import signal
import threading
import time
from dataclasses import dataclass
from multiprocessing import util
from multiprocessing.process import BaseProcess
from multiprocessing.util import Finalize
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import canonical_json
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.security_v1.worker_shutdown_v2 import ShutdownBackend, ShutdownConfig

MODES = (
    "fast",
    "bounded",
    "finalizer_block",
    "finalizer_ignore_term",
    "destructor_block",
    "thread_block",
)
STAGES = ("destructor", "finalizer", "thread")
PLAN: dict[str, Any] = dict(
    protocol="teardown_probe_v1",
    modes=list(MODES),
    repetitions=3,
    calls_per_worker=2,
    graceful_seconds=2.0,
    terminate_seconds=0.2,
    kill_seconds=1.0,
    bounded_delay_seconds=0.25,
    blocked_delay_seconds=5.0,
)
MODEL, REVISION = "synthetic-teardown", "v1"


def worker_config() -> ShutdownConfig:
    return ShutdownConfig(
        MODEL,
        REVISION,
        timeout_seconds=10.0,
        graceful_shutdown_seconds=2.0,
        terminate_grace_seconds=0.2,
        kill_grace_seconds=1.0,
    )


def runtime_identity() -> dict[str, str]:
    """Pin the actual CPU harness interpreter mechanics, not a guessed Kaggle version."""
    internals = {
        label: hashlib.sha256(inspect.getsource(getattr(owner, name)).encode()).hexdigest()
        for label, owner, name in (
            ("bootstrap_sha256", BaseProcess, "_bootstrap"),
            ("exit_function_sha256", util, "_exit_function"),
        )
    }
    return dict(
        version=platform.python_version(),
        implementation=platform.python_implementation(),
        system=platform.system(),
        machine=platform.machine(),
        **internals,
    )


def stage(marks: dict[str, Any], name: str, delay: float) -> None:
    marks[name + "_entered"].value = time.monotonic()
    if name == "thread":
        marks["thread_ready"].set()
    time.sleep(delay)
    marks[name + "_completed"].value = time.monotonic()


class SyntheticBackend:
    model_id = MODEL
    model_revision = REVISION

    def __init__(self, mode: str, marks: dict[str, Any]) -> None:
        self.mode, self.marks = mode, marks
        marks["writer_pid"].value = os.getpid()
        if mode == "finalizer_ignore_term":
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        delay = 0.25 if mode == "bounded" else 5.0 if mode.startswith("finalizer_") else 0.0
        Finalize(None, stage, args=(marks, "finalizer", delay), exitpriority=10)
        if mode == "thread_block":
            threading.Thread(target=stage, args=(marks, "thread", 5.0), daemon=False).start()
            if not marks["thread_ready"].wait(5.0):
                raise RuntimeError("synthetic thread did not start")

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        return ModelResponse(text="public", model_id=MODEL, model_revision=REVISION)

    def __del__(self) -> None:
        stage(self.marks, "destructor", 5.0 if self.mode == "destructor_block" else 0.0)


@dataclass(frozen=True)
class Factory:
    mode: str
    marks: dict[str, Any]

    def __call__(self) -> SyntheticBackend:
        return SyntheticBackend(self.mode, self.marks)


def source_hashes() -> dict[str, str]:
    root = Path(__file__).resolve().parents[3]
    names = (
        "src/react_agent/llm/teardown_probe_v1.py",
        "src/react_agent/validation/teardown_probe_audit_v1.py",
        "src/react_agent/security_v1/worker_shutdown_v2.py",
        "src/react_agent/security_v1/warm_guard.py",
        "src/react_agent/security_v1/process_guard.py",
        "src/react_agent/llm/base.py",
        "src/react_agent/validation/worker_shutdown_audit_v2.py",
        "scripts/run_phase5_teardown_probe_v1.py",
        "scripts/audit_phase5_teardown_probe_v1.py",
        "docs/architecture/phase5_teardown_probe_v1_contract.md",
    )
    for name in names:
        no_links(root / name)
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}


def run_case(mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("fixed synthetic teardown mode required")
    ctx = mp.get_context("spawn")
    marks: dict[str, Any] = {
        stage + suffix: ctx.RawValue(ctypes.c_double, -1.0)
        for stage in STAGES
        for suffix in ("_entered", "_completed")
    }
    marks["writer_pid"] = ctx.RawValue(ctypes.c_int, 0)
    marks["thread_ready"] = ctx.Event()
    backend = ShutdownBackend(Factory(mode, marks), worker_config())
    responses = []
    failure: str | None = None
    try:
        for _ in range(PLAN["calls_per_worker"]):
            result = backend.generate([], GenerationConfig())
            responses.append(result.model_dump(mode="json"))
    except (RuntimeError, TimeoutError, ValueError, OSError) as exc:
        # Retain sanitized infrastructure evidence; the auditor rejects incomplete calls.
        failure = type(exc).__name__
    finally:
        close_started = time.monotonic()
        backend.close()
        close_finished = time.monotonic()
    if backend._process is not None:
        raise RuntimeError("worker not reaped; do not start another control")
    observed = {
        name: float(value.value) if value.value >= 0 else None
        for name, value in marks.items()
        if name not in {"writer_pid", "thread_ready"}
    }
    return dict(
        protocol="teardown_case_v1",
        mode=mode,
        synthetic=True,
        actual_model_loads=0,
        generation_error=failure,
        writer_pid=int(marks["writer_pid"].value),
        attempts=backend.attempts,
        lifecycle=backend.lifecycle_events,
        responses=responses,
        stages=observed,
        close_started=close_started,
        close_finished=close_finished,
        stop_received_at=float(backend._stop_received.value),
        serve_returned_at=float(backend._serve_returned.value),
        execution_config_sha256=worker_config().identity,
    )


def run(output: Path, git_base: str) -> None:
    no_links(output)
    if output.exists() or re.fullmatch(r"[0-9a-f]{40}", git_base) is None:
        raise ValueError("fresh output and actual Git base required")
    source = source_hashes()
    output.mkdir(parents=True)
    (output / "cases").mkdir()
    write_receipt(
        output / "identity.json",
        dict(
            protocol="teardown_probe_v1",
            plan=PLAN,
            plan_sha256=hashlib.sha256(canonical_json(PLAN).encode()).hexdigest(),
            git_base_commit=git_base,
            source_identity="working_tree_hashes_with_git_base",
            source_sha256=source,
            python_runtime=runtime_identity(),
            python_version=platform.python_version(),
            python_implementation=platform.python_implementation(),
            start_method="spawn",
            synthetic=True,
            actual_model_loads=0,
            gpu_runs=0,
            test_payload_accessed=False,
        ),
    )
    for repeat in range(1, 4):
        for mode in MODES:
            value = run_case(mode)
            key = f"r{repeat}_{mode}"
            write_receipt(output / "cases" / (key + ".json"), value)
            print(key, value["lifecycle"][-1]["method"], flush=True)
    if source_hashes() != source:
        raise ValueError("source changed during controls")
