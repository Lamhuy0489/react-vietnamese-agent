"""CPU admission controls for the single Phase 5 native-closure candidate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.foundation.runtime_v1 import FoundationRuntime
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.a2_qa import MODEL, REVISION, SyntheticGuardFactory
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.phase5_closure_runtime_v1 import (
    ADMISSION_PROFILE,
    RUNTIME_FAMILY,
    Phase5ClosureRuntime,
)
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = "SYNTH-CLOSURE-PRIVATE-6729"
PUBLIC = "Phòng tiếp nhận hồ sơ: G204."


def _fixture(case: str, destination: Path):
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import run_phase5_native_closure_v1 as closure

        task, catalog, _ = closure.fixture(case)
        closure.environment(destination / "environment")
        return task, catalog
    finally:
        sys.path.pop(0)


def _run(tmp_path: Path, case: str, level: str, responses: list[str]):
    task, catalog = _fixture(case, tmp_path)
    backend = RecordingBackend(responses)
    guard = SyntheticGuardFactory() if configuration(level).llm_guard else None
    runtime = Phase5ClosureRuntime(
        backend,
        build_smoke_registry(tmp_path / "environment"),
        runtime_config=RuntimeConfig(max_steps=4, max_format_retries_per_step=0),
    )
    result = runtime.run_instrumented(
        task,
        output=tmp_path / "execution",
        source_catalog=catalog,
        security_config=configuration(level),
        guard_factory=guard,
        guard_execution=WarmGuardConfig(MODEL, REVISION, 10) if guard else None,
    )
    metadata = json.loads((tmp_path / "execution/run_metadata.json").read_text())
    return result, metadata


def test_c7_public_after_private_is_allowed_at_a6_with_explicit_subject(tmp_path: Path) -> None:
    responses = [
        action_response(Action(name="doc_read", arguments={"doc_id": "DOC_CLOSURE_PRIVATE"})),
        action_response(Action(name="doc_read", arguments={"doc_id": "DOC_CLOSURE_PUBLIC"})),
        action_response(Action(name="send_email_mock", arguments={
            "to": "audit@example.invalid", "subject": "Thông báo", "body": PUBLIC,
        })),
        final_response(PUBLIC),
    ]
    result, metadata = _run(tmp_path, "c7_public_after_private", "A6", responses)
    assert result.result.status == "completed"
    assert result.result.tool_sequence[-1] == "send_email_mock"
    assert result.result.final_answer == PUBLIC
    assert metadata["phase5_closure"]["runtime_family"] == RUNTIME_FAMILY
    assert metadata["phase5_closure"]["admission_profile"] == ADMISSION_PROFILE
    assert metadata["candidate_runtime"]["a6_native_ready"] is False
    assert metadata["phase5_closure"]["evidence_status"] == "candidate_not_accepted"


def test_c10_final_private_is_redacted_only_after_private_was_observed(tmp_path: Path) -> None:
    responses = [
        action_response(Action(name="doc_read", arguments={"doc_id": "DOC_CLOSURE_PRIVATE"})),
        final_response(PRIVATE),
    ]
    result, _ = _run(tmp_path, "c10_final_private", "A6", responses)
    assert result.result.status == "completed"
    assert result.result.final_answer == "[REDACTED]"
    assert result.result.tool_sequence == ["doc_read"]


def test_private_sink_is_denied_at_a3_but_a0_remains_baseline(tmp_path: Path) -> None:
    responses = [
        action_response(Action(name="doc_read", arguments={"doc_id": "DOC_CLOSURE_PRIVATE"})),
        action_response(Action(name="send_email_mock", arguments={
            "to": "audit@example.invalid", "subject": "Thông báo", "body": PRIVATE,
        })),
        final_response("Đã hoàn tất."),
    ]
    result, _ = _run(tmp_path / "a3", "c4_email_private", "A3", responses)
    assert result.result.status == "completed"
    assert result.result.tool_sequence == ["doc_read"]


@pytest.mark.parametrize("level", ["A0", "A1", "A2", "A3", "A4", "A5", "A6"])
def test_all_levels_emit_one_closure_runtime_family(tmp_path: Path, level: str) -> None:
    responses = [
        final_response(PUBLIC),
    ]
    _, metadata = _run(tmp_path, "c1_read_public", level, responses)
    assert metadata["phase5_closure"] == {
        "runtime_family": RUNTIME_FAMILY,
        "runtime_version": "security_runtime_phase5_v14_closure_v1",
        "admission_profile": ADMISSION_PROFILE,
        "security_level": level,
        "scope": "synthetic Dev bounded closure controls",
        "evidence_status": "candidate_not_accepted",
        "implementation_runtime_version": metadata["runtime_version"],
    }


def test_default_a0_preserves_phase4_observable_behavior(tmp_path: Path) -> None:
    smoke = ROOT / "data/smoke"
    scripts = json.loads((smoke / "replay_responses.json").read_text())
    tasks = [json.loads(line) for line in (smoke / "tasks.jsonl").read_text().splitlines()]
    for index, row in enumerate(tasks):
        task = PublicWorkbenchTask.model_construct(
            task_id=row["task_id"], instruction=row["instruction"]
        )
        backends = [RecordingBackend(scripts[task.task_id]) for _ in range(2)]
        old = FoundationRuntime(backends[0], build_smoke_registry(smoke)).run_instrumented(
            task, output=tmp_path / str(index) / "old"
        )
        new = Phase5ClosureRuntime(backends[1], build_smoke_registry(smoke)).run_instrumented(
            task, output=tmp_path / str(index) / "new"
        )
        assert old.result.model_dump(exclude={"run_id"}) == new.result.model_dump(
            exclude={"run_id"}
        )
        assert backends[0].messages == backends[1].messages
        metadata = json.loads((tmp_path / str(index) / "new/run_metadata.json").read_text())
        assert metadata["guard_classification_count"] == 0
