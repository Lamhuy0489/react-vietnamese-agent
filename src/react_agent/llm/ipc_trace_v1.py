"""Opt-in diagnostic of tracker calls, never a resource-cleanup implementation."""

from __future__ import annotations

import hashlib
import inspect
import json
import multiprocessing.resource_tracker as tracker
import os
import platform
import sys
import threading
from collections.abc import Callable, Sized
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.base import LLMBackend


class TrackerTrace:
    """Observe successful tracker entry-point calls until this process exits.

    One file/owner PID; stack metadata only, no source lines, locals or resource
    names. Hooks forward once to the original methods. No manual unregister,
    unlink, altered finalizer, suppression, or change to the tracker itself.
    Install before creating resources. Imports which saved aliases earlier and
    C-level registrations outside these entry points are not covered.
    """

    def __init__(self, path: Path, role: str) -> None:
        if role not in ("owner", "agent", "guard", "control"):
            raise ValueError("fixed diagnostic role required")
        no_links(path)
        if not path.parent.is_dir():
            raise ValueError("existing trace directory required")
        if getattr(tracker.register, "__self__", None) is not tracker._resource_tracker:
            raise RuntimeError("tracker already instrumented or unsupported")
        self.path, self.role, self.pid = path, role, os.getpid()
        self._lock = threading.RLock()
        self._sequence = 0
        # Bind helpers now: multiprocessing finalizers may execute late at exit.
        self._open = path.open
        self._dumps = json.dumps
        self._fsync = os.fsync
        self._register = tracker.register
        self._unregister = tracker.unregister
        with self._open("x", encoding="utf-8") as stream:
            stream.write("")
        self.record(
            "INSTALLED",
            python_version=platform.python_version(),
            implementation=platform.python_implementation(),
            tracker_source_sha256=hashlib.sha256(Path(tracker.__file__).read_bytes()).hexdigest(),
        )
        tracker.register = self.register
        tracker.unregister = self.unregister

    def record(self, action: str, **values: Any) -> None:
        if os.getpid() != self.pid:
            raise RuntimeError("trace belongs to another process; use spawn")
        with self._lock:
            row = {
                "protocol": "ipc_tracker_trace_v1",
                "sequence": self._sequence + 1,
                "pid": self.pid,
                "role": self.role,
                "action": action,
                **values,
            }
            with self._open("a", encoding="utf-8") as stream:
                stream.write(self._dumps(row, sort_keys=True) + "\n")
                stream.flush()
                self._fsync(stream.fileno())
            self._sequence += 1

    def _forward(
        self, action: str, original: Callable[[Sized, str], None], name: Sized, rtype: str
    ) -> None:
        with self._lock:
            if not isinstance(name, str):
                raise ValueError("text tracker identity required")
            frames: list[dict[str, Any]] = []
            frame = inspect.currentframe()
            try:
                frame = frame.f_back.f_back if frame and frame.f_back else None
                while frame is not None and len(frames) < 24:
                    frames.append(
                        {
                            "module": str(frame.f_globals.get("__name__", "unknown")),
                            "file": Path(frame.f_code.co_filename).name,
                            "function": frame.f_code.co_name,
                            "line": frame.f_lineno,
                        }
                    )
                    frame = frame.f_back
            finally:
                del frame
            original(name, rtype)
            self.record(
                action,
                resource_type=rtype,
                name_sha256=hashlib.sha256(name.encode()).hexdigest(),
                stack=frames,
            )

    def register(self, name: Sized, rtype: str) -> None:
        self._forward("REGISTER", self._register, name, rtype)

    def unregister(self, name: Sized, rtype: str) -> None:
        self._forward("UNREGISTER", self._unregister, name, rtype)


@dataclass(frozen=True)
class TracedFactory:
    factory: Callable[[], LLMBackend]
    path: Path
    role: str

    def __call__(self) -> LLMBackend:
        trace = TrackerTrace(self.path, self.role)
        trace.record("FACTORY_ENTER")
        try:
            backend = self.factory()
        except BaseException as exc:
            trace.record("FACTORY_ERROR", error_class=type(exc).__name__)
            raise
        modules = {}
        for name in (
            "torch",
            "transformers",
            "transformers.modeling_utils",
            "tqdm",
            "tqdm.std",
            "multiprocessing.synchronize",
        ):
            module = sys.modules.get(name)
            source_path = getattr(module, "__file__", None)
            if module is not None and isinstance(source_path, str):
                modules[name] = {
                    "version": getattr(module, "__version__", None),
                    "source_sha256": hashlib.sha256(Path(source_path).read_bytes()).hexdigest(),
                }
        trace.record("FACTORY_READY", modules=modules)
        return backend


def read_trace(path: Path) -> dict[str, Any]:
    """Strict per-process ledger, not a global IPC or OS unlink certificate."""
    no_links(path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if not rows or rows[0].get("action") != "INSTALLED":
        raise ValueError("missing trace installation")
    active: dict[tuple[str, str], dict[str, Any]] = {}
    registers = unregisters = 0
    for i, row in enumerate(rows, 1):
        if (
            row.get("protocol") != "ipc_tracker_trace_v1"
            or type(row.get("sequence")) is not int
            or row["sequence"] != i
            or type(row.get("pid")) is not int
            or row["pid"] <= 0
            or row["pid"] != rows[0]["pid"]
            or row.get("role") not in ("owner", "agent", "guard", "control")
            or row["role"] != rows[0]["role"]
        ):
            raise ValueError("trace identity or sequence mismatch")
        action = row.get("action")
        if action not in (
            "INSTALLED",
            "REGISTER",
            "UNREGISTER",
            "FACTORY_ENTER",
            "FACTORY_READY",
            "FACTORY_ERROR",
            "PROBE_DONE",
        ) or (action == "INSTALLED" and i != 1):
            raise ValueError("unexpected trace event")
        if action not in ("REGISTER", "UNREGISTER"):
            continue
        digest = row.get("name_sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
            or row.get("resource_type") not in ("semaphore", "shared_memory", "dummy", "noop")
            or not isinstance(row.get("stack"), list)
            or not 1 <= len(row["stack"]) <= 24
        ):
            raise ValueError("invalid resource identity or call stack")
        for frame in row["stack"]:
            if (
                not isinstance(frame, dict)
                or set(frame) != {"module", "file", "function", "line"}
                or any(not isinstance(frame[k], str) for k in ("module", "file", "function"))
                or type(frame["line"]) is not int
                or frame["line"] <= 0
            ):
                raise ValueError("invalid stack frame")
        key = (row["resource_type"], digest)
        if action == "REGISTER":
            registers += 1
            if key in active:
                raise ValueError("duplicate live registration; attribution ambiguous")
            active[key] = row
        else:
            unregisters += 1
            if key not in active:
                raise ValueError("unregister not paired in this process trace")
            del active[key]
    return {
        "pid": rows[0]["pid"],
        "role": rows[0]["role"],
        "events": len(rows),
        "register_calls": registers,
        "unregister_calls": unregisters,
        "unmatched_registrations": list(active.values()),
        "ipc_cleanup_verified": False,
        "scope": "Only observed Python entry-point calls; no OS/tracker-exit observation",
    }
