from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import ArtifactType, Sensitivity, Trust
from react_agent.foundation.runtime_hooks import derive
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.security_v1.a2_qa import MODEL, REVISION, SyntheticGuard, SyntheticGuardFactory
from react_agent.security_v1.a6_policy import A6Policy, admit, final_bound
from react_agent.security_v1.a6_qa import cases, parity_case, run_case
from react_agent.security_v1.contracts import Effect, configuration
from react_agent.security_v1.guard import ModelGuard
from react_agent.security_v1.process_guard import ProcessGuardConfig
from react_agent.security_v1.runtime_v4 import SecurityRuntime
from react_agent.security_v1.value_gates_qa import action_artifact, external_action, fixture
from react_agent.security_v1.value_origin import ValueOriginIndex
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("network is forbidden in synthetic runtime QA")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.mark.parametrize("case", cases(), ids=lambda c: c.name)
def test_runtime_matrix(case, tmp_path):
    assert run_case(ROOT, tmp_path, case)["valid"]


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A3", "A4", "A5"])
@pytest.mark.parametrize("task_index", [0, 10])
def test_prior_levels_exact_parity(level, task_index, tmp_path):
    assert parity_case(ROOT, tmp_path, level, task_index)["valid"]


@pytest.mark.parametrize("sensitivity", list(Sensitivity))
@pytest.mark.parametrize("trust", list(Trust))
@pytest.mark.parametrize("authorized", [False, True])
@pytest.mark.parametrize("webhook", [False, True])
def test_composed_host_gate(sensitivity, trust, authorized, webhook):
    store, index, user, _ = fixture(
        sensitivity=sensitivity, trust=trust, authorized=authorized, webhook=webhook
    )
    policy = A6Policy(
        configuration("A6"),
        str(store.get(user).content()),
        ModelGuard(SyntheticGuard(SyntheticGuardFactory())),
    )
    action = external_action(webhook)
    result = policy.pre_bound(
        action,
        action_artifact(store, action),
        user,
        index,
        build_smoke_registry(ROOT / "data/smoke"),
    )
    assert (result.effect == Effect.ALLOW) == (authorized and sensitivity == Sensitivity.PUBLIC)
    with pytest.raises(ValueError, match="pre_bound"):
        policy.pre(action)


@pytest.mark.parametrize("missing", ["user", "protected", "unexposed"])
def test_final_source_coverage_fail_closed(missing):
    store, _, user, source = fixture(unrelated_secret=True)
    index = ValueOriginIndex(store)
    roots = [a for a in store.all() if not a.parents]
    for a in roots:
        if (missing == "user" and a.artifact_id == user) or (
            missing == "protected" and a.sensitivity == Sensitivity.CONFIDENTIAL
        ):
            continue
        index.add_artifact(a.artifact_id, observed_step=1)
    parents = tuple(
        a.artifact_id for a in roots if not (missing == "unexposed" and a.artifact_id == source)
    )
    proposed = derive(
        store, "Public proposed answer", kind=ArtifactType.FINAL_RESPONSE, parents=parents, step=2
    )
    release = final_bound(index, proposed.artifact_id, user)
    assert release.effect == Effect.DENY
    assert store.get(release.released_artifact_id).content() == ""
    assert store.get(proposed.artifact_id).content() == "Public proposed answer"
    assert store.get(release.released_artifact_id).sensitivity == proposed.sensitivity


