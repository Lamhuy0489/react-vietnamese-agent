from __future__ import annotations

import copy
import json
import shutil
import smtplib
import socket
from pathlib import Path

import pytest
from pydantic import ValidationError

from react_agent.authoring.admission_review import (
    AdmissionRegister,
    evidence_checks,
    load_bound_previous,
    validate_admission,
    verify_hash_map,
)
from react_agent.authoring.mechanism_revision import validate_revision, verify_revision
from react_agent.authoring.workbench_qa import file_hashes

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / "data/adversarial/mechanism_batch_v1"
REVISION = ROOT / "data/adversarial/mechanism_batch_v2"
PILOT = ROOT / "data/adversarial/candidates_v2_2"
CLEAN = ROOT / "data/clean/v1_1/environment"
REGISTER = ROOT / "data/adversarial/admission_review_v1/reviews.json"


@pytest.fixture(scope="module")
def completed(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict, dict, AdmissionRegister]:
    output = tmp_path_factory.mktemp("admission") / "runs"
    register = AdmissionRegister.model_validate_json(REGISTER.read_text())
    previous = load_bound_previous(ROOT, register)

    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("network forbidden during authoring QA")

    with pytest.MonkeyPatch.context() as patch:
        for name in ("socket", "create_connection", "getaddrinfo"):
            patch.setattr(socket, name, deny)
        patch.setattr(smtplib, "SMTP", deny)
        report = verify_revision(PARENT, REVISION, PILOT, CLEAN, output)
    return output, report, previous, register


def test_versioned_allowlist_and_all_admission_evidence(completed: tuple) -> None:
    _, revision, previous, register = completed
    result = validate_admission(ROOT, register, evidence_checks(previous, revision))
    assert result["working_candidates"] == 48 and result["retained_representatives"] == 46
    assert result["remaining_to_target"] == 24 and result["review_unit_count"] == 15
    assert result["standard_reference_paths"] == 192
    assert result["pairs_examined"] == 1128
    assert result["merges"] == {"awb_hexcode": "awb_encoded", "awb_rowretry": "awb_rowdirect"}
    assert not result["phase3_accepted"] and not result["independent_human_review"]
    assert revision["fresh_replay_runs"] == 38
    assert len(revision["standard"]["checks"]) == 32


@pytest.mark.parametrize("task", ["awb_quantity", "awb_order"])
def test_real_counterexamples_close_old_false_safe_scores(completed: tuple, task: str) -> None:
    _, revision, _, _ = completed
    rows = {c["fixture"]: c for c in revision["counterexamples"] if c["task_id"] == task}
    assert all(r["old_score"]["safe_utility"] for r in rows.values())
    assert rows["safe"]["revised_score"]["safe_utility"]
    for fixture in ("violating_success", "violating_failure"):
        assert not rows[fixture]["revised_score"]["safe_utility"]
        assert rows[fixture]["revised_score"]["utility"]
        assert rows[fixture]["revised_score"]["proposed_violations"] == 1
    assert rows["violating_success"]["revised_score"]["executed_violations"] == 1
    assert rows["violating_failure"]["revised_score"]["executed_violations"] == 0
    assert rows["violating_failure"]["injected_failures"] == 1


@pytest.mark.parametrize("mutation", ["task", "overlay", "quota", "extra_rule", "inventory"])
def test_revision_rejects_changes_outside_allowlist(tmp_path: Path, mutation: str) -> None:
    revision = tmp_path / "revision"
    shutil.copytree(REVISION, revision)
    if mutation == "inventory":
        (revision / "extra.txt").write_text("unexpected")
    else:
        relative = {"task": "public/tasks.json", "overlay": "overlays/scenarios.json"}.get(
            mutation, "private/rules.json"
        )
        path = revision / relative
        rows = json.loads(path.read_text())
        if mutation == "task":
            rows[0]["instruction"] += " changed"
        elif mutation == "overlay":
            rows[0]["attack_text"] += " changed"
        elif mutation == "quota":
            next(r for r in rows if r["task_id"] == "awb_quantity")["action_rules"][0][
                "max_successful_calls"
            ] = 2
        else:
            next(r for r in rows if r["task_id"] == "awb_query")["action_rules"][0]["equals"][
                "top_k"
            ] = 1
        path.write_text(json.dumps(rows, ensure_ascii=False))
    with pytest.raises(ValueError):
        validate_revision(PARENT, revision)


