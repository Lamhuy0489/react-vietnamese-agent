"""Retain task-bound exit milestones after the unchanged constrained runtime cleanup."""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.exit_pair_v1 import ExitPair
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1 import constrained_runtime_v1 as baseline
from react_agent.security_v1.constrained_host_v1 import native_root as old_native_root
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.runtime import SecurityRun


def native_root(pair: ExitPair) -> Path:
    return cast(Path, bind(old_native_root, DiagnosticPair=ExitPair)(pair))


def _run(task: RuntimeTask, *, pair: ExitPair, synthetic: bool, **kwargs: Any) -> SecurityRun:
    if type(pair) is not ExitPair:
        raise TypeError("explicit exit pair required")
    output = Path(kwargs["output"])
    no_links(output)
    if output.exists():
        raise ValueError("fresh runtime output required")
    body = (
        bind(baseline.run_synthetic_pair_task, DiagnosticPair=ExitPair)
        if synthetic
        else bind(baseline.run_pair_task, native_root=native_root)
    )
    try:
        return cast(SecurityRun, body(task, pair=pair, **kwargs))
    finally:
        receipt = output / "pair_runtime.json"
        # Pre-admission failures create no synthetic success receipt.
        if receipt.is_file():
            snapshot = pair.snapshot()
            write_receipt(
                output / "exit_milestones.json",
                dict(
                    protocol="exit_pair_task_v1",
                    task_id=task.task_id,
                    task_sha256=text_hash(task.instruction),
                    owner_pid=os.getpid(),
                    pair_config_sha256=pair.config.sha256,
                    pair_runtime_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
                    pair_snapshot_sha256=text_hash(canonical_json(snapshot)),
                    observed_until=time.monotonic(),
                    workers=pair.exit_snapshot(),
                    phase5_accepted=False,
                ),
            )


def run_pair_task(task: RuntimeTask, *, pair: ExitPair, **kwargs: Any) -> SecurityRun:
    return _run(task, pair=pair, synthetic=False, **kwargs)


def run_synthetic_pair_task(task: RuntimeTask, *, pair: ExitPair, **kwargs: Any) -> SecurityRun:
    return _run(task, pair=pair, synthetic=True, **kwargs)
