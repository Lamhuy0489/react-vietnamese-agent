#!/usr/bin/env python3
"""Native tqdm/real spawn CPU controls, never torch, HF or model inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.ipc_trace_v1 import TrackerTrace, read_trace
from react_agent.llm.worker_progress_v1 import configure_worker_progress

CASES = ("default_term", "disabled_term", "thread_term", "thread_kill")


def child(root: Path, case: str, ready: Any) -> None:
    # The disabled control sets the variable before importing tqdm at all.
    if case == "disabled_term":
        os.environ["TQDM_DISABLE"] = "1"
    trace = TrackerTrace(root / f"{case}.jsonl", "control")
    trace.record("FACTORY_ENTER")
    policy = configure_worker_progress() if case.startswith("thread_") else None
    import hashlib
    import importlib

    from react_agent.llm.worker_progress_v1 import STD_SHA256, VERSION

    tqdm = importlib.import_module("tqdm")
    std = importlib.import_module("tqdm.std")
    source_path = getattr(std, "__file__", None)
    if (
        tqdm.__version__ != VERSION
        or not isinstance(source_path, str)
        or hashlib.sha256(Path(source_path).read_bytes()).hexdigest() != STD_SHA256
    ):
        raise ValueError("exact native tqdm required")
    # Disabled display still exercises __new__/get_lock. Iterate, do not just
    # import the package; otherwise this control misses the actual creation site.
    if list(tqdm.tqdm(range(3), disable=True)) != [0, 1, 2]:
        raise RuntimeError("iteration changed")
    trace.record("FACTORY_READY", policy=policy)
    ready.send(os.getpid())
    ready.close()
    if case == "thread_kill":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    while True:
        time.sleep(0.05)


def run_suite(root: Path) -> None:
    ctx = mp.get_context("spawn")
    rows = []
    for case in CASES:
        receiver, sender = ctx.Pipe(duplex=False)
        process = ctx.Process(target=child, args=(root, case, sender), daemon=True)
        try:
            process.start()
            sender.close()
            if not receiver.poll(15) or receiver.recv() != process.pid:
                raise RuntimeError("positive-control readiness failed")
            if case == "thread_kill":
                process.kill()
            else:
                process.terminate()
            process.join(3)
            if process.is_alive():
                raise RuntimeError("control worker not reaped")
            rows.append({"case": case, "pid": process.pid, "exitcode": process.exitcode})
        finally:
            receiver.close()
            sender.close()
            if process.pid is not None:
                if process.is_alive():
                    process.kill()
                    process.join(3)
                if process.is_alive():
                    raise RuntimeError("control cleanup incomplete")
            process.close()
    write_receipt(root / "workers.json", {"workers": rows})


def audit(root: Path) -> dict[str, Any]:
    rows = json.loads((root / "workers.json").read_text())["workers"]
    if [r["case"] for r in rows] != list(CASES) or len({r["pid"] for r in rows}) != 4:
        raise ValueError("control identity coverage")
    observations = {}
    for row in rows:
        case = row["case"]
        expected = 0 if case.startswith("thread_") else 1
        trace = read_trace(root / f"{case}.jsonl")
        if (
            trace["pid"] != row["pid"]
            or row["exitcode"] != (-9 if case == "thread_kill" else -15)
            or trace["register_calls"] != expected
            or trace["unregister_calls"] != 0
            or len(trace["unmatched_registrations"]) != expected
        ):
            raise ValueError("native progress control failed")
        observations[case] = trace
    return {
        "protocol": "worker_thread_progress_cpu_v1",
        "valid": True,
        "observations": observations,
        "workers": rows,
        "model_loads": 0,
        "gpu_runs": 0,
        "ipc_cleanup_verified": False,
        "phase5_accepted": False,
        "scope": "Native pinned tqdm with synthetic iteration, not HF loading or GPU cleanup",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--isolated-owner", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    no_links(args.output)
    if args.isolated_owner:
        run_suite(args.output)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    completed = subprocess.run(  # noqa: S603 - same fixed script and synthetic internal mode
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--output",
            str(args.output),
            "--isolated-owner",
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    (args.output / "owner_stdout.txt").write_text(completed.stdout)
    (args.output / "owner_stderr.txt").write_text(completed.stderr)
    if completed.returncode:
        raise RuntimeError("isolated native control failed; see retained logs")
    result = audit(args.output)
    project = Path(__file__).resolve().parents[1]
    result["source_commit"] = subprocess.check_output(  # noqa: S603,S607 - fixed read-only Git query
        ["git", "rev-parse", "HEAD"], cwd=project, text=True  # noqa: S607
    ).strip()
    result["python_version"] = platform.python_version()
    result["source_sha256"] = {
        name: hashlib.sha256((project / name).read_bytes()).hexdigest()
        for name in (
            "scripts/probe_phase5_worker_progress.py",
            "src/react_agent/llm/worker_progress_v1.py",
            "src/react_agent/llm/ipc_trace_v1.py",
        )
    }
    result["raw_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in args.output.iterdir()
        if p.is_file()
    }
    # Original tracker warnings must stay visible; the two positive controls
    # intentionally rely on the isolated owner's tracker for eventual cleanup.
    if "There appear to be 2 leaked semaphore objects" not in completed.stderr:
        raise ValueError("expected positive-control warning missing")
    write_receipt(args.output / "receipt.json", result)
    print("PASS: native tqdm controls; disable still registers, thread lock does not")


if __name__ == "__main__":
    main()
