"""Controlled CPU Replay measurements; never interpret as GPU/LLM throughput."""

from __future__ import annotations

import gc
import hashlib
import json
import platform
import resource
import shutil
import statistics
import subprocess
import sys
import tracemalloc
from pathlib import Path
from time import perf_counter_ns, process_time_ns
from typing import Any

from react_agent.agent import AgentRuntime
from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.runtime_qa import action_response, final_response
from react_agent.foundation.runtime_v1 import FoundationRuntime
from react_agent.foundation.source_catalog_v2 import environment_catalog
from react_agent.llm.replay import ReplayBackend
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.tools.factory import build_smoke_registry


def file_hashes(directory: Path) -> dict[str, str]:
    return {
        p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def measure_worker(
    root: Path, output: Path, mode: str, *, memory: bool = False, stress: bool = False
) -> dict[str, Any]:
    if mode not in {"legacy", "foundation"} or output.exists():
        raise ValueError("known mode and fresh output required")
    output.mkdir(parents=True)
    smoke = root / "data/smoke"
    rows = [json.loads(s) for s in (smoke / "tasks.jsonl").read_text().splitlines()]
    responses = json.loads((smoke / "replay_responses.json").read_text())
    if stress:
        rows = [{"task_id": "awb_stress", "instruction": "Đọc lại tài liệu giả lập tám lần."}]
        responses = {
            "awb_stress": [
                action_response(Action(name="doc_read", arguments={"doc_id": "STRESS_DOC"}))
            ]
            * 8
            + [final_response()]
        }
    measurements = []
    for row in rows:
        identity = row["task_id"]
        work = output / identity
        env = work / "copied_env"
        shutil.copytree(smoke, env)
        if stress:
            path = env / "documents/documents.json"
            documents = json.loads(path.read_text())
            documents.append(
                {"doc_id": "STRESS_DOC", "title": "Synthetic stress", "content": "x" * 65536}
            )
            path.write_text(json.dumps(documents, ensure_ascii=False) + "\n", encoding="utf-8")
        registry = build_smoke_registry(env)
        catalog = environment_catalog(env)
        task = PublicWorkbenchTask.model_construct(task_id=identity, instruction=row["instruction"])
        backend = ReplayBackend(responses[identity])
        config = RuntimeConfig(max_steps=16 if stress else 8)
        gc.collect()
        if memory:
            tracemalloc.start()
        wall, cpu = perf_counter_ns(), process_time_ns()
        if mode == "legacy":
            result = AgentRuntime(backend, registry, runtime_config=config).run(
                task, trace_path=work / "trace.jsonl"
            )
            artifact_count = 0
        else:
            run = FoundationRuntime(backend, registry, runtime_config=config).run_instrumented(
                task, output=work / "foundation", source_catalog=catalog
            )
            result = run.result
            artifact_count = len(run.artifacts)
        elapsed_cpu, elapsed_wall = process_time_ns() - cpu, perf_counter_ns() - wall
        current, peak = tracemalloc.get_traced_memory() if memory else (0, 0)
        if memory:
            tracemalloc.stop()
        if result.status != "completed":
            raise ValueError("measurement trajectory did not complete")
        sizes = {
            p.relative_to(work).as_posix(): p.stat().st_size
            for p in work.rglob("*")
            if p.is_file() and not p.is_relative_to(env)
        }
        measurements.append(
            {
                "task_id": identity,
                "wall_ns": elapsed_wall,
                "cpu_ns": elapsed_cpu,
                "traced_current_bytes": current,
                "traced_peak_bytes": peak,
                "artifact_count": artifact_count,
                "log_bytes": sum(sizes.values()),
                "log_files": sizes,
                "status": result.status,
                "tool_sequence": result.tool_sequence,
            }
        )
        if mode == "foundation":
            del run
        del result, backend, registry, catalog
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "mode": mode,
        "allocation_tracing": memory,
        "stress": stress,
        "peak_process_rss_bytes": int(rss if sys.platform == "darwin" else rss * 1024),
        "rss_scope": "process high-water incl. imports/setup; not task-incremental",
        "measurements": measurements,
    }


def percentile95(values: list[float]) -> float:
    if not values:
        raise ValueError("nonempty measurements required")
    import math

    return sorted(values)[max(0, math.ceil(len(values) * 0.95) - 1)]


