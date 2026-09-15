"""Saved-run recovery rejects wrong live identities before any native audit."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def release(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "saved_release", ROOT / "scripts/audit_phase5_bare_json_saved_v1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    return module


def test_launcher_inspection_does_not_execute(release, tmp_path):
    path = tmp_path / "worker.py"
    path.write_text("raise RuntimeError('never execute')\nSOURCE_COMMIT: str = 'fixed'\n")
    assert release.launcher_constants(path) == {"SOURCE_COMMIT": "fixed"}
    path.write_text("SOURCE_COMMIT = 'first'\nSOURCE_COMMIT = 'second'\n")
    with pytest.raises(ValueError, match="duplicate"):
        release.launcher_constants(path)
    path.write_text("SOURCE_COMMIT = input()\n")
    with pytest.raises(ValueError):
        release.launcher_constants(path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("actual_kernel", "wrong/worker"),
        ("kernel_version", 2),
        ("kernel_id", 1),
        ("private", False),
        ("session_status", {"status": "COMPLETE"}),
    ],
)
def test_wrong_terminal_identity_rejected(release, tmp_path, field, value):
    raw, remote = tmp_path / "raw", tmp_path / "remote"
    raw.mkdir()
    remote.mkdir()
    prepath, subpath = tmp_path / release.PREFLIGHT, tmp_path / release.SUBMISSION
    prepath.parent.mkdir(parents=True)
    prepath.write_text("{}")
    sub = dict(
        submission_confirmed=True,
        preflight_sha256=release.digest(prepath),
        actual_kernel=release.HANDLE,
        kernel_version=1,
        kernel_id=134511636,
        private=True,
    )
    subpath.write_text(json.dumps(sub))
    observation = dict(
        **sub, submission_sha256=release.digest(subpath), session_status={"status": "ERROR"}
    )
    observation[field] = value
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(observation))
    with pytest.raises(ValueError):
        release.audit(raw, remote, path)
