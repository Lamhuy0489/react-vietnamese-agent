"""CPU-only progress-lock scope, failures and native synthetic controls."""

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from react_agent.llm import worker_progress_v1 as mod


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Any, Any]:
    class Bar:
        _instances: set[Any] = set()

        @classmethod
        def set_lock(cls, lock: Any) -> None:
            cls._lock = lock

        @classmethod
        def get_lock(cls) -> Any:
            return cls._lock

    source = tmp_path / "std.py"
    source.write_text("synthetic source")
    std = SimpleNamespace(__file__=str(source), tqdm=Bar, TqdmDefaultWriteLock=type("Lock", (), {}))
    package = SimpleNamespace(__version__=mod.VERSION, tqdm=Bar)
    monkeypatch.setattr(mod, "STD_SHA256", hashlib.sha256(source.read_bytes()).hexdigest())
    original = importlib.import_module
    monkeypatch.setattr(
        mod.importlib,
        "import_module",
        lambda n: {"tqdm": package, "tqdm.std": std}.get(n) or original(n),
    )
    monkeypatch.setattr(mod.mp, "parent_process", lambda: object())
    monkeypatch.setattr(mod.mp, "current_process", lambda: SimpleNamespace(daemon=True))
    monkeypatch.setattr(mod.mp, "get_start_method", lambda **kw: "spawn")
    monkeypatch.delitem(sys.modules, "torch", raising=False)
    monkeypatch.delitem(sys.modules, "transformers", raising=False)
    return package, std


def test_install_thread_lock_once(fake: tuple[Any, Any]) -> None:
    package, std = fake
    result = mod.configure_worker_progress()
    assert result["lock"] == "threading.RLock"
    lock = std.tqdm.get_lock()
    with lock:
        with lock:
            assert package.tqdm.get_lock() is lock
    assert not hasattr(std.TqdmDefaultWriteLock, "mp_lock")
    with pytest.raises(RuntimeError, match="already initialized"):
        mod.configure_worker_progress()
    assert std.tqdm.get_lock() is lock


@pytest.mark.parametrize(
    "mode",
    [
        "owner",
        "non_daemon",
        "fork",
        "torch",
        "transformers",
        "version",
        "hash",
        "file",
        "class",
        "lock",
        "mp_lock",
        "bar",
    ],
)
def test_reject_unsupported_or_late_context(
    fake: tuple[Any, Any], monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    package, std = fake
    if mode == "owner":
        monkeypatch.setattr(mod.mp, "parent_process", lambda: None)
    elif mode == "non_daemon":
        monkeypatch.setattr(mod.mp, "current_process", lambda: SimpleNamespace(daemon=False))
    elif mode == "fork":
        monkeypatch.setattr(mod.mp, "get_start_method", lambda **kw: "fork")
    elif mode in ("torch", "transformers"):
        monkeypatch.setitem(sys.modules, mode, SimpleNamespace())
    elif mode == "version":
        package.__version__ = "other"
    elif mode == "hash":
        monkeypatch.setattr(mod, "STD_SHA256", "0" * 64)
    elif mode == "file":
        std.__file__ = None
    elif mode == "class":
        package.tqdm = object()
    elif mode == "lock":
        std.tqdm._lock = object()
    elif mode == "mp_lock":
        std.TqdmDefaultWriteLock.mp_lock = object()
    elif mode == "bar":
        std.tqdm._instances.add(object())
    with pytest.raises((RuntimeError, ValueError)):
        mod.configure_worker_progress()


def test_factory_is_lazy_and_configures_before_load(monkeypatch: pytest.MonkeyPatch) -> None:
    events = []
    monkeypatch.setattr(mod, "configure_worker_progress", lambda: events.append("configured"))

    def factory() -> Any:
        events.append("load")
        return SimpleNamespace(model_id="synthetic", model_revision="v1")

    wrapped = mod.ThreadProgressFactory(factory)
    assert events == []
    assert wrapped().model_id == "synthetic"
    assert events == ["configured", "load"]


def test_factory_failure_does_not_load(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail() -> Any:
        raise ValueError("unsupported native progress implementation")

    monkeypatch.setattr(mod, "configure_worker_progress", fail)

    def factory() -> Any:
        raise AssertionError("must not load")

    with pytest.raises(ValueError):
        mod.ThreadProgressFactory(factory)()


def test_native_real_spawn_controls(tmp_path: Path) -> None:
    # Native dependency optional in CI; the selected local receipt must separately
    # prove this test was run, not skipped. No pip install, model or network here.
    try:
        package = importlib.import_module("tqdm")
    except ImportError:
        pytest.skip("native tqdm unavailable; run CPU receipt with pinned dependency")
    if package.__version__ != mod.VERSION:
        pytest.skip("native tqdm not pinned; run selected CPU receipt separately")
    output = tmp_path / "native"
    result = subprocess.run(  # noqa: S603 - fixed synthetic script and interpreter
        [sys.executable, "scripts/probe_phase5_worker_progress.py", "--output", str(output)],
        capture_output=True,
        text=True,
        timeout=100,
    )
    assert result.returncode == 0, result.stderr
    value = json.loads((output / "receipt.json").read_text())
    assert value["valid"] and value["gpu_runs"] == value["model_loads"] == 0
    assert [r["register_calls"] for r in value["observations"].values()] == [1, 1, 0, 0]
