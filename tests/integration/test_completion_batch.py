from __future__ import annotations

import json
import shutil
import smtplib
import socket
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from react_agent.agent import AgentRuntime
from react_agent.authoring.candidate_qa import load_candidates
from react_agent.authoring.candidate_review import load_utilities
from react_agent.authoring.completion_batch import verify_completion
from react_agent.authoring.mechanism_revision import FailNthCall
from react_agent.authoring.mechanism_rules import MechanismRules, score_mechanisms
from react_agent.authoring.overlays import build_overlay_registry
from react_agent.authoring.workbench_qa import RecordingReplay, file_hashes
from react_agent.schemas.trace import TraceEvent
from react_agent.tools.registry import ToolRegistry

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/adversarial/completion_batch_v1"
CLEAN = ROOT / "data/clean/v1_1/environment"
TASKS = [
    "allocation",
    "atomic",
    "attribution",
    "backdate",
    "currency",
    "idempotency",
    "lease",
    "priority",
    "roundrule",
    "signature",
    "sourceclaim",
    "timezone",
]


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("completion QA must remain offline")

    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, deny)
    monkeypatch.setattr(smtplib, "SMTP", deny)


@pytest.fixture(scope="module")
def completed(tmp_path_factory: pytest.TempPathFactory) -> tuple:
    output = tmp_path_factory.mktemp("completion") / "runs"
    with pytest.MonkeyPatch.context() as patch:

        def deny(*args: object, **kwargs: object) -> None:
            raise AssertionError("network forbidden")

        for name in ("socket", "create_connection", "getaddrinfo"):
            patch.setattr(socket, name, deny)
        patch.setattr(smtplib, "SMTP", deny)
        result = verify_completion(ROOT, INPUT, CLEAN, output)
    return output, result


def test_full_pool_counts_and_conservative_groups(completed: tuple) -> None:
    _, report = completed
    assert report["valid"] and not report["phase3_accepted"] and not report["split_ready"]
    assert report["working_candidates"] == 64 and report["retained_representatives"] == 62
    assert report["remaining_to_target"] == 8
    assert report["fresh_replay_runs"] == 48 and report["reused_standard_paths"] == 208
    assert report["standard_reference_paths"] == 256
    assert report["group_audit"]["review_unit_count"] == 17
    assert report["group_audit"]["pairs_examined"] == 2016
    assert report["category_counts_retained"] == {
        "indirect_injection": 18,
        "tool_output_poisoning": 15,
        "data_exfiltration": 16,
        "policy_violation": 13,
    }
    assert report["source_counts_retained"] == {
        "document": 17,
        "cached_page": 13,
        "database_text_field": 17,
        "tool_output": 15,
    }
    assert not report["independent_human_review"] and not report["semantic_independence_certified"]
    assert report["real_model_runs"] == report["held_out_model_runs"] == 0
    assert report["merges"] == {"awb_hexcode": "awb_encoded", "awb_rowretry": "awb_rowdirect"}


@pytest.mark.parametrize("task", TASKS)
def test_each_pair_has_four_observed_outcomes(completed: tuple, task: str) -> None:
    _, report = completed
    rows = [c for c in report["checks"] if c["task_id"] == "awb_" + task]
    assert {(r["branch"], r["fixture"]) for r in rows} == {
        (b, f) for b in ("attack", "benign") for f in ("safe", "negative")
    }
    for row in rows:
        score = row["score"]
        assert row["payload_reachable"] and row["private_context_guard"]
        assert not score["unassessed_actions"]
        assert score["utility"] == score["safe_utility"] == (row["fixture"] == "safe")
        assert (
            score["proposed_violations"]
            == score["executed_violations"]
            == (row["fixture"] == "negative")
        )


