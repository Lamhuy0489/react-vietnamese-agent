"""Validate diagnostic accounting without treating negative findings as test errors."""

import importlib
from pathlib import Path

import pytest


@pytest.fixture
def probe(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("run_phase5_direction_probe_v1")


def test_predeclared_denominators_and_semantics(probe):
    cases = probe.cases()
    assert len(cases) == len({c.name for c in cases}) == 12
    assert sum(c.benign for c in cases) == 8
    for case in cases:
        assert probe.PUBLIC_ID in case.instruction and probe.PRIVATE_ID in case.instruction
        probe.PublicWorkbenchTask(task_id="awb_direction" + case.name.replace("_", "")
                                  .replace("64", "sixtyfour"), instruction=case.instruction)
        if case.benign:
            assert case.answer == case.public
        else:
            assert probe.disclosed(case.answer, case.forbidden)


@pytest.mark.parametrize("fault", [None, "lost_utility", "leak", "parity", "missing", "duplicate"])
def test_no_go_and_integrity_are_separate(probe, fault):
    rows = [dict(case=c.name, benign=c.benign, parity=True, arms={
        arm: dict(exact_utility=True, disclosed=False, terminal="completed", elapsed_cpu_seconds=1.)
        for arm in ("baseline", "candidate")
    }) for c in probe.cases()]
    if fault == "lost_utility":
        rows[1]["arms"]["candidate"]["exact_utility"] = False
    elif fault == "leak":
        rows[-1]["arms"]["candidate"]["disclosed"] = True
    elif fault == "parity":
        rows[0]["parity"] = False
    elif fault == "missing":
        rows.pop()
    elif fault == "duplicate":
        rows[-1] = rows[0]
    if fault in ("parity", "missing", "duplicate"):
        with pytest.raises(ValueError):
            probe.summarize(rows)
    else:
        result = probe.summarize(rows)
        assert result["phase5_accepted"] is False
        assert result["recommendation"] == ("eligible_for_broader_validation" if fault is None
                                            else "do_not_promote_as_general_remedy")


def test_declared_disclosure_check_is_not_generic_semantic_safety(probe):
    assert not probe.disclosed("Không có mã riêng.", probe.OTHER)
    assert probe.disclosed(probe.OTHER, probe.OTHER)
    # Deliberately outside this check's exact/base64/zero-width coverage.
    assert not probe.disclosed(" ".join(probe.OTHER), probe.OTHER)


def test_actual_cpu_arm_serializes_inputs_and_audits(probe, tmp_path):
    approved = probe.DocReadApproval(source_id=probe.PUBLIC_ID, review_ref="synthetic-unit")
    row = probe.run_arm(tmp_path / "run", probe.cases()[0], "candidate", approved)
    assert row["terminal"] == "completed" and row["audit_valid"] is True
    assert row["exact_utility"] is True and len(row["inputs_sha256"]) == 64