@pytest.mark.parametrize(
    "mutation",
    ["duplicate", "missing", "no_violation", "unsafe", "unassessed", "trace_hash", "unknown_task"],
)
def test_admission_requires_all_unique_valid_fixture_outcomes(
    completed: tuple, mutation: str
) -> None:
    _, revision, previous, register = completed
    checks = copy.deepcopy(evidence_checks(previous, revision))
    if mutation == "duplicate":
        checks.append(checks[0])
    elif mutation == "missing":
        checks.pop()
    elif mutation == "no_violation":
        scored = next(c for c in checks if c["fixture"] == "negative")["score"]
        scored["executed_violations"], scored["final_leaked_artifacts"] = 0, []
    elif mutation == "unsafe":
        next(c for c in checks if c["fixture"] == "safe")["score"]["safe_utility"] = False
    elif mutation == "unassessed":
        checks[0]["score"]["unassessed_actions"] = 1
    elif mutation == "trace_hash":
        checks[0]["trace_sha256"] = "g" * 64
    else:
        checks[0]["task_id"] = "awb_unknown"
    with pytest.raises(ValueError):
        validate_admission(ROOT, register, checks)


@pytest.mark.parametrize(
    "mutation",
    ["duplicate_review", "family", "batch", "group", "cycle", "cross_group", "stale_hash"],
)
def test_review_identity_merge_and_hash_integrity(completed: tuple, mutation: str) -> None:
    _, revision, previous, original = completed
    register = original.model_copy(deep=True)
    entry = next(e for e in register.entries if e.task_id == "awb_hexcode")
    if mutation == "duplicate_review":
        register.entries[-1] = register.entries[0]
    elif mutation == "family":
        entry.family_id = "CAND_UNKNOWN"
    elif mutation == "batch":
        entry.batch = "flow_batch_v1"
    elif mutation == "group":
        entry.template_group = "invented_independent_group"
    elif mutation == "cycle":
        target = next(e for e in register.entries if e.task_id == "awb_encoded")
        target.decision, target.representative = "merge", "awb_hexcode"
    elif mutation == "cross_group":
        entry.representative = "awb_cache"
    else:
        register.input_sha256["mechanism_batch_v2"]["private/rules.json"] = "0" * 64
    with pytest.raises(ValueError):
        validate_admission(ROOT, register, evidence_checks(previous, revision))


def test_register_requires_five_batches_and_48_decisions() -> None:
    data = json.loads(REGISTER.read_text())
    data["input_sha256"].pop("flow_batch_v1")
    with pytest.raises(ValidationError, match="five batches"):
        AdmissionRegister.model_validate(data)
    data = json.loads(REGISTER.read_text())
    data["entries"].pop()
    with pytest.raises(ValidationError, match="48 entries"):
        AdmissionRegister.model_validate(data)


def test_bound_previous_receipt_cannot_be_silently_replaced(completed: tuple) -> None:
    _, _, _, original = completed
    register = original.model_copy(deep=True)
    register.previous_receipt_sha256 = "0" * 64
    with pytest.raises(ValueError, match="stale"):
        load_bound_previous(ROOT, register)


def test_hash_map_rejects_missing_and_escaping_paths(tmp_path: Path) -> None:
    for hashes in ({}, {"missing": "0" * 64}, {"../escape": "0" * 64}):
        with pytest.raises(ValueError):
            verify_hash_map(tmp_path, hashes)


def test_inputs_and_counterexample_traces_are_reproducible(
    completed: tuple, tmp_path: Path
) -> None:
    output, revision, _, _ = completed
    before = [file_hashes(p) for p in (PARENT, REVISION, PILOT, CLEAN)]
    with pytest.raises(ValueError, match="fresh"):
        verify_revision(PARENT, REVISION, PILOT, CLEAN, output)
    again = verify_revision(PARENT, REVISION, PILOT, CLEAN, tmp_path / "repeat")
    assert before == [file_hashes(p) for p in (PARENT, REVISION, PILOT, CLEAN)]
    assert all(
        a["observable_sha256"] == b["observable_sha256"]
        and a["old_score"] == b["old_score"]
        and a["revised_score"] == b["revised_score"]
        for a, b in zip(revision["counterexamples"], again["counterexamples"], strict=True)
    )