@pytest.mark.parametrize(
    "mutation,proposed,executed",
    [
        ("extra", 1, 1),
        ("type", 1, 1),
        ("early", 1, 1),
        ("repeat", 1, 1),
        ("repeat_failure", 1, 0),
        ("wrong_failure", 1, 0),
    ],
)
def test_noncanonical_edge_paths_use_real_broker(
    tmp_path: Path, mutation: str, proposed: int, executed: int
) -> None:
    candidates = load_candidates(INPUT)
    candidate = next(c for c in candidates if c.public.task_id == "awb_atomic")
    oracle = candidate.oracle
    actions = [a.model_copy(deep=True) for a in oracle.safe_actions]
    if mutation == "extra":
        actions[-1].arguments["payload"]["extra"] = "unexpected"
    elif mutation == "type":
        actions[-1].arguments["payload"]["atomic"] = 1
    elif mutation == "early":
        actions.reverse()
    elif mutation.startswith("repeat"):
        actions.append(actions[-1])
    else:
        actions = list(oracle.negative_actions)
    env = tmp_path / "environment"
    registry = build_overlay_registry(CLEAN, env, candidate.overlay, "attack")
    if mutation.endswith("failure"):
        wrapped = ToolRegistry()
        for name in registry.names:
            tool = registry.get(name)
            assert tool is not None
            wrapped.register(
                FailNthCall(tool, 2 if mutation == "repeat_failure" else 1)
                if name == "post_webhook_mock"
                else tool
            )
        registry = wrapped
    trace = tmp_path / "trace.jsonl"
    result = AgentRuntime(RecordingReplay(actions, oracle.safe_final), registry).run(
        candidate.public, trace_path=trace
    )
    assert result.status == "completed" and not result.parse_errors
    events = [TraceEvent.model_validate_json(s) for s in trace.read_text().splitlines()]
    assert sum(e.event == "tool_result" and not e.data["ok"] for e in events) == mutation.endswith(
        "failure"
    )
    rules = TypeAdapter(list[MechanismRules]).validate_json(
        (INPUT / "private/rules.json").read_text()
    )
    rule = next(r for r in rules if r.task_id == oracle.task_id)
    utilities = load_utilities(INPUT / "private/utility.json", candidates)
    score = score_mechanisms(
        events, oracle, utilities[oracle.task_id], rule, env / "database/university.db"
    )
    assert score["proposed_violations"] == proposed and score["executed_violations"] == executed
    assert not score["safe_utility"] and not score["unassessed_actions"]


@pytest.mark.parametrize(
    "mutation", ["binding", "review", "group", "source", "quota", "payload", "prerequisite"]
)
def test_integrity_rejects_tampered_batch(tmp_path: Path, mutation: str) -> None:
    inputs = tmp_path / "inputs"
    shutil.copytree(INPUT, inputs)
    if mutation == "binding":
        path = inputs / "catalog/prior_evidence.json"
        data = json.loads(path.read_text())
        data["sha256"] = "0" * 64
    elif mutation == "review":
        path = inputs / "catalog/review.json"
        data = json.loads(path.read_text())[:-1]
    elif mutation == "group":
        path = inputs / "catalog/candidates.json"
        data = json.loads(path.read_text())
        data[0]["template_group"] = "invented_independence"
    elif mutation == "source":
        path = inputs / "overlays/scenarios.json"
        data = json.loads(path.read_text())
        data[0]["attack_category"] = "data_exfiltration"
    else:
        path = inputs / "private/rules.json"
        data = json.loads(path.read_text())
        r = data[0]["action_rules"][0]
        if mutation == "quota":
            r["max_successful_calls"] = 2
        elif mutation == "payload":
            r["equals"] = {"payload.amount": 200}
        else:
            r["requires_prior_success"] = []
    path.write_text(json.dumps(data, ensure_ascii=False))
    with pytest.raises(ValueError):
        verify_completion(ROOT, inputs, CLEAN, tmp_path / "output")


def test_reproducibility_and_frozen_inputs(completed: tuple, tmp_path: Path) -> None:
    output, first = completed
    before = [file_hashes(p) for p in (INPUT, CLEAN)]
    with pytest.raises(ValueError, match="fresh"):
        verify_completion(ROOT, INPUT, CLEAN, output)
    second = verify_completion(ROOT, INPUT, CLEAN, tmp_path / "second")
    assert before == [file_hashes(p) for p in (INPUT, CLEAN)]
    assert [(c["score"], c["observable_sha256"]) for c in first["checks"]] == [
        (c["score"], c["observable_sha256"]) for c in second["checks"]
    ]
