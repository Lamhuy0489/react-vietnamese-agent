"""Deterministic synthetic lifecycle fixtures and cold/warm runtime comparisons."""

from __future__ import annotations

import json
import os
import shutil
import signal
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import (
    ArtifactStore,
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
)
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.a2_qa import MODEL, REVISION, SyntheticGuardFactory
from react_agent.security_v1.a6_qa import audit_values
from react_agent.security_v1.contracts import Level, configuration
from react_agent.security_v1.guard import PROMPT, GuardInput, GuardOutcome
from react_agent.security_v1.process_guard import ProcessGuardConfig
from react_agent.security_v1.runtime_qa import trace_events
from react_agent.security_v1.runtime_v4 import SecurityRuntime as ColdRuntime
from react_agent.security_v1.runtime_v5 import SecurityRuntime
from react_agent.security_v1.session_qa import audit_session
from react_agent.security_v1.value_gates_qa import PUBLIC, SUBJECT, external_action
from react_agent.security_v1.warm_guard import WarmGuardBackend, WarmGuardConfig, WarmModelGuard
from react_agent.tools.factory import build_smoke_registry


@dataclass(frozen=True)
class LifecycleFactory:
    mode: str = "safe"

    def __call__(self) -> LLMBackend:
        if self.mode == "load_error":
            raise RuntimeError("synthetic backend text must be sanitized")
        if self.mode == "load_hang":
            time.sleep(20)
        return LifecycleBackend(self.mode)


class LifecycleBackend:
    model_id = MODEL

    def __init__(self, mode: str) -> None:
        self.model_revision = "wrong" if mode == "initial_identity" else REVISION
        self.mode = mode
        self.calls = 0

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        self.calls += 1
        if self.calls == 2:
            if self.mode == "crash_second":
                os._exit(7)
            if self.mode == "identity_second":
                self.model_revision = "changed"
            if self.mode == "kill_second":
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
            if self.mode in {"hang_second", "kill_second"}:
                time.sleep(20)
        text = canonical_json({"risk": "SAFE", "labels": [], "confidence": "HIGH"})
        if self.mode == "counter":
            text = canonical_json({"calls": self.calls, "pid": os.getpid()})
        elif self.mode == "oversized":
            text = "X" * 70_000
        elif self.mode == "invalid_second" and self.calls == 2:
            text = "invalid guard JSON"
        return ModelResponse(
            text=text,
            model_id=self.model_id,
            model_revision="wrong" if self.mode == "response_identity" else self.model_revision,
        )


def audit_lifecycle(output: Path) -> dict[str, Any]:
    metadata = json.loads((output / "run_metadata.json").read_text())
    guards = [json.loads(s) for s in (output / "trace_guard.jsonl").read_text().splitlines()]
    attempts = [a for g in guards for a in g["execution_attempts"]]
    store = ArtifactStore.deserialize(
        metadata["run_id"], (output / "artifacts/artifacts.jsonl").read_text()
    )
    security = [json.loads(s) for s in (output / "trace_security.jsonl").read_text().splitlines()]
    expected = []
    for event in security:
        data = json.loads(event["data_json"])
        if event["event"] == "proposal":
            expected.append(("PRE", data["proposal_id"], data["artifact_id"]))
        elif event["event"] == "decision" and data["stage"] == "POST":
            raw = store.get(data["artifact_id"])
            source_ids = [
                p.parent_id
                for p in raw.parents
                if store.get(p.parent_id).producer == "tool_source_snapshot"
            ]
            if len(source_ids) != 1:
                raise ValueError("guard Post source binding mismatch")
            expected.append(("POST", data["proposal_id"], source_ids[0]))
    if [(g["stage"], g["proposal_id"], g["candidate_artifact_id"]) for g in guards] != expected:
        raise ValueError("guard lifecycle coverage mismatch")
    if (
        not metadata["guard_closed"]
        or len(attempts) != metadata["guard_execution_attempt_count"]
        or len(guards) != metadata["guard_classification_count"]
    ):
        raise ValueError("warm lifecycle accounting mismatch")
    cache: dict[str, object] = {}
    for row in guards:
        request = GuardInput.model_validate(row["input"])
        GuardOutcome.model_validate(row["outcome"])
        source = store.get(row["candidate_artifact_id"])
        if text_hash(request.user_instruction) != metadata["task_hash"]:
            raise ValueError("guard input user differs from host user")
        if row["stage"] == "PRE":
            if request.candidate_action_json != canonical_json(
                json.loads(str(source.content()))["action"]
            ):
                raise ValueError("guard input differs from proposed action")
        elif request.candidate_content != source.raw_json:
            raise ValueError("guard input differs from raw source")
        key = text_hash(
            canonical_json(
                {
                    "model": metadata["guard_execution"]["model_id"],
                    "revision": metadata["guard_execution"]["model_revision"],
                    "prompt": text_hash(PROMPT),
                    "generation": metadata["guard_generation"],
                    "input": request.model_dump(mode="json"),
                }
            )
        )
        if key != row["outcome"]["cache_key"]:
            raise ValueError("guard cache identity mismatch")
        request_hash = text_hash(
            canonical_json(
                [
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": canonical_json(request.model_dump(mode="json"))},
                ]
            )
        )
        for attempt in row["execution_attempts"]:
            if attempt["request_sha256"] != request_hash or attempt[
                "generation_sha256"
            ] != text_hash(canonical_json(metadata["guard_generation"])):
                raise ValueError("execution request/generation binding mismatch")
        outcome = row["outcome"]
        if outcome["cache_hit"] and (
            row["execution_attempts"] or cache.get(outcome["cache_key"]) != outcome["result"]
        ):
            raise ValueError("unexplained cached outcome")
        if outcome["status"] == "OK":
            cache[outcome["cache_key"]] = outcome["result"]
        else:
            cache.clear()
    pids = {a["pid"] for a in attempts if a["pid"] is not None}
    if len(pids) > 1:
        raise ValueError("warm worker restarted within task")
    for i, attempt in enumerate(attempts, 1):
        if (
            attempt["sequence"] != i
            or attempt["elapsed_seconds"] < 0
            or attempt["execution_config_sha256"] != metadata["guard_execution_hash"]
        ):
            raise ValueError("warm attempt identity mismatch")
        if attempt["status"] == "OK":
            if not attempt["worker_retained"] or attempt["reaped"]:
                raise ValueError("successful warm request must retain worker")
            if attempt["cold_start"] != (i == 1):
                raise ValueError("load accounting mismatch")
            if i > 1 and attempt["load_seconds"] != 0:
                raise ValueError("warm request reloaded model")
        elif not attempt["reaped"]:
            raise ValueError("failed request not reaped")
    cleanup = metadata["guard_lifecycle_events"]
    if pids != {e["pid"] for e in cleanup if e["pid"] is not None} or any(
        not e["reaped"] for e in cleanup
    ):
        raise ValueError("worker not closed/reaped at task boundary")
    return {
        "valid": True,
        "guard_classifications": len(guards),
        "guard_attempts": len(attempts),
        "worker_processes": len(pids),
    }


