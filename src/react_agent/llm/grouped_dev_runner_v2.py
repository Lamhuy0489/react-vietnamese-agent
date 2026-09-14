"""Fresh-task grouped native runner, with durable checkpoints and recovery stops."""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.base import GenerationConfig, LLMBackend
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.grouped_dev_identity_v1 import pair_config
from react_agent.llm.grouped_dev_identity_v2 import identity
from react_agent.llm.grouped_dev_runner_v1 import ScriptedFactory
from react_agent.llm.guard_diagnostic_backend_v1 import DiagnosticFactory
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_probe_v1 import (
    PairCUDAObserver,
    PairObserver,
    SyntheticPairObserver,
    validate_memory,
)
from react_agent.llm.model_pair_v2 import ShutdownPair
from react_agent.llm.native_agent_only_v1 import native_agent
from react_agent.llm.native_guard_diagnostics_v1 import native_pair
from react_agent.llm.native_shutdown_v2 import agent_config, native_config
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.sql_pair_runtime_v1 import run_pair_task
from react_agent.validation.grouped_dev_checkpoint_v2 import audit_checkpoint, audit_prefix
from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog


def run(
    output: Path,
    release: Path,
    environment: Path,
    *,
    commit: str,
    shard: int,
    backend: str = "stub",
    resume: bool = False,
    max_new_tasks: int | None = None,
    agent: Path | None = None,
    model_inventory: Path | None = None,
    guard: Path | None = None,
    snapshot: GuardSnapshot | None = None,
    observer_factory: Callable[[], PairObserver] | None = None,
) -> dict[str, Any]:
    if type(shard) is not int or not 0 <= shard < 8 or type(resume) is not bool:
        raise ValueError("known shard and boolean resume required")
    if max_new_tasks is not None and (type(max_new_tasks) is not int or max_new_tasks < 0):
        raise ValueError("nonnegative controlled task budget required")
    if (backend == "hf" and (agent is None or guard is None)) or (
        backend != "hf" and (agent is not None or guard is not None)
    ):
        raise ValueError("native model paths must agree with backend")
    frozen = Path(__file__).resolve().parents[3] / "data"
    no_links(output)
    for source in (release, environment, frozen, agent, guard, model_inventory):
        if source is None:
            continue
        no_links(source)
        if output.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(
            output.resolve()
        ):
            raise ValueError("output overlaps input or frozen data")
    manifest, rows = identity(release, environment, commit, backend, model_inventory, snapshot)
    if output.exists():
        if not resume:
            raise ValueError("fresh output required unless resuming exact identity")
        saved = audit_prefix(output, manifest, shard)
    else:
        output.mkdir(parents=True, exist_ok=False)
        write_receipt(output / "identity.json", {"run": manifest, "shard": shard})
        (output / "tasks").mkdir()
        saved = []
    factory = observer_factory or (PairCUDAObserver if backend == "hf" else SyntheticPairObserver)
    tasks = [t for t in manifest["tasks"] if t["shard"] == shard]
    by_variant = {row.variant_id: row for row in rows}
    remaining = tasks[len(saved) :]
    if max_new_tasks is not None:
        remaining = remaining[:max_new_tasks]
    config = native_config() if backend == "hf" else pair_config()
    for task in remaining:
        row = by_variant[task["variant_id"]]
        root = output / "tasks" / task["key"]
        root.mkdir(exist_ok=False)
        started = time.perf_counter()
        observer = factory()
        if (
            type(observer.interval) not in (int, float)
            or not math.isfinite(observer.interval)
            or (observer.interval != manifest["recovery"]["sample_interval_seconds"])
        ):
            raise ValueError("observer interval differs from frozen recovery policy")
        baseline = observer.sample("baseline")
        validate_memory(baseline)
        write_receipt(root / "baseline.json", {"memory": baseline})
        registry = row.registry(environment, root / "environment")
        overlay_before = inventory(root / "environment")
        pair = None
        arguments: dict[str, Any]
        if backend == "hf":
            if agent is None or model_inventory is None or guard is None or snapshot is None:
                raise ValueError("native inputs missing")
            if task["level"] in {"A0", "A1"}:
                arguments = dict(
                    agent_factory=native_agent(
                        agent,
                        model_inventory,
                        root / "native/agent_hf_metrics.jsonl",
                        root / "attention/agent",
                        root / "policy/agent",
                    ),
                    agent_execution=agent_config(config),
                )
            else:
                pair = native_pair(
                    agent,
                    model_inventory,
                    guard,
                    snapshot,
                    root / "native",
                    root / "attention",
                    root / "policy",
                )
                arguments = {"pair": pair}
            (root / "native").mkdir()
        else:
            scripted = ScriptedFactory(
                "agent", canonical_json({"action": row.overlay.trigger.model_dump()})
            )
            if task["level"] in {"A0", "A1"}:
                arguments = dict(agent_factory=scripted, agent_execution=agent_config(config))
            else:
                pair = ShutdownPair(
                    scripted,
                    cast(
                        Callable[[], LLMBackend],
                        DiagnosticFactory(
                            ScriptedFactory("guard"), root / "guard_diagnostics.jsonl"
                        ),
                    ),
                    config,
                )
                arguments = {"pair": pair}
        try:
            result = run_pair_task(
                PublicWorkbenchTask.model_validate(row.task.model_dump()),
                output=root / "execution",
                registry_factory=lambda registry=registry: registry,
                security=configuration(task["level"]),
                runtime_config=RuntimeConfig(),
                generation=GenerationConfig(),
                source_catalog=fixture_catalog(row),
                **arguments,
            )
        finally:
            try:
                if pair is not None:
                    pair.close()
            finally:
                samples = []
                for _ in range(manifest["recovery"]["samples"]):
                    if observer.interval:
                        time.sleep(observer.interval)
                    sample = observer.sample("recovery")
                    validate_memory(sample)
                    samples.append(sample)
                write_receipt(root / "recovery.json", {"memory": samples})
        if inventory(root / "environment") != overlay_before:
            raise ValueError("task environment changed")
        recovered = all(
            sample[i]["total_bytes"] == baseline[i]["total_bytes"]
            and abs(sample[i]["free_bytes"] - baseline[i]["free_bytes"])
            <= manifest["recovery"]["tolerance_bytes"]
            for sample in samples[-manifest["recovery"]["stable_tail"] :]
            for i in (0, 1)
        )
        write_receipt(
            root / "task_timing.json",
            dict(
                task_wall_seconds_including_setup_cleanup_recovery=time.perf_counter() - started,
                backend=backend,
                quality_scoring=False,
            ),
        )
        write_receipt(
            root / "checkpoint.json",
            dict(
                protocol="grouped_dev_checkpoint_v2",
                identity_sha256=text_hash(canonical_json(manifest)),
                key=task["key"],
                terminal=result.result.status,
                recovered=recovered,
                raw_sha256=inventory(root),
            ),
        )
        saved.append(audit_checkpoint(root, manifest, task))
        print(f"{task['key']}: {result.result.status}; recovered={recovered}", flush=True)
        if not recovered:
            raise RuntimeError("memory not recovered; stop before next task")
    current, _ = identity(release, environment, commit, backend, model_inventory, snapshot)
    if current != manifest:
        raise ValueError("grouped input changed during run")
    return dict(
        protocol=manifest["protocol"],
        backend=backend,
        shard=shard,
        completed=len(saved),
        expected=14,
        remaining=14 - len(saved),
        terminal_statuses=[r["terminal"] for r in saved],
        identity_sha256=text_hash(canonical_json(manifest)),
        phase5_accepted=False,
        quality_scoring=False,
        native_artifacts_authenticated=False,
    )
