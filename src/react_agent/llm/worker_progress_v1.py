"""Avoid child-owned tqdm semaphores in dedicated, non-forking model workers."""

from __future__ import annotations

import hashlib
import importlib
import multiprocessing as mp
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from react_agent.llm.base import LLMBackend

VERSION = "4.67.3"
STD_SHA256 = "4a4db84b039de7d86935b6f450bf18dfff2e79198bdffe4eef6572d9729ab231"


def configure_worker_progress() -> dict[str, str]:
    """Must precede native imports and first bar; no cleanup or hidden fallback.

    A task-owned daemon spawn worker never has child processes or shared output
    locks. Its own threads still require synchronization. Use tqdm's set_lock API
    with a reentrant threading lock, not multiprocessing synchronization. Refuse
    late/repeated calls instead of replacing/unlinking an already-live lock.
    """
    if (
        mp.parent_process() is None
        or not mp.current_process().daemon
        or mp.get_start_method(allow_none=True) != "spawn"
    ):
        raise RuntimeError("dedicated daemon spawn worker required")
    if "torch" in sys.modules or "transformers" in sys.modules:
        raise RuntimeError("configure progress before native model imports")
    package = importlib.import_module("tqdm")
    std = importlib.import_module("tqdm.std")
    if package.__version__ != VERSION:
        raise ValueError("pinned tqdm version required")
    source_path = getattr(std, "__file__", None)
    if (
        not isinstance(source_path, str)
        or hashlib.sha256(Path(source_path).read_bytes()).hexdigest() != STD_SHA256
    ):
        raise ValueError("pinned tqdm implementation required")
    if (
        package.tqdm is not std.tqdm
        or hasattr(std.tqdm, "_lock")
        or hasattr(std.TqdmDefaultWriteLock, "mp_lock")
        or len(std.tqdm._instances)
    ):
        raise RuntimeError("progress already initialized; no late lock replacement")
    lock = threading.RLock()
    std.tqdm.set_lock(lock)
    if std.tqdm.get_lock() is not lock or hasattr(std.TqdmDefaultWriteLock, "mp_lock"):
        raise RuntimeError("thread-only progress lock installation failed")
    return {
        "protocol": "worker_thread_progress_v1",
        "tqdm_version": VERSION,
        "tqdm_std_sha256": STD_SHA256,
        "lock": "threading.RLock",
        "scope": "one daemon spawn worker; no descendant processes",
    }


@dataclass(frozen=True)
class ThreadProgressFactory:
    """Opt-in factory for a future versioned GPU worker, not wired into v1 runs."""

    factory: Callable[[], LLMBackend]

    def __call__(self) -> LLMBackend:
        configure_worker_progress()
        return self.factory()
