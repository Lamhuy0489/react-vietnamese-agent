"""Real CPU checkpoints verify audit coverage and CPU/native CLI admission."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest
from test_guard_bare_json_probe_v1 import source as prior_source  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def source(prior_source):  # noqa: F811 - pytest resolves the imported parametrized fixture
    return prior_source


@pytest.fixture
def cli():
    spec = importlib.util.spec_from_file_location(
        "bare_cli", ROOT / "scripts/audit_phase5_guard_bare_json_probe_v1.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_actual_cpu_audit_identity_and_no_mutation(cli, source):
    root, condition, _ = source
    before = cli.inventory(root)
    result = cli.audit_probe(root, condition, "1" * 40)
    assert result["valid"] and len(result["tasks"]) == 4
    assert cli.inventory(root) == before
    other = "fenced" if condition == "valid" else "valid"
    with pytest.raises(ValueError, match="condition"):
        cli.audit_probe(root, other, "1" * 40)


def test_missing_task_cannot_report_valid(cli, source, tmp_path):
    root, condition, _ = source
    target = tmp_path / "missing"
    shutil.copytree(root, target)
    (target / "tasks/DOC_A6").rename(target / "retained_DOC_A6")
    with pytest.raises(ValueError, match="four-task"):
        cli.audit_probe(target, condition, "1" * 40)


def test_default_condition_executes_cli_without_launcher_flag(cli, source, tmp_path, monkeypatch):
    root, condition, _ = source
    if condition != "valid":
        return
    out = tmp_path / "audit.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["audit", "--probe", str(root), "--source-commit", "1" * 40, "--output", str(out)],
    )
    cli.main()
    assert json.loads(out.read_text())["valid"]


def test_native_inputs_cannot_fall_through_cpu_audit(cli, tmp_path, monkeypatch):
    probe = tmp_path / "probe"
    probe.mkdir()
    (probe / "identity.json").write_text(json.dumps(dict(backend="hf")))
    out = tmp_path / "audit.json"
    argv = ["audit", "--probe", str(probe), "--source-commit", "1" * 40, "--output", str(out)]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(ValueError, match="snapshot inputs"):
        cli.main()
    assert not out.exists()

    called = []

    def fail(*args):
        called.append(args)
        raise ValueError("native metric hash mismatch")

    pin = ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json"
    monkeypatch.setattr(cli, "native_audit", fail)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            *argv,
            "--snapshot",
            str(pin),
            "--tokenizers",
            str(tmp_path / "tokens"),
            "--publishers",
            str(tmp_path / "publishers"),
        ],
    )
    with pytest.raises(ValueError, match="metric hash"):
        cli.main()
    assert len(called) == 1 and not out.exists()
