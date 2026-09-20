"""Opt-in child-local CPython exit observation; frozen worker methods are inherited."""

from __future__ import annotations

import ast
import ctypes
import hashlib
import inspect
import os
import platform
import textwrap
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from multiprocessing import util
from multiprocessing.process import BaseProcess
from typing import Any, cast

from react_agent.llm.base import LLMBackend
from react_agent.security_v1.worker_shutdown_v2 import (
    ShutdownBackend,
    ShutdownConfig,
    _observed_serve,
)

PHASES = ("target", "finalizers", "threads")
EVENTS = tuple(f"{phase}_{event}" for phase in PHASES for event in ("enter", "return", "error"))


def runtime_identity() -> dict[str, str]:
    sources = {
        label: inspect.getsource(getattr(owner, name))
        for label, owner, name in (
            ("bootstrap", BaseProcess, "_bootstrap"),
            ("finalizers", util, "_exit_function"),
            ("threads", threading, "_shutdown"),
        )
    }
    calls = sorted(
        (node.lineno, ast.unparse(node.func))
        for node in ast.walk(ast.parse(textwrap.dedent(sources["bootstrap"])))
        if isinstance(node, ast.Call)
        and ast.unparse(node.func) in {"self.run", "util._exit_function", "threading._shutdown"}
    )
    if platform.python_implementation() != "CPython" or [name for _, name in calls] != [
        "self.run",
        "util._exit_function",
        "threading._shutdown",
    ]:
        raise RuntimeError("unsupported interpreter exit structure")
    return {
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
        **{
            name + "_sha256": hashlib.sha256(src.encode()).hexdigest()
            for name, src in sources.items()
        },
    }


@dataclass(frozen=True)
class MilestoneConfig(ShutdownConfig):
    lifecycle: str = field(default="task_local_exit_milestones_v1", init=False)


def new_slots(ctx: Any) -> dict[str, Any]:
    return {
        "time": ctx.RawArray(ctypes.c_double, [-1.0] * len(EVENTS)),
        "pid": ctx.RawArray(ctypes.c_longlong, [0] * len(EVENTS)),
        "threads": ctx.RawArray(ctypes.c_longlong, [-1] * len(EVENTS)),
    }


def mark(slots: dict[str, Any], event: str) -> None:
    index = EVENTS.index(event)
    if slots["time"][index] >= 0:
        raise RuntimeError("duplicate milestone")
    slots["pid"][index] = os.getpid()
    main = threading.main_thread()
    slots["threads"][index] = sum(
        thread is not main and not thread.daemon and thread.is_alive()
        for thread in threading.enumerate()
    )
    slots["time"][index] = time.monotonic()  # Commit this fixed slot last.


def observed_call(
    function: Callable[..., Any],
    phase: str,
    slots: dict[str, Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    mark(slots, phase + "_enter")
    try:
        result = function(*args, **kwargs)
    except BaseException:
        mark(slots, phase + "_error")
        raise  # Preserve exception type/value; never serialize it.
    mark(slots, phase + "_return")
    return result


def install_hook(owner: Any, name: str, phase: str, slots: dict[str, Any]) -> None:
    original = getattr(owner, name)

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return observed_call(original, phase, slots, args, kwargs)
        finally:
            setattr(owner, name, original)

    setattr(owner, name, wrapped)


def observed_target(
    args: tuple[Any, ...], slots: dict[str, Any], expected_runtime: dict[str, str]
) -> None:
    if runtime_identity() != expected_runtime:
        raise RuntimeError("child interpreter identity changed")
    install_hook(util, "_exit_function", "finalizers", slots)
    install_hook(threading, "_shutdown", "threads", slots)
    observed_call(_observed_serve, "target", slots, args, {})


@dataclass
class _Context:
    original: Any
    slots: dict[str, Any]
    runtime: dict[str, str]

    def Process(self, *, target: Any, args: tuple[Any, ...], daemon: bool) -> Any:
        if target is not _observed_serve or not daemon:
            raise ValueError("only frozen observed worker target supported")
        return self.original.Process(
            target=observed_target, args=(args, self.slots, self.runtime), daemon=daemon
        )


class MilestoneBackend(ShutdownBackend):
    def __init__(self, factory: Callable[[], LLMBackend], config: MilestoneConfig) -> None:
        if not isinstance(config, MilestoneConfig):
            raise TypeError("explicit milestone config required")
        self.observer_runtime = runtime_identity()
        super().__init__(factory, config)
        self._milestones = new_slots(self._ctx)
        self._ctx = cast(Any, _Context(self._ctx, self._milestones, self.observer_runtime))

    def exit_milestones(self) -> dict[str, Any]:
        if os.getpid() != self._owner_pid or self._process is not None:
            raise RuntimeError("owner may snapshot only after reaping")
        events = {
            name: None
            if self._milestones["time"][index] < 0
            else {
                "at": float(self._milestones["time"][index]),
                "pid": int(self._milestones["pid"][index]),
                "non_daemon_threads": int(self._milestones["threads"][index]),
            }
            for index, name in enumerate(EVENTS)
        }
        return {
            "protocol": "exit_milestones_v1",
            "runtime": self.observer_runtime,
            "execution_config_sha256": self.config.identity,
            "events": events,
        }
