"""Offline deployment guards: no submission on zero quota or changed package."""
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def deploy(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("deploy_structured_pair_v3")


@pytest.fixture
def prepared(tmp_path, deploy, monkeypatch):
    commit = "a" * 40
    roles = {}
    for role, account in deploy.ACCOUNTS.items():
        folder = tmp_path / role
        folder.mkdir()
        (folder / "kernel-metadata.json").write_text(json.dumps({"is_private": True}))
        roles[role] = {"kernel": account + "/synthetic", "cfg": {"model_source": "synthetic"},
                       "files": {
            "kernel-metadata.json": deploy.digest(folder / "kernel-metadata.json")}}
    (tmp_path / "prepared.json").write_text(json.dumps({"source_commit": commit, "roles": roles}))
    qa = tmp_path / "preflight_v3"
    qa.mkdir()
    (qa / "receipt.json").write_text(json.dumps({
        "prepared_sha256": deploy.digest(tmp_path / "prepared.json"),
        "launcher_sha256": deploy.digest(ROOT / "scripts/launch_structured_pair_v3.py"),
        "profile": deploy.PROFILE, "roles": [{}, {}, {}, {}]}))
    monkeypatch.setattr(deploy, "_check_source_commit", lambda c: None)
    monkeypatch.setattr(deploy, "verify_model_access", lambda role, source: None)
    monkeypatch.setattr(deploy, "git", lambda *args: commit + "\trefs/heads/synthetic")
    return tmp_path


def test_zero_quota_blocks_all_submissions(prepared, deploy, monkeypatch):
    calls = []
    def cli(role, args):
        calls.append((role, args))
        return SimpleNamespace(returncode=0, stdout="resource,remaining\nGPU,0.00h\n")
    monkeypatch.setattr(deploy, "kaggle", cli)
    with pytest.raises(ValueError, match="quota exhausted"):
        deploy.push(prepared)
    assert all(args[0] == "quota" for _, args in calls)
    assert not list(prepared.glob("*_submission*.json"))


def test_changed_package_stops_before_network(prepared, deploy, monkeypatch):
    (prepared / "agent/extra.py").write_text("changed")
    monkeypatch.setattr(deploy, "kaggle", lambda *a: pytest.fail("network after tamper"))
    with pytest.raises(ValueError, match="hash mismatch"):
        deploy.push(prepared)


def test_previous_attempt_never_submits_twice(prepared, deploy, monkeypatch):
    (prepared / "agent_submission_started.json").write_text("{}")
    monkeypatch.setattr(deploy, "kaggle", lambda *a: pytest.fail("duplicate submit"))
    with pytest.raises(ValueError, match="already attempted"):
        deploy.push(prepared)


@pytest.mark.parametrize("endpoint", ["http://synthetic.trycloudflare.com/v1",
    "https://attacker.invalid/v1", "https://synthetic.trycloudflare.com/v1?key=x"])
def test_discovery_rejects_unapproved_destinations(deploy, endpoint):
    with pytest.raises(ValueError, match="discovery identity"):
        deploy.validate_connection({"endpoint": endpoint, "api_key": "x" * 43,
            "session_id": "s", "profile": deploy.PROFILE}, {"session_id": "s"})
