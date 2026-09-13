from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.a2_qa import MODEL, REVISION, SyntheticGuardFactory
from react_agent.security_v1.contracts import Effect, Level, configuration
from react_agent.security_v1.final_entitlements import FinalEntitlement, extract_final_entitlement
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v6 import SecurityRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network is forbidden in synthetic entitlement runtime QA")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def source_catalog(
    *, source_id: str = "DOC_001", trust: Trust = Trust.TRUSTED
) -> SourceCatalog:
    action = Action(name="db_query", arguments={"query": "SELECT 3.2 AS gpa"})
    return SourceCatalog(
        bindings=(
            SourceBinding(
                tool=action.name,
                arguments_json=canonical_json(action.arguments),
                label=SourceLabel(
                    source_type=SourceType.DATABASE,
                    source_id=source_id,
                    sensitivity=Sensitivity.CONFIDENTIAL,
                    trust=trust,
                ),
            ),
        )
    )


def run_case(
    tmp_path: Path,
    *,
    instruction: str,
    answer: str = "GPA: 3.2",
    source_id: str = "DOC_001",
    trust: Trust = Trust.TRUSTED,
    entitlement: FinalEntitlement | None = None,
    level: Level = "A6",
) -> SecurityRun:
    action = Action(name="db_query", arguments={"query": "SELECT 3.2 AS gpa"})
    runtime = SecurityRuntime(
        RecordingBackend([action_response(action), final_response(answer)]),
        build_smoke_registry(ROOT / "data/smoke"),
        runtime_config=RuntimeConfig(max_steps=2, max_format_retries_per_step=0),
    )
    catalog = source_catalog(source_id=source_id, trust=trust)
    if level == "A6":
        return runtime.run_instrumented(
            PublicWorkbenchTask(task_id="awb_entitled", instruction=instruction),
            output=tmp_path / "run",
            source_catalog=catalog,
            security_config=configuration(level),
            guard_factory=SyntheticGuardFactory(),
            guard_execution=WarmGuardConfig(MODEL, REVISION, 10),
            entitlement=entitlement,
        )
    if entitlement is not None:
        raise ValueError("final entitlement requires A6")
    return runtime.run_instrumented(
        PublicWorkbenchTask(task_id="awb_entitled", instruction=instruction),
        output=tmp_path / "run",
        source_catalog=catalog,
        security_config=configuration(level),
    )


def metadata(tmp_path: Path) -> dict[str, Any]:
    value = json.loads((tmp_path / "run/run_metadata.json").read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_explicit_trusted_entitlement_releases_private_gpa(tmp_path: Path) -> None:
    instruction = "Trả GPA từ DOC_001 trong câu trả lời"
    run_case(tmp_path, instruction=instruction, entitlement=extract_final_entitlement(instruction))
    result = metadata(tmp_path)
    assert result["runtime_version"] == "security_runtime_v6_entitlement_adapter"
    assert result["final_policy"] == "final_entitlement_release_v1"
    assert result["final_release"]["profile"] == "final_entitlement_release_v1"
    assert result["final_release"]["effect"] == Effect.ALLOW
    assert result["result"]["final_answer"] == "GPA: 3.2"


def test_implicit_or_missing_entitlement_redacts_private_gpa(tmp_path: Path) -> None:
    run_case(tmp_path, instruction="Đọc DOC_001 và tóm tắt")
    result = metadata(tmp_path)
    assert result["final_release"]["effect"] == Effect.REDACT
    assert result["result"]["final_answer"] == "GPA: [REDACTED]"


def test_raw_user_affirmative_clause_is_auto_extracted(tmp_path: Path) -> None:
    run_case(tmp_path, instruction="Trả GPA từ DOC_001 trong câu trả lời")
    result = metadata(tmp_path)
    assert result["final_release"]["effect"] == Effect.ALLOW
    assert result["result"]["final_answer"] == "GPA: 3.2"


@pytest.mark.parametrize(
    "instruction,source_id,trust",
    [
        ("Trả GPA từ DOC_OTHER trong câu trả lời", "DOC_001", Trust.TRUSTED),
        ("Trả GPA từ DOC_001 trong câu trả lời", "DOC_001", Trust.UNTRUSTED),
    ],
)
def test_wrong_source_or_untrusted_origin_cannot_be_entitled(
    tmp_path: Path, instruction: str, source_id: str, trust: Trust
) -> None:
    run_case(tmp_path, instruction=instruction, source_id=source_id, trust=trust)
    result = metadata(tmp_path)
    assert result["final_release"]["effect"] == Effect.REDACT
    assert result["result"]["final_answer"] == "GPA: [REDACTED]"


def test_normalized_only_final_denies(tmp_path: Path) -> None:
    run_case(
        tmp_path,
        instruction="Trả GPA từ DOC_001 trong câu trả lời",
        answer="GPA: 3.\u200b2",
    )
    result = metadata(tmp_path)
    assert result["final_release"]["effect"] == Effect.DENY
    assert result["result"]["final_answer"] == ""


def test_supplied_entitlement_is_hash_bound_to_raw_task(tmp_path: Path) -> None:
    supplied = extract_final_entitlement("Trả GPA từ DOC_OTHER trong câu trả lời")
    with pytest.raises(ValueError, match="bound"):
        run_case(
            tmp_path,
            instruction="Trả GPA từ DOC_001 trong câu trả lời",
            entitlement=supplied,
        )
    assert not (tmp_path / "run").exists()


def test_a0_keeps_public_final_and_does_not_start_guard(tmp_path: Path) -> None:
    run_case(
        tmp_path,
        instruction="Trả lời công khai",
        answer="Nội dung công khai",
        level="A0",
    )
    result = metadata(tmp_path)
    assert result["runtime_version"] == "security_runtime_v6_entitlement_adapter"
    assert result["final_release"] is None
    assert result["result"]["final_answer"] == "Nội dung công khai"
    assert result["guard_execution_attempt_count"] == 0
