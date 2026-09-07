from __future__ import annotations

import json
import shutil
import smtplib
import socket
from pathlib import Path

import pytest

from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
)
from react_agent.foundation.runtime_contracts import (
    ContextBundle,
    ControlState,
    Decision,
    FoundationEvent,
)
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.foundation.runtime_qa import (
    RecordingBackend,
    action_response,
    compare,
    final_response,
)
from react_agent.foundation.runtime_v1 import FoundationRuntime
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.tools.factory import build_smoke_registry

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / "data/smoke"
CALC = action_response(Action(name="calculator", arguments={"expression": "1+1"}))


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("runtime QA must remain offline")

    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, deny)
    monkeypatch.setattr(smtplib, "SMTP", deny)


def task() -> PublicWorkbenchTask:
    return PublicWorkbenchTask(task_id="awb_runtime", instruction="Kiểm tra luồng giả lập.")


def registry(destination: Path):
    shutil.copytree(SMOKE, destination)
    return build_smoke_registry(destination)


@pytest.mark.parametrize("index", range(20))
def test_all_smoke_context_action_result_final_parity(index: int, tmp_path: Path) -> None:
    tasks = [json.loads(s) for s in (SMOKE / "tasks.jsonl").read_text().splitlines()]
    responses = json.loads((SMOKE / "replay_responses.json").read_text())
    row = tasks[index]
    public = PublicWorkbenchTask.model_construct(
        task_id=row["task_id"], instruction=row["instruction"]
    )
    report = compare(public, responses[row["task_id"]], registry, tmp_path / "parity")
    assert report["valid"] and report["status"] == "completed"
    assert report["exact_context_parity"] and report["exact_observable_parity"]


@pytest.mark.parametrize(
    "responses,status,errors",
    [
        ([final_response()], "completed", 0),
        (["not json", final_response()], "completed", 1),
        (["bad", "bad", "bad"], "parse_failure", 3),
        ([], "model_error", 0),
        ([CALC], "model_error", 0),
        ([CALC] * 3, "max_steps", 0),
        (['{"action":{"name":"unknown","arguments":{}}}', final_response()], "completed", 1),
        (['{"action":{"name":"calculator","arguments":{}}}', final_response()], "completed", 1),
        (
            [
                action_response(Action(name="calculator", arguments={"expression": "1/0"})),
                final_response(),
            ],
            "completed",
            0,
        ),
    ],
)
def test_terminal_retry_and_tool_failure_parity(
    responses: list[str], status: str, errors: int, tmp_path: Path
) -> None:
    report = compare(
        task(), responses, registry, tmp_path / "parity", config=RuntimeConfig(max_steps=3)
    )
    assert report["status"] == status and report["parse_errors"] == errors


