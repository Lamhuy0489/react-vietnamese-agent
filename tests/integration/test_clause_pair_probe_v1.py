"""Actual spawned siblings, candidate identities and read-only corruption audits."""

import json
import shutil
from pathlib import Path

import pytest

from react_agent.llm import clause_pair_probe_v1 as candidate
from react_agent.llm import exit_pair_probe_v1 as previous
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver
from react_agent.validation.clause_pair_audit_v1 import audit_task

ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENT = ROOT / "data/clean/v1_1/environment"


def invoke(output, condition="valid", **kwargs):
    return candidate.run(
        output,
        ENVIRONMENT,
        backend="stub",
        commit="1" * 40,
        observer_factory=SyntheticPairObserver,
        condition=condition,
        **kwargs,
    )


@pytest.fixture(scope="module", params=["valid", "backend_failure"])
def source(request, tmp_path_factory):
    output = tmp_path_factory.mktemp("clause_pair") / request.param
    originals = dict(vars(previous))
    summary = invoke(output, request.param)
    assert all(vars(previous)[key] is value for key, value in originals.items())
    return output, request.param, summary


def test_recorded_runtime_and_resume_keep_actual_outcomes(source):
    output, condition, summary = source
    assert summary["completed"] == (4 if condition == "valid" else 0)
    assert summary["model_errors"] == (0 if condition == "valid" else 4)
    before = inventory(output)
    assert invoke(output, condition, resume=True) == summary
    assert inventory(output) == before
    for key in candidate.SCHEDULE:
        task = output / "tasks" / key
        assert candidate.checkpoint(task)["recovered"]
        metadata = json.loads((task / "execution/runtime/run_metadata.json").read_text())
        assert metadata["runtime_version"] == candidate.RUNTIME_VERSION
        assert metadata["authorization"]["profile"] == candidate.ANCHORS
        if key.endswith("A6"):
            assert metadata["processing_scope_profile"] == candidate.SCOPE
            assert (
                json.loads((task / "execution/runtime/value_index.json").read_text())["profile"]
                == candidate.ORIGIN
            )
        with pytest.raises(ValueError):
            previous.checkpoint(task)


def test_missing_only_resume(source, tmp_path):
    output, condition, summary = source
    resumed = tmp_path / "resume"
    resumed.mkdir()
    shutil.copy2(output / "identity.json", resumed / "identity.json")
    for key in candidate.SCHEDULE[:-1]:
        shutil.copytree(output / "tasks" / key, resumed / "tasks" / key)
    before = inventory(resumed)
    assert invoke(resumed, condition, resume=True) == summary
    after = inventory(resumed)
    assert all(after[key] == value for key, value in before.items())


@pytest.mark.parametrize(
    "fault",
    [
        "runtime",
        "profile",
        "anchors",
        "clause_span",
        "raw_hash",
        "scope",
        "origin",
        "index_hash",
        "admission",
    ],
)
def test_candidate_metadata_corruption_rejected_beyond_checkpoint_hash(source, tmp_path, fault):
    output, _, _ = source
    execution = tmp_path / "execution"
    shutil.copytree(output / "tasks/DOC_A6/execution", execution)
    path = execution / "runtime/run_metadata.json"
    value = json.loads(path.read_text())
    if fault == "runtime":
        value["runtime_version"] = "security_runtime_v12_clause_candidate"
    elif fault == "profile":
        value["clause_pair_profiles"]["origin"] = "typed_value_origin_v2"
    elif fault == "anchors":
        value["authorization"]["anchors"]["emails"] = ["fake@example.test"]
    elif fault == "clause_span":
        value["authorization"]["clauses"][0]["start"] += 1
    elif fault == "raw_hash":
        value["authorization"]["raw_user_sha256"] = "0" * 64
    elif fault == "scope":
        value["processing_scope_profile"] = "old_scope"
    elif fault == "index_hash":
        value["value_index_hash"] = "0" * 64
    elif fault == "origin":
        path = execution / "runtime/value_index.json"
        value = json.loads(path.read_text())
        value["records"][0]["source_sha256"] = "0" * 64
    else:
        path = execution / "runtime/trace_value.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["admission_error"] = "OriginError"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    if fault != "admission":
        path.write_text(json.dumps(value))
    before = inventory(execution)
    with pytest.raises(ValueError):
        audit_task(execution)
    assert inventory(execution) == before


def test_recorded_interpreter_not_current_audit_host(source, monkeypatch):
    output, _, _ = source
    identity = json.loads((output / "identity.json").read_text())
    recorded = identity["exit_observer"]["runtime"]
    monkeypatch.setattr(candidate, "runtime_identity", lambda: {**recorded, "system": "other"})
    assert candidate.checkpoint(output / "tasks/DOC_A6", expected_runtime=recorded)["recovered"]
    with pytest.raises(ValueError):
        candidate.checkpoint(output / "tasks/DOC_A6")


def test_linked_identity_rejected_before_resume(tmp_path):
    output = tmp_path / "resume"
    output.mkdir()
    (output / "identity.json").symlink_to(tmp_path / "absent")
    with pytest.raises(ValueError):
        invoke(output, resume=True)
