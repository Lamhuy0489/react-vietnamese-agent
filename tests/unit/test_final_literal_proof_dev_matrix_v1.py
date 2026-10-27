"""Matrix reproducibility and input integrity, without Test/benchmark reads."""

import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = runpy.run_path(str(ROOT / "scripts/audit_phase5_final_literal_proof_dev_v1.py"))


def test_three_arm_matrix_and_unscored_limits():
    first = MODULE["audit"]()
    assert first["input_sha256"] == (
        "13fd8a775a45dcf7d4c7b84cb55fed932d0354f5bdd14d03ba806883ac534603"
    )
    assert first == MODULE["audit"]()
    assert first["cpu_adapter_admitted"] is True
    assert first["native_model_runs"] == 0
    assert first["held_out_test_loaded"] is False
    assert first["public_field_runtime_admitted"] is False
    for group, expected in MODULE["COUNTS"].items():
        result = first["summary"][group]["proof"]
        assert result["desired_pass"] == (None if group == "unsupported" else expected)
        assert result["scored"] == (0 if group == "unsupported" else expected)
    assert first["summary"]["leak"]["v3"]["desired_pass"] == 0
    assert first["summary"]["user_collision"]["v4"]["desired_pass"] == 0
    assert first["summary"]["public_collision"]["v4"]["desired_pass"] == 0
    for arm in ("v3", "v4"):
        assert first["summary"]["invalid_proof"][arm]["scored"] == 0
        assert first["summary"]["invalid_proof"][arm]["desired_pass"] is None


@pytest.mark.parametrize("fault", ["duplicate", "target", "scope", "group", "public"])
def test_malformed_matrix_rejected(tmp_path, fault):
    payload = json.loads(MODULE["CASES"].read_text())
    if fault == "duplicate":
        payload["cases"][0]["id"] = payload["cases"][1]["id"]
    elif fault == "target":
        payload["cases"][0]["private"] = "No protected target here."
    elif fault == "scope":
        payload["scope"] = "held_out"
    elif fault == "group":
        payload["cases"][0]["group"] = "leak"
    else:
        payload["cases"][6]["public"] = {"room_code": "DIFFERENT1234"}
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        MODULE["load_cases"](path)