def test_sensitive_untrusted_context_flows_into_sink_fields_and_final_without_block(
    tmp_path: Path,
) -> None:
    read = Action(name="doc_read", arguments={"doc_id": "DOC_001"})
    catalog = SourceCatalog(
        bindings=(
            SourceBinding(
                tool=read.name,
                arguments_json=canonical_json(read.arguments),
                label=SourceLabel(
                    source_type=SourceType.DOCUMENT,
                    source_id="DOC_001",
                    sensitivity=Sensitivity.CONFIDENTIAL,
                    trust=Trust.TRUSTED,
                ),
            ),
        )
    )
    responses = [
        action_response(read),
        action_response(
            Action(
                name="send_email_mock",
                arguments={
                    "to": "outside@example.test",
                    "subject": "SYNTH",
                    "body": "giữ nguyên\u200b dữ liệu",
                },
            )
        ),
        action_response(
            Action(
                name="post_webhook_mock",
                arguments={
                    "endpoint": "mock://outside/demo",
                    "payload": {"text": "giữ nguyên\u200b"},
                },
            )
        ),
        final_response("giữ nguyên\u200b dữ liệu"),
    ]
    report = compare(
        task(),
        responses,
        registry,
        tmp_path / "parity",
        catalog=catalog,
        audit_profile="security_v1",
    )
    assert report["status"] == "completed" and report["hook_counts"] == {
        "pre": 3,
        "post": 3,
        "final": 1,
    }
    directory = tmp_path / "parity/foundation"
    metadata = json.loads((directory / "run_metadata.json").read_text())
    store = ArtifactStore.deserialize(
        metadata["run_id"], (directory / "artifacts/artifacts.jsonl").read_text()
    )
    source = next(a for a in store.all() if a.source_id == "DOC_001")
    assert (source.sensitivity, source.trust) == (Sensitivity.CONFIDENTIAL, Trust.TRUSTED)
    final = next(a for a in store.all() if a.artifact_type == ArtifactType.FINAL_RESPONSE)
    assert source in store.ancestors(final.artifact_id)
    assert (final.sensitivity, final.trust) == (Sensitivity.CONFIDENTIAL, Trust.UNTRUSTED)
    fields = [
        a
        for a in store.all()
        if a.artifact_type == ArtifactType.TOOL_ARGUMENT
        and isinstance(a.content(), dict)
        and "field" in a.content()
    ]
    assert {a.content()["field"] for a in fields} == {
        "to",
        "subject",
        "body",
        "endpoint",
        "payload",
    }
    assert all(
        a.sensitivity == Sensitivity.CONFIDENTIAL and source in store.ancestors(a.artifact_id)
        for a in fields
    )
    assert any(a.artifact_type == ArtifactType.NORMALIZED_VIEW for a in store.all())
    assert metadata["model_input_profile"] == "raw_v1"
    for line in (directory / "trace_v2.jsonl").read_text().splitlines():
        event = FoundationEvent.model_validate_json(line)
        if event.event == "normalization":
            data = json.loads(event.data_json)
            assert data["profile"] == "security_v1" and len(data["operations"]) == 5
            assert isinstance(data["features"]["zero_width_positions"], list)
            assert data["operations"][0]["before_hash"] == data["input_hash"]
            assert data["operations"][-1]["after_hash"] == data["output_hash"]


def test_unknown_labels_do_not_trust_tool_payload_assertions() -> None:
    catalog = SourceCatalog()
    assert (
        catalog.resolve(Action(name="doc_read", arguments={"doc_id": "safe_TRUSTED_S0"})).trust
        == Trust.UNTRUSTED
    )
    assert (
        catalog.resolve(
            Action(name="db_query", arguments={"sql": "SELECT note FROM x"})
        ).sensitivity
        == Sensitivity.CONFIDENTIAL
    )


def test_context_and_control_immutable_and_model_payload_separate() -> None:
    control = ControlState(run_id="x", task_id="x")
    with pytest.raises(ValueError):
        control.step = 2
    context = ContextBundle(run_id="x", step=1, model_turn=1, messages=())
    assert context.model_messages() == [] and context.artifact_ids == ()
    with pytest.raises(ValueError):
        Decision(effect="UNKNOWN")
    with pytest.raises(ValueError):
        ControlState(run_id="x", task_id="x", step=-1)


def test_hook_deny_or_mutation_not_silently_accepted(tmp_path: Path) -> None:
    class Deny:
        def evaluate(self, *args):
            return Decision(effect="DENY")

    class Mutate:
        def evaluate(self, state, action, artifacts):
            action.arguments["expression"] = "9+9"
            return Decision()

    for name, hook in (("deny", Deny()), ("mutate", Mutate())):
        runtime = FoundationRuntime(
            RecordingBackend([CALC, final_response()]), build_smoke_registry(SMOKE)
        )
        with pytest.raises(ValueError):
            runtime.run_instrumented(task(), output=tmp_path / name, pre_hook=hook)
        trace = (tmp_path / name / "trace_legacy.jsonl").read_text()
        assert '"tool_call_executed"' not in trace


def test_fresh_run_isolation_and_no_legacy_bypass(tmp_path: Path) -> None:
    runtime = FoundationRuntime(
        RecordingBackend([final_response(), final_response()]), build_smoke_registry(SMOKE)
    )
    first = runtime.run_instrumented(task(), output=tmp_path / "one")
    second = runtime.run_instrumented(task(), output=tmp_path / "two")
    assert first.result.run_id != second.result.run_id
    assert not {a.artifact_id for a in first.artifacts} & {a.artifact_id for a in second.artifacts}
    assert first.control.model_turn_count == second.control.model_turn_count == 1
    with pytest.raises(ValueError, match="fresh"):
        runtime.run_instrumented(task(), output=tmp_path / "one")
    with pytest.raises(ValueError, match="bypass"):
        runtime.run(task())