def summarize(workers: list[dict[str, Any]], expected_ids: list[str]) -> dict[str, Any]:
    indexed = {(w["stage"], w["repeat"], w["mode"]): w for w in workers}
    expected = {
        (stage, repeat, mode)
        for stage, count in (("warmup", 1), ("time", 7), ("memory", 3))
        for repeat in range(count)
        for mode in ("legacy", "foundation")
    }
    if len(indexed) != len(workers) or set(indexed) != expected:
        raise ValueError("duplicate or incomplete measurement workers")
    for worker in workers:
        if [r["task_id"] for r in worker["measurements"]] != expected_ids:
            raise ValueError("measurement task coverage mismatch")
        if worker["allocation_tracing"] != (worker["stage"] == "memory"):
            raise ValueError("timing contaminated by allocation tracer")
    deltas, ratios, repeats = [], [], []
    for repeat in range(7):
        old, new = [
            indexed["time", repeat, mode]["measurements"] for mode in ("legacy", "foundation")
        ]
        difference = []
        for a, b in zip(old, new, strict=True):
            if a["status"] != b["status"] or a["tool_sequence"] != b["tool_sequence"]:
                raise ValueError("measurement A0 execution mismatch")
            if a["wall_ns"] <= 0 or b["wall_ns"] <= 0:
                raise ValueError("invalid monotonic clock interval")
            difference.append((b["wall_ns"] - a["wall_ns"]) / 1e6)
            ratios.append(b["wall_ns"] / a["wall_ns"])
        deltas.extend(difference)
        repeats.append(
            {
                "repeat": repeat,
                "median_added_ms": statistics.median(difference),
                "batch_wall_ratio": sum(r["wall_ns"] for r in new) / sum(r["wall_ns"] for r in old),
            }
        )
    peaks = [
        r["traced_peak_bytes"]
        for w in workers
        if w["stage"] == "memory" and w["mode"] == "foundation"
        for r in w["measurements"]
    ]
    by_mode = {}
    for mode in ("legacy", "foundation"):
        timed = [
            r
            for w in workers
            if w["stage"] == "time" and w["mode"] == mode
            for r in w["measurements"]
        ]
        mem = [
            r
            for w in workers
            if w["stage"] == "memory" and w["mode"] == mode
            for r in w["measurements"]
        ]
        by_mode[mode] = {
            "median_wall_ms": statistics.median(r["wall_ns"] for r in timed) / 1e6,
            "p95_wall_ms": percentile95([r["wall_ns"] / 1e6 for r in timed]),
            "median_cpu_ms": statistics.median(r["cpu_ns"] for r in timed) / 1e6,
            "max_traced_peak_bytes": max(r["traced_peak_bytes"] for r in mem),
            "median_log_bytes": statistics.median(r["log_bytes"] for r in timed),
            "max_process_rss_bytes": max(
                w["peak_process_rss_bytes"] for w in workers if w["mode"] == mode
            ),
        }
    guards = {
        "p95_added_under_100ms": percentile95(deltas) < 100,
        "max_traced_peak_under_32MiB": max(peaks) < 32 * 1024 * 1024,
    }
    return {
        "valid": all(guards.values()),
        "guards": guards,
        "fresh_replay_runs": len(workers) * len(expected_ids),
        "timing_pairs": len(deltas),
        "median_added_ms": statistics.median(deltas),
        "p95_added_ms": percentile95(deltas),
        "median_task_wall_ratio": statistics.median(ratios),
        "repeats": repeats,
        "by_mode": by_mode,
    }


def run_study(root: Path, output: Path) -> dict[str, Any]:
    if output.exists() or not output.resolve().is_relative_to(root.resolve() / "results"):
        raise ValueError("fresh results-only study output required")
    output.mkdir(parents=True)
    before = file_hashes(root / "data/smoke")
    workers = []
    script = root / "scripts/verify_phase4_closure.py"
    for stage, count in (("warmup", 1), ("time", 7), ("memory", 3)):
        for repeat in range(count):
            modes = ("legacy", "foundation") if repeat % 2 == 0 else ("foundation", "legacy")
            for mode in modes:
                destination = output / f"{stage}_{repeat}_{mode}"
                command = [
                    sys.executable,
                    str(script),
                    "--worker",
                    mode,
                    "--output",
                    str(destination),
                ]
                if stage == "memory":
                    command.append("--memory")
                subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)  # noqa: S603
                worker = json.loads((destination / "worker.json").read_text())
                worker.update(stage=stage, repeat=repeat)
                workers.append(worker)
    ids = [
        json.loads(s)["task_id"] for s in (root / "data/smoke/tasks.jsonl").read_text().splitlines()
    ]
    summary = summarize(workers, ids)
    stress = []
    for mode in ("legacy", "foundation"):
        destination = output / ("stress_" + mode)
        subprocess.run(  # noqa: S603 - fixed local worker, no shell or user code
            [
                sys.executable,
                str(script),
                "--worker",
                mode,
                "--memory",
                "--stress",
                "--output",
                str(destination),
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )  # noqa: S603
        stress.append(json.loads((destination / "worker.json").read_text()))
    if file_hashes(root / "data/smoke") != before:
        raise ValueError("smoke data changed during measurement")
    return {
        **summary,
        "workers": workers,
        "stress_workers": stress,
        "stress_replay_runs": 2,
        "smoke_input_sha256": before,
        "machine": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version,
            "clock": "perf_counter_ns/process_time_ns",
            "execution": "sequential fresh subprocesses",
        },
        "scope": "bounded CPU Replay diagnostics; no LLM/GPU extrapolation",
    }
