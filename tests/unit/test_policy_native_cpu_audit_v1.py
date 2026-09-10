"""Synthetic native-shaped records; only the outer release audit authenticates source."""

import copy
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    entry = importlib.import_module("run_phase5_policy_native_compat")
    auditor = importlib.import_module("audit_phase5_policy_native_cpu")
    raw = tmp_path / "synthetic"
    result = entry.run(raw, "stub", "a" * 40)
    result.update(backend="native", native_library_verified=True)
    for row in result["cases"]:
        row["identity"] = copy.deepcopy(auditor.NATIVE)
    (raw / "summary.json").write_text(json.dumps(result))
    return auditor, raw


def test_consistent_synthetic_harness(sample: Any) -> None:
    auditor, raw = sample
    result = auditor.audit_harness(raw, "a" * 40)
    assert result == auditor.audit_harness(raw, "a" * 40)
    assert len(result["raw_sha256"]) == 21
    assert result["summary"]["model_generate_calls"] == 0
    assert not result["summary"]["phase5_accepted"]


@pytest.mark.parametrize(
    "case",
    [
        "pid",
        "source",
        "torch",
        "weights",
        "model_calls",
        "gpu",
        "synthetic_label",
        "error",
        "restore",
        "publisher",
        "missing",
        "extra",
    ],
)
def test_corruption_rejected(sample: Any, case: str) -> None:
    auditor, raw = sample
    path = raw / "summary.json"
    if case in ("pid", "publisher"):
        path = raw / "agent_none/policy/entered.json"
    elif case in ("restore", "error"):
        path = raw / f"guard_error/policy/{'restored' if case == 'restore' else 'error'}.json"
    record = json.loads(path.read_text())
    if case == "pid":
        record["pid"] = 0
    elif case == "source":
        record["source_commit"] = "b" * 40
    elif case == "torch":
        record["cases"][0]["identity"]["torch"] = "2.2.2"
    elif case == "weights":
        record["weights_loaded"] = 1
    elif case == "model_calls":
        record["model_generate_calls"] = 1
    elif case == "gpu":
        record["gpu_used"] = True
    elif case == "synthetic_label":
        record["cases"][0]["policy_receipt_generation_count_is_synthetic"] = False
    elif case == "publisher":
        record["publisher"]["repetition_penalty"] = 1.0
    elif case == "restore":
        record["methods_restored"] = False
    elif case == "error":
        record["error_class"] = "TypeError"
    if case == "missing":
        path.unlink()
    elif case == "extra":
        (raw / "extra.json").write_text("{}")
    else:
        path.write_text(json.dumps(record))
    with pytest.raises((ValueError, FileNotFoundError)):
        auditor.audit_harness(raw, "a" * 40)


def test_audit_cli_refuses_output_under_raw(sample: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    auditor, raw = sample
    monkeypatch.setattr(
        "sys.argv",
        [
            "audit",
            "--raw",
            str(raw),
            "--remote",
            "unused",
            "--preflight",
            "unused",
            "--output",
            str(raw / "audit.json"),
        ],
    )
    with pytest.raises(ValueError, match="outside raw"):
        auditor.main()
