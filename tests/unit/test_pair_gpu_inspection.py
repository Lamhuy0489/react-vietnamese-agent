"""Recovery evidence must be complete and valid, never inferred from a summary flag."""

import importlib
import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def inspector(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("inspect_phase5_pair_gpu")


@pytest.fixture
def probe(tmp_path: Path) -> Path:
    memory = [
        {"device": i, "total_bytes": 16 * 1024**3, "free_bytes": 14 * 1024**3} for i in (0, 1)
    ]
    (tmp_path / "baseline.json").write_text(json.dumps({"memory": memory}))
    for i in range(6):
        (tmp_path / f"recovery_{i}.json").write_text(
            json.dumps({"memory": memory, "elapsed_seconds": float(i)})
        )
    return tmp_path


def test_complete_recovery(inspector: Any, probe: Path) -> None:
    result = inspector.recovery_observations(probe)
    assert result["complete"] and result["recovery_pass"]
    assert result["signed_residual_bytes"] == [[0, 0]] * 6


def test_missing_is_not_pass(inspector: Any, tmp_path: Path) -> None:
    assert inspector.recovery_observations(tmp_path) == {"complete": False, "recovery_pass": False}


@pytest.mark.parametrize("mode", ["total", "negative", "devices", "time", "nan", "infinity"])
def test_invalid_sample_rejected(inspector: Any, probe: Path, mode: str) -> None:
    path = probe / "recovery_4.json"
    row = json.loads(path.read_text())
    if mode == "total":
        row["memory"][0]["total_bytes"] += 1
    elif mode == "negative":
        row["memory"][0]["free_bytes"] = -1
    elif mode == "devices":
        row["memory"].reverse()
    else:
        row["elapsed_seconds"] = {"time": 0, "nan": float("nan"), "infinity": float("inf")}[mode]
    path.write_text(json.dumps(row))
    with pytest.raises(ValueError):
        inspector.recovery_observations(probe)


@pytest.mark.parametrize("index,expected", [(0, True), (3, False), (5, False)])
def test_frozen_last_three_tolerance(
    inspector: Any, probe: Path, index: int, expected: bool
) -> None:
    path = probe / f"recovery_{index}.json"
    row = json.loads(path.read_text())
    row["memory"][1]["free_bytes"] -= inspector.TOLERANCE + 1
    path.write_text(json.dumps(row))
    assert inspector.recovery_observations(probe)["recovery_pass"] is expected
