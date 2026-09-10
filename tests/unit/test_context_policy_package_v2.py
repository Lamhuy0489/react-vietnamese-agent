"""Package boundaries and synthetic release composition; not GPU evidence."""

import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
from test_context_policy_audit_v1 import combined as combined
from test_context_policy_audit_v1 import write

from react_agent.validation.context_stress_audit_v1 import read_record
from react_agent.validation.guard_probe_audit_v2 import digest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def scripts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))


@pytest.mark.parametrize("fault", ["hash", "missing", "extra", "overwrite"])
def test_exact_overlay_rejects_mutation(scripts: None, tmp_path: Path, fault: str) -> None:
    builder = importlib.import_module("prepare_phase5_context_policy_v2")
    wrapper = builder.load(ROOT / "notebooks/kaggle/context_policy_kernel_v2.py")
    helper = importlib.import_module("test_policy_native_compat_v1")
    helper.test_overlay_rejects_mutations(wrapper, tmp_path, fault)


def test_overlay_preserves_every_native_cpu_source(scripts: None) -> None:
    builder = importlib.import_module("prepare_phase5_context_policy_v2")
    wrapper = builder.load(ROOT / "notebooks/kaggle/context_policy_kernel_v2.py")
    prior = read_record(
        ROOT / "experiments/manifests/phase5_context_policy_gpu_v1_preflight01.json"
    )
    assert len(wrapper.OVERLAY_PATHS) == 36
    assert set(prior["overlay_sha256"]) < wrapper.OVERLAY_PATHS
    assert all(digest(ROOT / n) == h for n, h in prior["overlay_sha256"].items())
    assert not any("credential" in n or "/test" in n.lower() for n in wrapper.OVERLAY_PATHS)


