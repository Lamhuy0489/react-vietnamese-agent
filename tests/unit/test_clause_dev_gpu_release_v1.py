"""Synthetic release boundaries, not native/GPU evidence; native audit is mocked explicitly."""

import base64
import importlib.util
import io
import json
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def case(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "constrained_release", ROOT / "scripts/audit_phase5_clause_dev_gpu_v1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "BUNDLE", tmp_path / "bundle.json")
    monkeypatch.setattr(module, "GuardSnapshot", SimpleNamespace(model_validate=lambda x: x))
    result = dict(protocol="clause_dev32_native_all_v1", fixture=True, source_authenticated=False)
    monkeypatch.setattr(module, "native_audit", lambda *a: result)

    def put(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def mutate(path, key, value):
        record = json.loads(path.read_text())
        record[key] = value
        put(path, record)

    package = tmp_path / "build/kaggle/package"
    kernel, remote, raw = package / "kernel", tmp_path / "remote", tmp_path / "raw"
    for p in (kernel, remote, raw):
        p.mkdir(parents=True)
    source = "notebooks/kaggle/guard_cancellation_kernel_v1.py"
    (tmp_path / source).parent.mkdir(parents=True)
    (tmp_path / source).write_text("raise AssertionError('never execute remote Python')\n")
    template = "notebooks/kaggle/clause_dev32_kernel_v1.py"
    (tmp_path / template).write_text((ROOT / template).read_text())
    pins = {name: module.digest(tmp_path / name) for name in sorted((source, template))}
    monkeypatch.setattr(module, "git_digest", lambda commit, name: pins[name])
    archive = package / "source.tar.gz"
    with tarfile.open(archive, "w:gz") as stream:
        for name in sorted(pins):
            value = (tmp_path / name).read_bytes()
            member = tarfile.TarInfo(name)
            member.size = len(value)
            stream.addfile(member, io.BytesIO(value))
    put(module.BUNDLE, dict(dataset="synthetic/data", snapshot={}, wheel_sha256={}))
    constants = dict(
        SOURCE_COMMIT="a" * 40,
        SOURCE_MODE="committed",
        SOURCE_FILES=pins,
        ARCHIVE=base64.b64encode(archive.read_bytes()).decode(),
        ARCHIVE_SHA=module.digest(archive),
        BUNDLE_SHA=module.digest(module.BUNDLE),
        BASE_SHA=pins[source],
        BASE_SOURCE=base64.b64encode((tmp_path / source).read_bytes()).decode(),
    )
    code = (tmp_path / template).read_text()
    for key, value in constants.items():
        marker = "{}  # __SOURCE_FILES__" if key == "SOURCE_FILES" else "__" + key + "__"
        code = code.replace(marker, repr(value) if key == "SOURCE_FILES" else value)
    admission = dict(
        protocol="clause_dev32_source_v1",
        source_mode="committed",
        source_commit="a" * 40,
        git_base_commit="a" * 40,
        source_sha256=pins,
        archive_sha256=module.digest(archive),
    )
    put(package / "source_manifest.json", admission)
    put(raw / "source_manifest.json", admission)
    (kernel / module.CODE).write_text(code)
    (remote / module.CODE).write_text(code)
    metadata = dict(
        id="synthetic/constrained",
        code_file=module.CODE,
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
    put(kernel / "kernel-metadata.json", metadata)
    put(remote / "kernel-metadata.json", metadata | dict(id_no=1))
    full = dict(
        protocol="clause_dev32_package_v1_cpu",
        valid=True,
        native_submission_ready=True,
        source_commit="a" * 40,
        source_mode="committed",
        source_sha256=pins,
        package_sha256=pins,
        archive_sha256=module.digest(archive),
        dataset_manifest_sha256=module.digest(module.BUNDLE),
        kernel_sha256=module.inventory(kernel),
        requested_notebook=metadata["id"],
        checks=[
            dict(
                layout=layout,
                valid=True,
                tools=8,
                clean_dummy_tasks=21,
                dev32=dict(
                    runtime_tasks=32,
                    valid=True,
                    missing_only_resume=True,
                    complete_resume=True,
                    source_bytes_verified=True,
                ),
            )
            for layout in ("archive", "expanded")
        ],
    )
    full_path = package / "preflight_receipt.json"
    put(full_path, full)
    preflight, submission, observation = (
        tmp_path / name for name in ("preflight.json", "submission.json", "observation.json")
    )
    put(
        preflight,
        full
        | dict(
            package_path="build/kaggle/package", original_receipt_sha256=module.digest(full_path)
        ),
    )
    sub = dict(
        submission_confirmed=True,
        preflight_sha256=module.digest(preflight),
        kernel_version=1,
        kernel_id=1,
        source_commit="a" * 40,
        actual_kernel=metadata["id"],
        private=True,
        notebook_url="https://www.kaggle.com/code/" + metadata["id"],
        remote_source_sha256=module.digest(remote / module.CODE),
        dataset="synthetic/data",
        dataset_version=1,
    )
    put(submission, sub)
    put(
        raw / "observer_bootstrap.json",
        dict(
            protocol="clause_dev32_package_v1",
            source_mode="committed",
            source_commit="a" * 40,
            source_sha256=pins,
            source_archive_sha256=module.digest(archive),
            bundle_manifest_sha256=module.digest(module.BUNDLE),
            snapshot={},
            wheel_sha256={},
            phase5_accepted=False,
        ),
    )
    put(raw / "native_audit.json", result)
    observed = {
        k: sub[k]
        for k in ("kernel_version", "kernel_id", "actual_kernel", "private", "remote_source_sha256")
    }
    observed["session_status"] = dict(status="COMPLETE")
    put(
        observation,
        observed
        | dict(
            before_download=observed,
            submission_sha256=module.digest(submission),
            raw_sha256=module.inventory(raw),
            remote_sha256=module.inventory(remote),
        ),
    )

    def repin():
        mutate(preflight, "original_receipt_sha256", module.digest(full_path))
        mutate(submission, "preflight_sha256", module.digest(preflight))
        mutate(observation, "submission_sha256", module.digest(submission))
        mutate(observation, "raw_sha256", module.inventory(raw))
        mutate(observation, "remote_sha256", module.inventory(remote))

    return SimpleNamespace(
        module=module,
        args=(raw, remote, preflight, submission, observation),
        package=package,
        put=put,
        mutate=mutate,
        repin=repin,
        source=source,
    )


def test_readonly_repeatable_release(case):
    before = case.module.inventory(case.module.ROOT)
    result = case.module.audit(*case.args)
    assert result == case.module.audit(*case.args)
    assert result["source_authenticated"] and not result["guard_quality_validated"]
    assert not result["phase5_accepted"] and result["native"]["fixture"]
    assert before == case.module.inventory(case.module.ROOT)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source_mode", "working_tree"),
        ("native_submission_ready", False),
        ("valid", 1),
        ("source_commit", "a" * 39),
        ("source_commit", "A" * 40),
        ("package_path", "../outside"),
        ("package_path", "/outside"),
        ("package_sha256", {}),
        ("source_sha256", {}),
        ("protocol", "observer_native_package_v2"),
    ],
)
def test_bad_preflight(case, key, value):
    case.mutate(case.args[2], key, value)
    case.repin()
    with pytest.raises(ValueError):
        case.module.audit(*case.args)


@pytest.mark.parametrize(
    "key,value",
    [
        ("kernel_version", 2),
        ("kernel_version", True),
        ("kernel_id", 2),
        ("private", False),
        ("actual_kernel", "synthetic/other"),
        ("remote_source_sha256", "0" * 64),
        ("session_status", {"status": "RUNNING"}),
        ("session_status", {"status": "ERROR"}),
        ("raw_sha256", {}),
        ("remote_sha256", {}),
        ("submission_sha256", "0" * 64),
    ],
)
def test_bad_post_download(case, key, value):
    case.mutate(case.args[4], key, value)
    with pytest.raises(ValueError):
        case.module.audit(*case.args)


def test_version_changes_during_download(case):
    observed = json.loads(case.args[4].read_text())
    observed["before_download"]["kernel_version"] = 2
    case.put(case.args[4], observed)
    with pytest.raises(ValueError, match="download identity"):
        case.module.audit(*case.args)


@pytest.mark.parametrize(
    "key,value",
    [
        ("kernel_id", True),
        ("kernel_version", 0),
        ("private", False),
        ("notebook_url", "https://example.com"),
        ("dataset_version", True),
        ("dataset_version", 2),
        ("dataset", "synthetic/other"),
        ("submission_confirmed", 1),
    ],
)
def test_bad_submission(case, key, value):
    case.mutate(case.args[3], key, value)
    case.repin()
    with pytest.raises(ValueError):
        case.module.audit(*case.args)


@pytest.mark.parametrize(
    "key,value",
    [
        ("is_private", False),
        ("enable_internet", True),
        ("machine_shape", "other"),
        ("model_sources", ["synthetic/model/2"]),
        ("dataset_sources", ["synthetic/other"]),
        ("id_no", True),
        ("code_file", "../outside.py"),
    ],
)
def test_remote_metadata_mutation_even_if_download_rehashed(case, key, value):
    case.mutate(case.args[1] / "kernel-metadata.json", key, value)
    case.repin()
    with pytest.raises(ValueError):
        case.module.audit(*case.args)


@pytest.mark.parametrize("fault", ["source", "git", "archive", "bootstrap", "native", "code"])
def test_bound_content_mutation(case, monkeypatch, fault):
    if fault == "source":
        (case.module.ROOT / case.source).write_text("tampered")
    elif fault == "git":
        monkeypatch.setattr(case.module, "git_digest", lambda *a: "0" * 64)
    elif fault == "archive":
        (case.package / "source.tar.gz").write_bytes(b"tampered")
    elif fault == "code":
        (case.args[1] / case.module.CODE).write_text("raise AssertionError('not executed')")
    else:
        name = "observer_bootstrap.json" if fault == "bootstrap" else "source_manifest.json"
        case.put(case.args[0] / name, {})
    case.repin()
    with pytest.raises(ValueError):
        case.module.audit(*case.args)


def test_duplicate_json_key_rejected(case):
    case.args[4].write_text('{"kernel_version": 1, "kernel_version": 2}')
    with pytest.raises(ValueError, match="duplicate"):
        case.module.audit(*case.args)


def test_linked_raw_rejected(case):
    (case.args[0] / "linked.json").symlink_to(case.args[2])
    with pytest.raises(ValueError):
        case.module.audit(*case.args)


def test_pinned_local_cache_is_not_remote_source(case):
    cache = case.package / "kernel/__pycache__/clause_dev32_kernel_v1.cpython-311.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"synthetic cache never executed")
    pins = case.module.inventory(case.package / "kernel")
    case.mutate(case.package / "preflight_receipt.json", "kernel_sha256", pins)
    case.mutate(case.args[2], "kernel_sha256", pins)
    case.repin()
    assert case.module.audit(*case.args)["valid"]


@pytest.mark.parametrize("fault", ["duplicate", "traversal", "link"])
def test_archive_members_rejected_even_with_rehashed_archive(case, fault):
    archive = case.package / "source.tar.gz"
    with tarfile.open(archive, "w:gz") as stream:
        member = tarfile.TarInfo("../escape" if fault == "traversal" else case.source)
        if fault == "link":
            member.type, member.linkname = tarfile.SYMTYPE, "elsewhere"
        stream.addfile(member)
        if fault == "duplicate":
            stream.addfile(member)
    for path in (case.args[2], case.package / "preflight_receipt.json"):
        case.mutate(path, "archive_sha256", case.module.digest(archive))
    case.repin()
    with pytest.raises(ValueError):
        case.module.audit(*case.args)


@pytest.mark.parametrize("literal", ["SOURCE_MODE", "SOURCE_COMMIT", "ARCHIVE", "BASE_SOURCE"])
def test_rehashed_launcher_still_binds_embedded_content(case, literal):
    code = case.package / "kernel" / case.module.CODE
    lines = code.read_text().splitlines()
    code.write_text(
        "\n".join(
            f"{literal} = 'wrong'" if line.startswith(literal + " =") else line for line in lines
        )
    )
    pins = case.module.inventory(case.package / "kernel")
    for path in (case.args[2], case.package / "preflight_receipt.json"):
        case.mutate(path, "kernel_sha256", pins)
    case.repin()
    with pytest.raises(ValueError):
        case.module.audit(*case.args)


def test_duplicate_launcher_constant_rejected(case):
    code = case.package / "kernel" / case.module.CODE
    code.write_text(code.read_text() + "\nSOURCE_MODE = 'committed'\n")
    with pytest.raises(ValueError, match="unique launcher"):
        case.module.constants(code)


def test_model_mount_case_normalization(case):
    case.mutate(case.args[1] / "kernel-metadata.json", "model_sources", ["SYNTHETIC/MODEL/1"])
    case.repin()
    assert case.module.audit(*case.args)["valid"]


@pytest.mark.parametrize("target", ["outside.json", "results", "results/input/audit.json"])
def test_cli_output_containment(case, monkeypatch, target):
    arguments = []
    for name, path in zip(
        ("raw", "remote", "preflight", "submission", "observation"), case.args, strict=True
    ):
        if name == "raw" and target.startswith("results/input"):
            path = case.module.ROOT / "results/input"
        arguments.extend(["--" + name, str(path)])
    monkeypatch.setattr(
        "sys.argv", ["audit", *arguments, "--output", str(case.module.ROOT / target)]
    )
    with pytest.raises(ValueError):
        case.module.main()
