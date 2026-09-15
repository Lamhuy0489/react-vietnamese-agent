"""Synthetic release-boundary mutations; never promote these fixtures to native evidence."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def case(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "release", ROOT / "scripts/audit_phase5_observer_gpu_v2.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    bundle_path = tmp_path / "bundle.json"
    monkeypatch.setattr(module, "BUNDLE", bundle_path)
    # Pin parsing remains out of this release boundary test; native audit has its own tests.
    monkeypatch.setattr(module, "GuardSnapshot", SimpleNamespace(model_validate=lambda x: x))
    result = dict(artifact_integrity_valid=True, source_authenticated=False, fixture=True)
    monkeypatch.setattr(module, "native_audit", lambda *a: result)

    def put(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    package = tmp_path / "build/kaggle/package"
    remote, raw = tmp_path / "remote", tmp_path / "raw"
    metadata = dict(
        id="synthetic/observer",
        id_no=1,
        code_file="worker.py",
        is_private=True,
        enable_gpu=True,
        enable_tpu=False,
        enable_internet=False,
        machine_shape="NvidiaTeslaT4",
        docker_image="fixed",
        dataset_sources=["synthetic/data"],
        competition_sources=[],
        kernel_sources=[],
        language="python",
        kernel_type="script",
        model_sources=["synthetic/model/1"],
    )
    put(package / "kernel/kernel-metadata.json", metadata)
    put(remote / "kernel-metadata.json", metadata)
    (remote / "worker.py").write_text("# synthetic, never executed\n")
    bundle = dict(snapshot={}, wheel_sha256={})
    put(bundle_path, bundle)
    full = dict(dataset_manifest_sha256=module.digest(bundle_path), package_sha256={})
    put(package / "preflight_receipt.json", full)
    selected = dict(
        valid=True,
        native_submission_ready=True,
        source_commit="a" * 40,
        package_path="build/kaggle/package",
        full_receipt_sha256=module.digest(package / "preflight_receipt.json"),
        source_sha256={},
        kernel_sha256={
            "observer_native_kernel_v2.py": module.digest(remote / "worker.py"),
            "kernel-metadata.json": module.digest(package / "kernel/kernel-metadata.json"),
        },
        archive_sha256="b" * 64,
    )
    preflight = tmp_path / "preflight.json"
    put(preflight, selected)
    submission = tmp_path / "submission.json"
    put(
        submission,
        dict(
            submission_confirmed=True,
            preflight_sha256=module.digest(preflight),
            kernel_version=1,
            source_commit="a" * 40,
            actual_kernel="synthetic/observer",
            notebook_url="synthetic",
        ),
    )
    observation = tmp_path / "observation.json"
    put(
        observation,
        dict(
            submission_sha256=module.digest(submission),
            kernel_version=1,
            kernel_id=1,
            session_status=dict(status="COMPLETE"),
            actual_kernel="synthetic/observer",
            remote_sha256=module.inventory(remote),
        ),
    )
    put(
        raw / "observer_bootstrap.json",
        dict(
            protocol="observer_native_package_v2",
            source_commit="a" * 40,
            source_sha256={},
            source_archive_sha256="b" * 64,
            bundle_manifest_sha256=module.digest(bundle_path),
            snapshot={},
            wheel_sha256={},
            phase5_accepted=False,
        ),
    )
    put(raw / "native_audit.json", result)
    return module, (raw, remote, preflight, submission, observation)


def test_release_boundary_readonly_repeatable(case):
    module, args = case
    first = module.audit(*args)
    assert first == module.audit(*args)
    assert first["source_authenticated"] and not first["phase5_accepted"]


@pytest.mark.parametrize(
    "fault",
    ["version", "running", "submission_pin", "remote_code", "bootstrap", "native_report", "public"],
)
def test_mutated_release_rejected(case, fault):
    module, args = case
    raw, remote, _, _, obs = args
    if fault in {"version", "running", "submission_pin"}:
        value = json.loads(obs.read_text())
        if fault == "version":
            value["kernel_version"] = 2
        elif fault == "running":
            value["session_status"]["status"] = "RUNNING"
        else:
            value["submission_sha256"] = "0" * 64
        obs.write_text(json.dumps(value))
    elif fault == "remote_code":
        (remote / "worker.py").write_text("tampered")
    elif fault == "bootstrap":
        (raw / "observer_bootstrap.json").write_text("{}")
    elif fault == "native_report":
        (raw / "native_audit.json").write_text("{}")
    else:
        value = json.loads((remote / "kernel-metadata.json").read_text())
        value["is_private"] = False
        (remote / "kernel-metadata.json").write_text(json.dumps(value))
        value = json.loads(obs.read_text())
        value["remote_sha256"] = module.inventory(remote)
        obs.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        module.audit(*args)