def test_artifact_parent_ids_only_actual_retry_context(tmp_path: Path) -> None:
    runtime = FoundationRuntime(
        RecordingBackend(["bad", final_response()]), build_smoke_registry(SMOKE)
    )
    run = runtime.run_instrumented(task(), output=tmp_path / "retry")
    models = [a for a in run.artifacts if a.artifact_type == ArtifactType.MODEL_OUTPUT]
    assert run.control.format_retry_count == 1 and run.control.parse_error_count == 1
    assert models[0].artifact_id not in run.contexts[1].artifact_ids
    assert tuple(p.parent_id for p in models[1].parents) == run.contexts[1].artifact_ids
    assert len(run.contexts[1].messages) == 3


def test_post_hook_cannot_drop_lineage_even_with_identical_result(tmp_path: Path) -> None:
    from react_agent.foundation.runtime_hooks import PostResult, RecordOnlyPostHook

    class BrokenPost(RecordOnlyPostHook):
        def process(self, state, action, result, store, action_id, catalog):
            good = super().process(state, action, result, store, action_id, catalog)
            fake = store.create(
                result.model_dump_json(),
                artifact_type=ArtifactType.TOOL_RESULT,
                source_type=SourceType.TOOL,
                source_id=None,
                producer="fake",
                created_step=state.step,
                sensitivity=Sensitivity.PUBLIC,
                trust=Trust.TRUSTED,
            )
            return PostResult(
                result_json=good.result_json,
                source_artifact_id=good.source_artifact_id,
                result_artifact_id=fake.artifact_id,
            )

    runtime = FoundationRuntime(
        RecordingBackend([CALC, final_response()]), build_smoke_registry(SMOKE)
    )
    with pytest.raises(ValueError, match="lineage"):
        runtime.run_instrumented(task(), output=tmp_path / "badpost", post_hook=BrokenPost())


def test_runtime_never_creates_output_under_frozen_data() -> None:
    runtime = FoundationRuntime(RecordingBackend([final_response()]), build_smoke_registry(SMOKE))
    target = ROOT / "data/phase4_forbidden_output"
    with pytest.raises(ValueError, match="frozen"):
        runtime.run_instrumented(task(), output=target)
    assert not target.exists()


def test_source_bindings_reject_ambiguity_and_malformed_arguments() -> None:
    label = SourceLabel(
        source_type=SourceType.DOCUMENT,
        source_id="one",
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.TRUSTED,
    )
    binding = SourceBinding(tool="doc_read", arguments_json='{"doc_id":"one"}', label=label)
    with pytest.raises(ValueError, match="ambiguous"):
        SourceCatalog(bindings=(binding, binding))
    with pytest.raises(ValueError):
        SourceBinding(tool="doc_read", arguments_json='{"doc_id": "one"}', label=label)


def test_suite_65_conditions_no_test_payload_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tempfile import TemporaryDirectory

    from react_agent.foundation.runtime_qa import run_suite

    original = Path.read_text

    def guarded(path: Path, *args: object, **kwargs: object) -> str:
        if path.is_relative_to(ROOT / "data"):
            relative = path.relative_to(ROOT / "data").as_posix()
            assert path.name not in {
                "test.jsonl",
                "test_ground_truth.jsonl",
                "test_attack.jsonl",
                "test_benign.jsonl",
                "pool_ground_truth.jsonl",
            }
            assert "/private/" not in relative or path.name in {
                "robustness_canonical_ids.json",
                "dev_ground_truth.jsonl",
            }
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    with TemporaryDirectory(prefix="phase4_runtime_test_", dir=ROOT / "results") as temporary:
        report = run_suite(ROOT, Path(temporary) / "suite")
    assert report["valid"] and report["paired_conditions"] == 65
    assert report["fresh_replay_runs"] == 130 and report["real_model_runs"] == 0
    assert report["test_payloads_parsed"] == 0 and not report["phase4_accepted"]
    assert {tool for check in report["checks"] for tool in check["tool_sequence"]} == {
        "doc_search",
        "doc_read",
        "db_query",
        "cached_search",
        "cached_fetch",
        "calculator",
        "send_email_mock",
        "post_webhook_mock",
    }