def comparable_contexts(output: Path, messages: list[list[dict[str, str]]]) -> object:
    """Rename only host Post-envelope source IDs using their verified source binding."""
    metadata = json.loads((output / "run_metadata.json").read_text())
    store = ArtifactStore.deserialize(
        metadata["run_id"], (output / "artifacts/artifacts.jsonl").read_text()
    )
    copied = [[dict(m) for m in context] for context in messages]
    for context in copied:
        for message in context:
            if not message["content"].startswith("OBSERVATION: "):
                continue
            envelope = json.loads(message["content"].removeprefix("OBSERVATION: "))
            if envelope.get("representation") != "untrusted_data_view_v1":
                continue
            source = store.get(envelope["source_artifact_id"])
            envelope["source_artifact_id"] = {
                "source_id": source.source_id,
                "source_type": source.source_type.value,
                "content_hash": source.content_hash,
                "step": source.created_step,
                "sensitivity": source.sensitivity.value,
                "trust": source.trust.value,
            }
            message["content"] = "OBSERVATION: " + canonical_json(envelope)
    return copied


def parity_case(
    root: Path, output: Path, level: Level, *, error: bool = False, external: str = ""
) -> dict[str, Any]:
    instruction = (
        (
            "Post webhook to mock://report"
            if external == "webhook"
            else "Gửi kết quả đến demo@example.test"
        )
        if external
        else "Chỉ đọc và trả lời."
    )
    task = PublicWorkbenchTask(task_id="awb_warm", instruction=instruction)
    reads = [
        Action(name="doc_read", arguments={"doc_id": "DOC_001"}),
        Action(name="calculator", arguments={"expression": "1+1"}),
        Action(name="calculator", arguments={"expression": "1+1"}),
    ]
    if external:
        reads.append(external_action(external == "webhook"))
    responses = [action_response(a) for a in reads] + [final_response()]
    catalog = (
        SourceCatalog(
            bindings=(
                SourceBinding(
                    tool="doc_read",
                    arguments_json=canonical_json({"doc_id": "DOC_001"}),
                    label=SourceLabel(
                        source_type=SourceType.DOCUMENT,
                        source_id="DOC_001",
                        sensitivity=Sensitivity.PUBLIC,
                        trust=Trust.UNTRUSTED,
                    ),
                ),
            )
        )
        if external
        else None
    )
    outputs, messages = [], []
    for i in range(2):
        env = output / f"{i}_env"
        shutil.copytree(root / "data/smoke", env)
        if external:
            path = env / "documents/documents.json"
            documents = json.loads(path.read_text())
            next(d for d in documents if d["doc_id"] == "DOC_001").update(
                title=SUBJECT, content=PUBLIC
            )
            path.write_text(json.dumps(documents, ensure_ascii=False) + "\n")
        backend = RecordingBackend(responses)
        guarded = int(level[1]) >= 2
        factory = SyntheticGuardFactory(failure="load_error" if error else "") if guarded else None
        if i == 0:
            run = ColdRuntime(backend, build_smoke_registry(env)).run_instrumented(
                task,
                output=output / str(i),
                security_config=configuration(level),
                source_catalog=catalog,
                guard_factory=factory,
                guard_execution=ProcessGuardConfig(MODEL, REVISION, 10) if guarded else None,
            )
        else:
            run = SecurityRuntime(backend, build_smoke_registry(env)).run_instrumented(
                task,
                output=output / str(i),
                security_config=configuration(level),
                source_catalog=catalog,
                guard_factory=factory,
                guard_execution=WarmGuardConfig(MODEL, REVISION, 10) if guarded else None,
            )
        outputs.append(run.result.model_dump(exclude={"run_id"}))
        messages.append(backend.messages)
        if external and (
            run.denied_tool_count != int(error) or len(run.result.tool_sequence) != 4 - int(error)
        ):
            raise ValueError("critical sink differs from predeclared allow/error-deny behavior")
    if (
        outputs[0] != outputs[1]
        or comparable_contexts(output / "0", messages[0])
        != comparable_contexts(output / "1", messages[1])
        or trace_events(output / "0/trace_legacy.jsonl")
        != trace_events(output / "1/trace_legacy.jsonl")
    ):
        raise ValueError("warm lifecycle changed observable runtime behavior")
    result: dict[str, Any] = {"valid": True, "level": level, "error": error, "external": external}
    if int(level[1]) >= 2:
        result.update(audit_lifecycle(output / "1"))
    if int(level[1]) >= 3:
        result.update(audit_session(output / "1"))
    if level == "A6":
        result.update(audit_values(output / "1", root, messages[1]))
    return result


