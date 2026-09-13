"""Synthetic native-shaped sidecars; checkpoint boundary mocked explicitly, no GPU."""

import copy
import json
import shutil
from dataclasses import asdict

import pytest
from test_ordinary_pair_audit_v1 import native as native  # noqa: F401
from test_ordinary_pair_audit_v1 import sample as sample  # noqa: F401
from test_ordinary_pair_audit_v1 import template as template  # noqa: F401
from test_ordinary_tokenizer_audit_v1 import tokenizers as tokenizers  # noqa: F401

from react_agent.foundation.normalization import text_hash
from react_agent.llm.ordinary_pair_probe_v1 import native_config
from react_agent.llm.security_runtime_probe_v1 import GENERATION, LEVELS, TASK
from react_agent.security_v1.contracts import configuration
from react_agent.validation import security_runtime_probe_audit_v1 as impl


@pytest.fixture
def inputs(native, tokenizers, tmp_path, monkeypatch):
    root = tmp_path / "seven"
    root.mkdir()
    security = {level: configuration(level).model_dump(mode="json") for level in LEVELS}
    identity = dict(
        backend="hf",
        source_commit=native["commit"],
        snapshot_sha256=native["pin"].sha256,
        pair_config=asdict(native_config()),
        security=security,
        generation=GENERATION.model_dump(),
        task_sha256=text_hash(TASK.instruction),
    )
    (root / "identity.json").write_text(json.dumps(identity))
    closed = json.loads((native["probe"] / "closed.json").read_text())
    for level in LEVELS:
        task = root / "tasks" / level
        (task / "execution").mkdir(parents=True)
        (task / "native").mkdir()
        workers = copy.deepcopy(closed["workers"])
        if level in {"A0", "A1"}:
            workers.pop("guard")
        receipt = dict(
            snapshot=dict(workers=workers),
            security=security[level],
            task_sha256=identity["task_sha256"],
            generation=identity["generation"],
        )
        (task / "execution/pair_runtime.json").write_text(json.dumps(receipt))
        shutil.copy2(native["probe"] / "baseline.json", task / "baseline.json")
        for role in workers:
            shutil.copy2(
                native["probe"] / f"{role}_hf_metrics.jsonl",
                task / "native" / f"{role}_hf_metrics.jsonl",
            )
            for kind in ("policy", "attention"):
                shutil.copytree(native[kind] / role, task / kind / role)
    monkeypatch.setattr(impl, "checkpoint", lambda root: dict(terminal="completed", recovered=True))
    return dict(
        probe=root,
        tokenizers=tokenizers,
        publishers=native["publishers"],
        pin=native["pin"],
        commit=native["commit"],
    )


def test_join_is_repeatable_and_not_execution_claim(inputs):
    first = impl.audit(**inputs)
    assert first == impl.audit(**inputs)
    assert first["artifact_integrity_valid"] and not first["source_authenticated"]
    assert not first["guard_quality_validated"] and not first["phase5_accepted"]
    assert len(first["levels"]) == 7
    assert all(
        role["policy_attention_verified"]
        for level in first["levels"]
        for role in level["roles"].values()
    )


@pytest.mark.parametrize("fault", ["source", "tokenizer", "policy", "time", "guard_in_a0"])
def test_reject_mutated_sidecars(inputs, fault):
    if fault == "source":
        inputs["commit"] = "b" * 40
    elif fault == "tokenizer":
        (inputs["tokenizers"] / "agent_tokenizer_config.json").write_text("{}")
    elif fault == "policy":
        (inputs["probe"] / "tasks/A0/policy/agent/request_000001/completed.json").write_text("{}")
    elif fault == "guard_in_a0":
        (inputs["probe"] / "tasks/A0/native/guard_hf_metrics.jsonl").write_text("{}")
    else:
        path = inputs["probe"] / "tasks/A0/execution/pair_runtime.json"
        receipt = json.loads(path.read_text())
        receipt["snapshot"]["workers"]["agent"]["attempts"][1]["generation_seconds"] = 0
        path.write_text(json.dumps(receipt))
    with pytest.raises((ValueError, KeyError)):
        impl.audit(**inputs)
