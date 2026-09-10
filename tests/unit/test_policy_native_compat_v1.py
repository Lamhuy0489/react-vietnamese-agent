"""Offline package/harness tests; stub successes cannot certify native execution."""

import base64
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def entry(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("run_phase5_policy_native_compat")


def test_stub_all_cases_no_native_claim(entry: Any, tmp_path: Path) -> None:
    result = entry.run(tmp_path / "run", "stub", "a" * 40)
    assert result["valid"] and not result["native_library_verified"]
    assert result["model_generate_calls"] == result["weights_loaded"] == 0
    assert len(result["cases"]) == 4
    assert [r["caught"] for r in result["cases"]] == [
        None,
        None,
        "RuntimeError",
        "KeyboardInterrupt",
    ]
    assert not result["gpu_used"] and not result["phase5_accepted"]
    for case in ("agent_none", "guard_none"):
        audit = json.loads((tmp_path / f"run/{case}/audit.json").read_text())
        assert audit["valid"] and not audit["source_authenticated"]
    for case in ("guard_error", "guard_interrupt"):
        assert not (tmp_path / f"run/{case}/policy/completed.json").exists()
    with pytest.raises(ValueError, match="fresh"):
        entry.run(tmp_path / "run", "stub", "a" * 40)


@pytest.mark.parametrize("commit", ["", "a" * 39, "X" * 40, "a" * 41])
def test_invalid_identity_before_libraries(
    entry: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, commit: str
) -> None:
    def libraries(*args: Any) -> Any:
        raise AssertionError("no native imports")

    monkeypatch.setattr(entry, "libraries", libraries)
    with pytest.raises(ValueError):
        entry.run(tmp_path / "run", "native", commit)
    assert not (tmp_path / "run").exists()


def test_unexpected_harness_failure_cannot_pass(
    entry: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("synthetic unexpected failure")

    monkeypatch.setattr(entry.StubModel, "_prepare_special_tokens", fail)
    with pytest.raises(ValueError, match="expected harness outcome"):
        entry.run(tmp_path / "run", "stub", "a" * 40)
    assert not (tmp_path / "run/summary.json").exists()


@pytest.fixture
def wrapper(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    builder = importlib.import_module("prepare_phase5_policy_native")
    return builder.load(ROOT / "notebooks/kaggle/policy_native_kernel_v1.py")


def test_overlay_is_additive_and_avoids_weights(wrapper: Any) -> None:
    prior = json.loads(
        (ROOT / "experiments/manifests/phase5_pair_progress_gpu_v1_preflight01.json").read_text()
    )
    assert set(prior["overlay_sha256"]) < wrapper.OVERLAY_PATHS
    assert len(wrapper.OVERLAY_PATHS) == 25
    source = (ROOT / "notebooks/kaggle/policy_native_kernel_v1.py").read_text()
    assert '"guard-model.tar"' not in source and '"model.safetensors"' not in source
    assert '"native"' in source and "POLICY_NATIVE_CPU_COMPLETE" in source


@pytest.mark.parametrize("fault", ["hash", "missing", "extra", "overwrite"])
def test_overlay_rejects_mutations(wrapper: Any, tmp_path: Path, fault: str) -> None:
    base_path = ROOT / "notebooks/kaggle/guard_cancellation_kernel_v1.py"
    spec = importlib.util.spec_from_file_location("policy_base_test", base_path)
    assert spec and spec.loader
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    project = tmp_path / "project"
    project.mkdir()
    overlay = {
        name: {
            "base64": base64.b64encode((ROOT / name).read_bytes()).decode(),
            "sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
        }
        for name in wrapper.OVERLAY_PATHS
    }
    name = next(iter(overlay))
    original: dict[str, str] = {}
    if fault == "hash":
        overlay[name]["sha256"] = "0" * 64
    elif fault == "missing":
        overlay.pop(name)
    elif fault == "extra":
        overlay["extra.py"] = overlay[name]
    else:
        target = project / name
        target.parent.mkdir(parents=True)
        target.write_bytes((ROOT / name).read_bytes())
        original[name] = overlay[name]["sha256"]
    wrapper.OVERLAY = overlay
    with pytest.raises(ValueError):
        wrapper.install_overlay(base, project, original)