@pytest.mark.parametrize(
    "mode", ["hf", "stub", "nested", "existing", "no_commit", "hf_missing", "stub_guard"]
)
def test_dispatch_boundaries(
    scripts: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    entry = importlib.import_module("run_phase5_policy_stress_v3")
    hf = importlib.import_module("run_phase5_policy_stress_fixed")
    stub = importlib.import_module("run_phase5_context_stress_worker")
    compat = importlib.import_module("run_phase5_policy_native_compat")
    calls: list[Any] = []

    def fake() -> int:
        calls.append(list(sys.argv))
        return 0

    monkeypatch.setattr(hf, "main", fake)
    monkeypatch.setattr(stub, "main", fake)
    monkeypatch.setattr(compat, "run", lambda *a: calls.append(a))
    monkeypatch.setenv("PAIR_SOURCE_COMMIT", "a" * 40 if mode != "no_commit" else "")
    output, policy = tmp_path / "probe", tmp_path / "policy"
    if mode == "existing":
        output.mkdir()
    if mode == "nested":
        policy = output / "policy"
    argv = [
        "entry",
        "--backend",
        "hf" if mode in ("hf", "hf_missing") else "stub",
        "--output",
        str(output),
        "--policy-output",
        str(policy),
    ]
    if mode in ("hf", "stub_guard"):
        argv += ["--guard-path", "no-weights", "--snapshot", "no-snapshot"]
    monkeypatch.setattr(sys, "argv", argv)
    if mode not in ("hf", "stub"):
        with pytest.raises(ValueError):
            entry.main()
        assert not calls
    else:
        assert entry.main() == 0
        assert len(calls) == (1 if mode == "hf" else 2)
        assert ("--backend" in calls[0]) is (mode == "stub")
    assert sys.argv is argv


def test_dispatch_restores_argv_on_interruption(scripts: None) -> None:
    entry = importlib.import_module("run_phase5_policy_stress_v3")
    before = sys.argv

    def interrupt() -> int:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        entry.invoke(interrupt, ["synthetic"])
    assert sys.argv is before


@pytest.fixture
def release(combined: Any, scripts: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    auditor = importlib.import_module("audit_phase5_context_policy_gpu_v2")
    probe, policy, publishers, pin, commit = combined
    raw, remote, repo = tmp_path / "raw", tmp_path / "remote", tmp_path / "repo"
    shutil.copytree(probe, raw / "context_stress")
    shutil.copytree(policy, raw / "generation_policy")
    shutil.copytree(publishers, repo / "docs/evaluation/publisher_policy_v1")
    remote.mkdir()
    code = remote / "worker.py"
    code.write_text("# synthetic wrapper, no native execution\n")
    bundle = {
        "dataset": "synthetic/private",
        "snapshot": pin.model_dump(mode="json"),
        "wheel_sha256": {},
    }
    bundlepath = tmp_path / "bundle.json"
    write(bundlepath, bundle)
    preflight = tmp_path / "preflight.json"
    receipt = {
        "protocol": "context_policy_gpu_exact_preflight_v2",
        "valid": True,
        "phase5_accepted": False,
        "source_commit": commit,
        "base_source_sha256": "b" * 64,
        "bundle_manifest_sha256": digest(bundlepath),
        "overlay_sha256": {},
        "wrapper_sha256": digest(code),
        "prerequisites": {"synthetic": True},
        "checks": [
            {
                "layout": layout,
                "factory_shape": {
                    "protocol": "policy_factory_shape_rehearsal_v1",
                    "valid": True,
                    "native_context_verified": False,
                    "rows": [
                        {
                            "statuses": statuses,
                            "all_handles_reaped": True,
                            "stress_call_not_consumed": True,
                            "native_model_calls": 0,
                            "weights_loaded": 0,
                        }
                        for statuses in (["BACKEND_FAILURE"], ["OK", "OK"])
                    ],
                },
            }
            for layout in ("archive", "expanded")
        ],
    }
    write(preflight, receipt)
    write(
        raw / "context_policy_bootstrap_identity.json",
        {
            "protocol": "context_policy_bootstrap_v2",
            **{
                k: receipt[k]
                for k in (
                    "source_commit",
                    "base_source_sha256",
                    "bundle_manifest_sha256",
                    "overlay_sha256",
                )
            },
            "snapshot": bundle["snapshot"],
            "wheel_sha256": {},
        },
    )
    write(
        remote / "kernel-metadata.json",
        {
            "code_file": "worker.py",
            "id": "huylmhuhu/react-vn-context-policy-v2",
            "is_private": True,
            "enable_gpu": True,
            "enable_tpu": False,
            "enable_internet": False,
            "machine_shape": "NvidiaTeslaT4",
            "docker_image": auditor.IMAGE,
            "dataset_sources": [bundle["dataset"]],
            "model_sources": ["qwen-lm/qwen2.5/Transformers/7b-instruct/1"],
            "kernel_sources": [],
            "competition_sources": [],
        },
    )
    (raw / "react-vn-context-policy-v2.log").write_text(
        "synthetic CONTEXT_POLICY_GPU_V2_COMPLETE\n"
    )
    write(raw / "dummy/identity.json", {"task_ids": []})
    write(raw / "dummy/results.json", [])
    write(raw / "dummy/summary.json", {})
    monkeypatch.setattr(auditor, "ROOT", repo)
    monkeypatch.setattr(auditor, "BUNDLE", bundlepath)
    monkeypatch.setattr(auditor, "BUNDLE_SHA", digest(bundlepath))
    monkeypatch.setattr(auditor, "prerequisites", lambda _: {"synthetic": True})
    # Dummy's full21/84-event behavior is covered by its frozen independent tests.
    monkeypatch.setattr(auditor, "audit_dummy", lambda r, b: {"synthetic_test_transport": True})
    return auditor, raw, remote, preflight


def test_outer_composes_real_inner_validator(release: Any) -> None:
    auditor, raw, remote, preflight = release
    result = auditor.audit(raw, remote, preflight)
    assert result == auditor.audit(raw, remote, preflight)
    assert result["combined"]["publisher_metadata_authenticated"]
    assert not result["phase5_accepted"]


@pytest.mark.parametrize(
    "case",
    [
        "wrapper",
        "private",
        "gpu",
        "model_version",
        "bootstrap",
        "extra_raw",
        "missing_log",
        "extra_remote",
        "preflight",
        "policy",
    ],
)
def test_outer_corruption_rejected(release: Any, case: str) -> None:
    auditor, raw, remote, preflight = release
    if case == "wrapper":
        (remote / "worker.py").write_text("different")
    elif case == "extra_raw":
        write(raw / "extra.json", {})
    elif case == "missing_log":
        (raw / "react-vn-context-policy-v2.log").unlink()
    elif case == "extra_remote":
        write(remote / "extra.json", {})
    elif case == "policy":
        p = raw / "generation_policy/agent/entered.json"
        v = read_record(p)
        v["publisher"]["repetition_penalty"] = 1.1
        write(p, v)
    else:
        p = (
            preflight
            if case == "preflight"
            else (
                raw / "context_policy_bootstrap_identity.json"
                if case == "bootstrap"
                else remote / "kernel-metadata.json"
            )
        )
        v = json.loads(p.read_text())
        if case in ("preflight", "bootstrap"):
            v["source_commit"] = "e" * 40
        elif case == "private":
            v["is_private"] = False
        elif case == "gpu":
            v["enable_gpu"] = False
        elif case == "model_version":
            v["model_sources"] = ["qwen-lm/qwen2.5/Transformers/7b-instruct/2"]
        write(p, v)
    with pytest.raises((ValueError, FileNotFoundError)):
        auditor.audit(raw, remote, preflight)


@pytest.mark.parametrize("case", ["missing", "native", "unreaped", "consumed", "old_protocol"])
def test_requires_actual_factory_preflight(release: Any, case: str) -> None:
    auditor, raw, remote, preflight = release
    value = read_record(preflight)
    if case == "missing":
        value["checks"] = []
    elif case == "old_protocol":
        value["protocol"] = "context_policy_gpu_exact_preflight_v1"
    elif case == "native":
        value["checks"][0]["factory_shape"]["native_context_verified"] = True
    else:
        key = "all_handles_reaped" if case == "unreaped" else "stress_call_not_consumed"
        value["checks"][1]["factory_shape"]["rows"][1][key] = False
    write(preflight, value)
    with pytest.raises(ValueError):
        auditor.audit(raw, remote, preflight)
