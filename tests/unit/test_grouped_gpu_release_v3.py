"""Remote metadata/hash controls and terminal release joins; never model inference."""

import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def auditor(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("audit_phase5_grouped_gpu_v3")


@pytest.fixture
def remote_fixture(auditor, tmp_path):
    remote = tmp_path / "remote"
    remote.mkdir()
    (remote / "code.py").write_text("raise RuntimeError('must never execute downloaded code')")
    submission = dict(
        actual_kernel="huylmhuhu/react-vn-grouped-dev-v3-shard-0", kernel_id=42, shard=0
    )
    metadata = dict(
        id=submission["actual_kernel"],
        id_no=42,
        code_file="code.py",
        is_private=True,
        enable_gpu=True,
        enable_tpu=False,
        enable_internet=False,
        machine_shape="NvidiaTeslaT4",
        docker_image=auditor.IMAGE,
        dataset_sources=[auditor.DATASET],
        kernel_sources=[],
        competition_sources=[],
        language="python",
        kernel_type="script",
        model_sources=[auditor.MODEL],
    )
    (remote / "kernel-metadata.json").write_text(json.dumps(metadata))
    preflight = dict(
        kernels=[
            dict(shard=0, files={"grouped_native_kernel_v3.py": auditor.digest(remote / "code.py")})
        ]
    )
    return remote, metadata, preflight, submission


def test_remote_identity_uses_actual_slug_and_does_not_execute(auditor, remote_fixture):
    remote, _, preflight, submission = remote_fixture
    before = auditor.inventory(remote)
    result = auditor.remote_identity(remote, preflight, submission)
    assert result["sha256"] == before == auditor.inventory(remote)


@pytest.mark.parametrize(
    "fault",
    [
        "public",
        "internet",
        "image",
        "model",
        "dataset",
        "shard",
        "code",
        "extra",
        "path",
        "link",
        "bool_type",
    ],
)
def test_remote_tampering_rejected(auditor, remote_fixture, fault):
    remote, metadata, preflight, submission = remote_fixture
    if fault == "public":
        metadata["is_private"] = False
    elif fault == "internet":
        metadata["enable_internet"] = True
    elif fault == "image":
        metadata["docker_image"] = "latest"
    elif fault == "model":
        metadata["model_sources"] = [auditor.MODEL[:-1] + "2"]
    elif fault == "dataset":
        metadata["dataset_sources"] = ["another/dataset"]
    elif fault == "shard":
        submission["shard"] = True
    elif fault == "code":
        (remote / "code.py").write_text("changed")
    elif fault == "extra":
        (remote / "extra").write_text("extra")
    elif fault == "path":
        metadata["code_file"] = "../outside.py"
    elif fault == "link":
        (remote / "link").symlink_to(remote / "code.py")
    else:
        metadata["enable_gpu"] = 1
    (remote / "kernel-metadata.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError):
        auditor.remote_identity(remote, preflight, submission)


@pytest.fixture
def joined_fixture(auditor, tmp_path, monkeypatch):
    bundle = tmp_path / "bundle.json"
    snapshot = json.loads((ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text())
    bundle.write_text(json.dumps(dict(snapshot=snapshot)))
    monkeypatch.setattr(auditor, "BUNDLE", bundle)
    raw, remote = tmp_path / "raw", tmp_path / "remote"
    raw.mkdir()
    remote.mkdir()
    (raw / "grouped").mkdir()
    (raw / "grouped/fixture").write_text("synthetic boundary fixture")
    (raw / "tokenizers").mkdir()
    for name in ("agent_tokenizer_config.json", "guard_tokenizer_config.json"):
        (raw / "tokenizers" / name).write_text("{}")
    (raw / "grouped_bootstrap.json").write_text("{}")
    (raw / "kernel.log").write_text("synthetic")
    joined = dict(
        complete=True, completed=14, tasks=[], raw_sha256=auditor.inventory(raw / "grouped")
    )
    (raw / "native_audit.json").write_text(json.dumps(joined, indent=2, sort_keys=True) + "\n")
    submission = dict(shard=0, actual_kernel="owner/kernel", kernel_version=1)
    preflight = dict(source_commit="a" * 40)
    monkeypatch.setattr(
        auditor,
        "authenticate",
        lambda *a: (preflight, submission, dict(sha256=auditor.inventory(remote))),
    )
    monkeypatch.setattr(auditor, "identity", lambda *a: ({}, ()))
    monkeypatch.setattr(auditor, "native_audit", lambda *a: joined)
    preflight_path, submission_path = tmp_path / "preflight.json", tmp_path / "submission.json"
    preflight_path.write_text("{}")
    submission_path.write_text("{}")
    return (raw, remote, preflight_path, submission_path), joined


def test_complete_join_is_readonly_and_not_quality(auditor, joined_fixture):
    args, _ = joined_fixture
    before = auditor.inventory(args[0])
    result = auditor.audit(*args)
    assert result["remote_source_authenticated"] and result["completed"] == 14
    assert not result["guard_quality_validated"] and not result["phase5_accepted"]
    assert before == auditor.inventory(args[0])


@pytest.mark.parametrize("fault", ["incomplete", "worker_claim", "extra", "noncanonical", "repeat"])
def test_release_requires_exact_complete_reproducible_join(
    auditor, joined_fixture, monkeypatch, fault
):
    args, joined = joined_fixture
    raw = args[0]
    if fault == "incomplete":
        joined["completed"], joined["complete"] = 13, False
    elif fault == "worker_claim":
        (raw / "native_audit.json").write_text("{}")
    elif fault == "extra":
        (raw / "extra").write_text("unexpected")
    elif fault == "noncanonical":
        (raw / "native_audit.json").write_text(json.dumps(joined))
    else:
        calls = []

        def unstable(*args):
            calls.append(1)
            return joined if len(calls) == 1 else dict(joined, complete=False)

        monkeypatch.setattr(auditor, "native_audit", unstable)
    with pytest.raises(ValueError):
        auditor.audit(*args)


@pytest.mark.parametrize(
    "fault", [None, "commit", "preflight_pin", "source", "bootstrap", "bundle", "unconfirmed"]
)
def test_bootstrap_and_source_binding(auditor, remote_fixture, tmp_path, monkeypatch, fault):
    remote, _, preflight, submission = remote_fixture
    raw = tmp_path / "raw"
    raw.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle = dict(dataset=auditor.DATASET, snapshot={"synthetic": True}, wheel_sha256={})
    bundle_path.write_text(json.dumps(bundle))
    monkeypatch.setattr(auditor, "BUNDLE", bundle_path)
    source = {"pyproject.toml": auditor.digest(ROOT / "pyproject.toml")}
    preflight.update(
        protocol="grouped_package_v3_preflight",
        valid=True,
        package_rehearsal_passed=True,
        source_commit="a" * 40,
        source_sha256=source,
        package_sha256=source,
        archive_sha256="b" * 64,
        bundle_manifest_sha256=auditor.digest(bundle_path),
    )
    submission.update(submission_confirmed=True, source_commit="a" * 40)
    bootstrap = dict(
        protocol="grouped_native_package_v3",
        source_commit="a" * 40,
        source_sha256=source,
        source_archive_sha256="b" * 64,
        shard=0,
        bundle_manifest_sha256=auditor.digest(bundle_path),
        snapshot=bundle["snapshot"],
        wheel_sha256={},
        phase5_accepted=False,
    )
    if fault == "commit":
        submission["source_commit"] = "c" * 40
    elif fault == "source":
        preflight["source_sha256"] = {"pyproject.toml": "0" * 64}
    elif fault == "bootstrap":
        bootstrap["shard"] = 1
    elif fault == "bundle":
        bundle_path.write_text("{}")
    elif fault == "unconfirmed":
        submission["submission_confirmed"] = False
    (raw / "grouped_bootstrap.json").write_text(json.dumps(bootstrap))
    preflight_path, submission_path = tmp_path / "preflight.json", tmp_path / "submission.json"
    preflight_path.write_text(json.dumps(preflight))
    submission["preflight_sha256"] = auditor.digest(preflight_path)
    if fault == "preflight_pin":
        submission["preflight_sha256"] = "0" * 64
    submission_path.write_text(json.dumps(submission))
    args = raw, remote, preflight_path, submission_path
    if fault is None:
        result = auditor.authenticate(*args)
        assert result[0] == preflight and result[1] == submission
    else:
        with pytest.raises(ValueError):
            auditor.authenticate(*args)
