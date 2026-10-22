"""Exercise runner aggregation without workers, guarding the duplicate-key bug."""

import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("failed", [False, True])
def test_runner_writes_complete_receipt_including_failed_controls(tmp_path, monkeypatch, failed):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    module = importlib.import_module("run_phase5_doc_read_final_cpu_v1")
    module = importlib.reload(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    output = tmp_path / "build/evaluation/run"

    class FakeProcess:
        stdout = "a" * 40

    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: FakeProcess())
    monkeypatch.setattr(module.shutil, "which", lambda _: "/test/git")
    original_read = Path.read_bytes

    def source_bytes(path):
        if path.is_relative_to(tmp_path) and not path.is_relative_to(tmp_path / "build"):
            return b"synthetic source bytes"
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", source_bytes)

    def fake_control(root, destination, case):
        assert (output / "declaration.json").is_file()
        destination.mkdir()
        success = not (failed and case == module.CASES[0])
        row = dict(case=case, checks=dict(candidate_desired=success), expectation_met=success,
                   arms={arm: dict(desired_pass=success) for arm in ("baseline", "candidate")})
        (destination / "receipt.json").write_text(json.dumps(row))
        return row

    monkeypatch.setattr(module, "run_control", fake_control)
    monkeypatch.setattr("sys.argv", ["runner", "--output", str(output)])
    if failed:
        with pytest.raises(SystemExit, match="matrix failed"):
            module.main()
    else:
        module.main()
    receipt = json.loads((output / "receipt.json").read_text())
    assert receipt["protocol"] == "doc_read_final_cpu_matrix_receipt_v1"
    assert receipt["case_count"] == 12 and receipt["runtime_count"] == 24
    assert receipt["all_gates_passed"] is not failed
    assert len(receipt["case_receipt_sha256"]) == 12
    assert receipt["source_commit"] is None