@pytest.mark.parametrize("mode", ["final", "parse", "model", "max_steps"])
def test_terminal_paths_and_fresh_state(mode, tmp_path):
    responses = {
        "final": [final_response("Câu trả lời công khai")],
        "parse": ["invalid"],
        "model": [],
        "max_steps": [action_response(external_action())],
    }[mode]
    run = SecurityRuntime(
        RecordingBackend(responses),
        build_smoke_registry(ROOT / "data/smoke"),
        runtime_config=RuntimeConfig(max_steps=1, max_format_retries_per_step=0),
    )
    task = PublicWorkbenchTask(task_id="awb_terminal", instruction="Chỉ trả lời.")
    result = run.run_instrumented(
        task,
        output=tmp_path / "run",
        security_config=configuration("A6"),
        guard_factory=SyntheticGuardFactory(),
        guard_execution=ProcessGuardConfig(MODEL, REVISION, 10),
    )
    assert (
        result.result.status
        == {
            "final": "completed",
            "parse": "parse_failure",
            "model": "model_error",
            "max_steps": "max_steps",
        }[mode]
    )
    meta = json.loads((tmp_path / "run/run_metadata.json").read_text())
    assert bool(meta["final_release"]) == (mode == "final")
    assert len(json.loads((tmp_path / "run/value_index.json").read_text())["source_sha256"]) == 1
    if mode == "final":
        assert (tmp_path / "run/trace_guard.jsonl").read_text() == ""
        release = meta["final_release"]
        assert release["proposed_artifact_id"] != release["released_artifact_id"]
    with pytest.raises(ValueError, match="fresh"):
        run.run_instrumented(
            task,
            output=tmp_path / "run",
            security_config=configuration("A6"),
            guard_factory=SyntheticGuardFactory(),
            guard_execution=ProcessGuardConfig(MODEL, REVISION, 10),
        )


def test_a6_requires_guard_and_no_legacy_bypass(tmp_path):
    runtime = SecurityRuntime(RecordingBackend([]), build_smoke_registry(ROOT / "data/smoke"))
    task = PublicWorkbenchTask(task_id="awb_guard", instruction="Chỉ đọc.")
    with pytest.raises(ValueError, match="explicit guard"):
        runtime.run_instrumented(task, output=tmp_path / "run", security_config=configuration("A6"))
    assert not (tmp_path / "run").exists()
    with pytest.raises(ValueError, match="no legacy bypass"):
        runtime.run(task)


@pytest.mark.parametrize("risk", ["SUSPICIOUS", "MALICIOUS", "SAFE"])
def test_current_guard_veto_survives_public_origin(risk):
    store, index, user, _ = fixture(unrelated_secret=True)
    policy = A6Policy(
        configuration("A6"),
        str(store.get(user).content()),
        ModelGuard(SyntheticGuard(SyntheticGuardFactory(pre_risk=risk))),
    )
    action = external_action()
    result = policy.pre_bound(
        action,
        action_artifact(store, action),
        user,
        index,
        build_smoke_registry(ROOT / "data/smoke"),
    )
    assert (result.effect == Effect.ALLOW) == (risk == "SAFE")


def test_incomplete_index_final_denies():
    store, index, user, source = fixture()
    proposed = derive(
        store, "Public answer", kind=ArtifactType.FINAL_RESPONSE, parents=(user, source), step=2
    )
    assert admit(index, proposed.artifact_id, 2) == "OriginError"
    assert not index.complete
    release = final_bound(index, proposed.artifact_id, user)
    assert release.effect == Effect.DENY
    assert store.get(release.released_artifact_id).content() == ""


def test_mismatched_host_action_aborts_before_guard():
    store, index, user, _ = fixture()
    policy = A6Policy(
        configuration("A6"),
        str(store.get(user).content()),
        ModelGuard(SyntheticGuard(SyntheticGuardFactory())),
    )
    proposal = action_artifact(store, external_action())
    with pytest.raises(ValueError, match="differs"):
        policy.pre_bound(
            external_action(True), proposal, user, index, build_smoke_registry(ROOT / "data/smoke")
        )
    assert policy.guard_records == []


def test_repeated_runtime_has_fresh_index(tmp_path):
    runtime = SecurityRuntime(
        RecordingBackend([final_response(), final_response()]),
        build_smoke_registry(ROOT / "data/smoke"),
    )
    task = PublicWorkbenchTask(task_id="awb_repeat", instruction="Chỉ trả lời.")
    identities = []
    for i in range(2):
        output = tmp_path / str(i)
        runtime.run_instrumented(
            task,
            output=output,
            security_config=configuration("A6"),
            guard_factory=SyntheticGuardFactory(),
            guard_execution=ProcessGuardConfig(MODEL, REVISION, 10),
        )
        index = json.loads((output / "value_index.json").read_text())
        identities.append(index["run_id"])
        assert len(index["source_sha256"]) == 1
    assert identities[0] != identities[1]