def component_cases(output: Path) -> list[dict[str, Any]]:
    reports = []
    modes = (
        "counter",
        "cache",
        "load_error",
        "initial_identity",
        "oversized",
        "invalid_second",
        "crash_second",
        "hang_second",
        "kill_second",
    )
    for mode in modes:
        destination = output / mode
        destination.mkdir(parents=True, exist_ok=False)
        backend = WarmGuardBackend(
            LifecycleFactory("safe" if mode == "cache" else mode),
            WarmGuardConfig(MODEL, REVISION, 2, terminate_grace_seconds=0.2),
        )
        outcomes = []
        values: list[dict[str, Any]] = []
        with backend:
            if mode == "counter":
                values = [
                    json.loads(backend.generate([], GenerationConfig()).text) for _ in range(3)
                ]
                if [v["calls"] for v in values] != [1, 2, 3] or len(
                    {v["pid"] for v in values}
                ) != 1:
                    raise ValueError("backend was not loaded once and reused")
            else:
                guard = WarmModelGuard(backend)
                first = GuardInput(
                    user_instruction="Chỉ đọc", source_type="document", candidate_content="public"
                )
                outcomes.append(guard.classify(first).model_dump(mode="json"))
                if mode == "cache":
                    outcomes.append(guard.classify(first).model_dump(mode="json"))
                    outcomes.append(
                        guard.classify(
                            first.model_copy(update={"candidate_content": "other"})
                        ).model_dump(mode="json")
                    )
                    if (
                        not outcomes[1]["cache_hit"]
                        or len(backend.attempts) != 2
                        or any(o["status"] != "OK" for o in outcomes)
                    ):
                        raise ValueError("cache/reuse mismatch")
                elif mode.endswith("second"):
                    if outcomes[0]["status"] != "OK":
                        raise ValueError("cold request failed unexpectedly")
                    outcomes.append(
                        guard.classify(
                            first.model_copy(update={"candidate_content": "other"})
                        ).model_dump(mode="json")
                    )
                    if outcomes[-1]["status"] != "ERROR" or not backend.retired:
                        raise ValueError("warm failure did not retire")
                elif outcomes[0]["status"] != "ERROR" or not backend.retired:
                    raise ValueError("initial failure not retired")
        if not backend.closed or any(not e["reaped"] for e in backend.lifecycle_events):
            raise ValueError("component worker leaked")
        (destination / "worker.json").write_text(
            canonical_json(
                {
                    "execution_config": asdict(backend.config),
                    "attempts": backend.attempts,
                    "lifecycle": backend.lifecycle_events,
                    "outcomes": outcomes,
                    "counter_responses": values,
                }
            )
            + "\n"
        )
        reports.append(
            {
                "valid": True,
                "component": mode,
                "request_statuses": [a["status"] for a in backend.attempts],
                "outcome_statuses": [o["status"] for o in outcomes],
                "closed": backend.closed,
            }
        )
    return reports


def all_cases(root: Path, output: Path) -> list[dict[str, Any]]:
    levels: tuple[Level, ...] = ("A0", "A1", "A2", "A3", "A4", "A5", "A6")
    external_levels: tuple[Level, ...] = ("A5", "A6")
    return (
        [
            parity_case(root, output / f"parity_{level}_{error}", level, error=error)
            for level in levels
            for error in (False, True)
        ]
        + [
            parity_case(
                root,
                output / f"external_{level}_{channel}_{error}",
                level,
                error=error,
                external=channel,
            )
            for level in external_levels
            for channel in ("mail", "webhook")
            for error in (False, True)
        ]
        + component_cases(output / "components")
    )
