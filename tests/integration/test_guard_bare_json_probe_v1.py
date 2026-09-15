"""Candidate uses real spawned CPU workers; never represents model-quality evidence."""

import json
import shutil
from pathlib import Path

import pytest

from react_agent.foundation.normalization import text_hash
from react_agent.llm import guard_observer_probe_v2 as baseline
from react_agent.llm.document_runtime_probe_v1 import inventory
from react_agent.llm.guard_bare_json_probe_v1 import SCHEDULE, checkpoint, fixed_identity, run
from react_agent.llm.model_pair_probe_v1 import SyntheticPairObserver
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, RUNTIME_VERSION
from react_agent.validation.guard_bare_json_audit_v1 import audit_task
from react_agent.validation.pair_runtime_audit_v3 import audit_task as baseline_audit

ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENT = ROOT / "data/clean/v1_1/environment"
COMMIT = "1" * 40


def invoke(output, condition="valid", **kwargs):
    return run(
        output,
        ENVIRONMENT,
        backend="stub",
        commit=COMMIT,
        observer_factory=SyntheticPairObserver,
        condition=condition,
        **kwargs,
    )


@pytest.fixture(scope="module", params=["valid", "trailing_comma", "fenced"])
def source(tmp_path_factory, request):
    root = tmp_path_factory.mktemp("bare_json") / request.param
    before = dict(baseline.__dict__)
    summary = invoke(root, request.param)
    assert all(baseline.__dict__[k] is v for k, v in before.items())
    return root, request.param, summary


def test_full_runtime_prompt_join_and_resume(source):
    root, condition, summary = source
    assert summary["tasks"] == 4
    assert summary["completed"] == (4 if condition == "valid" else 0)
    assert summary["model_errors"] == (0 if condition == "valid" else 4)
    before = inventory(root)
    assert invoke(root, condition, resume=True) == summary
    assert inventory(root) == before
    for key in SCHEDULE:
        folder = root / "tasks" / key
        assert checkpoint(folder)["recovered"]
        metadata = json.loads((folder / "execution/runtime/run_metadata.json").read_text())
        assert metadata["guard_prompt_hash"] == text_hash(PROMPT)
        assert metadata["runtime_version"] == RUNTIME_VERSION
        assert audit_task(folder / "execution")["valid"]
        with pytest.raises(ValueError, match="request binding"):
            baseline_audit(folder / "execution")
        joined = json.loads((folder / "join.json").read_text())
        assert joined["response_records"] == (2 if condition == "valid" else 1)
        assert joined["response_hash_cross_checked"]
        if condition == "fenced":
            assert joined["joined"][0]["diagnostic"]["framing"] == "fenced"


def test_missing_only_resume(source, tmp_path):
    root, condition, summary = source
    target = tmp_path / "partial"
    target.mkdir()
    shutil.copy2(root / "identity.json", target / "identity.json")
    for key in SCHEDULE[:-1]:
        shutil.copytree(root / "tasks" / key, target / "tasks" / key)
    before = inventory(target)
    assert invoke(target, condition, resume=True) == summary
    assert all(inventory(target)[k] == v for k, v in before.items())


@pytest.mark.parametrize("mutation", ["prompt", "witness", "metadata"])
def test_candidate_tamper_rejected_before_any_new_inference(source, tmp_path, mutation):
    root, condition, _ = source
    target = tmp_path / "copy"
    shutil.copytree(root, target)
    if mutation == "prompt":
        path = target / "identity.json"
        data = json.loads(path.read_text())
        data["guard_prompt"]["sha256"] = "0" * 64
        path.write_text(json.dumps(data))
    elif mutation == "witness":
        (target / "tasks/CALC_A2/witness.jsonl").write_text("")
    else:
        folder = target / "tasks/CALC_A2"
        path = folder / "execution/runtime/run_metadata.json"
        data = json.loads(path.read_text())
        data["guard_prompt_hash"] = "0" * 64
        path.write_text(json.dumps(data))
    before = inventory(target)
    with pytest.raises(ValueError):
        invoke(target, condition, resume=True)
    assert inventory(target) == before


def test_only_prompt_and_protocol_change_in_native_identity():
    old = baseline.fixed_identity("hf", "valid")
    candidate = fixed_identity("hf", "valid")
    assert {k for k in old if old[k] != candidate[k]} == {"protocol", "security_runtime_version"}
    assert set(candidate) - set(old) == {"guard_prompt"}
    for condition in ("fenced", "trailing_comma"):
        with pytest.raises(ValueError, match="injection"):
            fixed_identity("hf", condition)
