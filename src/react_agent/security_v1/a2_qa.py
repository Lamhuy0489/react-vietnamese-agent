"""Synthetic A2 fixtures only: no model quality, dataset labels or benchmark input."""

from __future__ import annotations

import json
import os
import shutil
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import ArtifactStore, canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_qa import RecordingBackend, action_response, final_response
from react_agent.llm.base import GenerationConfig, LLMBackend, ModelResponse
from react_agent.schemas.adversarial_workbench import PublicWorkbenchTask
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.guard import PROMPT, GuardInput, GuardOutcome, GuardResult
from react_agent.security_v1.process_guard import ProcessGuardConfig
from react_agent.security_v1.runtime import SecurityRuntime as PreviousRuntime
from react_agent.security_v1.runtime_qa import audit_run, trace_events
from react_agent.security_v1.runtime_v2 import SecurityRuntime
from react_agent.tools.factory import build_smoke_registry

MODEL = "synthetic/guard-lifecycle"
REVISION = "synthetic-v2-not-a-real-model"


def audit_guard(output: Path) -> dict[str, Any]:
    metadata = json.loads((output / "run_metadata.json").read_text())
    rows = [json.loads(s) for s in (output / "trace_guard.jsonl").read_text().splitlines()]
    store = ArtifactStore.deserialize(
        metadata["run_id"], (output / "artifacts/artifacts.jsonl").read_text()
    )
    security = [json.loads(s) for s in (output / "trace_security.jsonl").read_text().splitlines()]
    expected = []
    for event in security:
        data = json.loads(event["data_json"])
        if event["event"] == "proposal":
            expected.append(("PRE", data["proposal_id"], data["artifact_id"], event["step"]))
        if event["event"] == "decision" and data["stage"] == "POST":
            result = store.get(data["artifact_id"])
            sources = [
                p.parent_id
                for p in result.parents
                if store.get(p.parent_id).producer == "tool_source_snapshot"
            ]
            if len(sources) != 1:
                raise ValueError("ambiguous Post source")
            expected.append(("POST", data["proposal_id"], sources[0], event["step"]))
    actual = [(r["stage"], r["proposal_id"], r["candidate_artifact_id"], r["step"]) for r in rows]
    if actual != expected or len(rows) != metadata["guard_classification_count"]:
        raise ValueError("guard gate coverage/link mismatch")
    attempts = []
    cached: dict[str, GuardResult] = {}
    for index, row in enumerate(rows, 1):
        if (
            row["sequence"] != index
            or row["run_id"] != metadata["run_id"]
            or row["task_id"] != metadata["task_id"]
            or row["elapsed_seconds"] < 0
        ):
            raise ValueError("guard identity/sequence/timing mismatch")
        request = GuardInput.model_validate(row["input"])
        outcome = GuardOutcome.model_validate(row["outcome"])
        if text_hash(request.user_instruction) != metadata["task_hash"]:
            raise ValueError("guard user differs from host user")
        artifact = store.get(row["candidate_artifact_id"])
        if row["stage"] == "PRE":
            if request.candidate_action_json != canonical_json(
                json.loads(str(artifact.content()))["action"]
            ):
                raise ValueError("guard action differs from proposed artifact")
        elif request.candidate_content != artifact.raw_json:
            raise ValueError("guard source differs from raw artifact")
        key = text_hash(
            canonical_json(
                {
                    "model": metadata["guard_execution"]["model_id"],
                    "revision": metadata["guard_execution"]["model_revision"],
                    "prompt": text_hash(PROMPT),
                    "generation": GenerationConfig(
                        temperature=0, max_new_tokens=128, seed=42
                    ).model_dump(),
                    "input": request.model_dump(mode="json"),
                }
            )
        )
        if outcome.cache_key != key:
            raise ValueError("guard cache identity mismatch")
        if outcome.cache_hit and (row["execution_attempts"] or cached.get(key) != outcome.result):
            raise ValueError("unexplained guard cache hit")
        if outcome.status == "OK":
            if outcome.result is None or outcome.error_code is not None:
                raise ValueError("invalid successful guard outcome")
            cached[key] = outcome.result
        elif outcome.result is not None or outcome.error_code is None:
            raise ValueError("invalid failed guard outcome")
        attempts.extend(row["execution_attempts"])
    if len(attempts) != metadata["guard_execution_attempt_count"]:
        raise ValueError("guard attempt count mismatch")
    for index, attempt in enumerate(attempts, 1):
        if (
            attempt["sequence"] != index
            or not attempt["reaped"]
            or attempt["elapsed_seconds"] < 0
            or attempt["execution_config_sha256"] != metadata["guard_execution_hash"]
        ):
            raise ValueError("guard worker lifecycle mismatch")
    return {"valid": True, "guard_classifications": len(rows), "guard_attempts": len(attempts)}


def parity_case(root: Path, output: Path, index: int, level: str = "A0") -> dict[str, Any]:
    from react_agent.security_v1.contracts import SecurityConfig

    smoke = root / "data/smoke"
    row = json.loads((smoke / "tasks.jsonl").read_text().splitlines()[index])
    task = PublicWorkbenchTask.model_construct(
        task_id=row["task_id"], instruction=row["instruction"]
    )
    responses = json.loads((smoke / "replay_responses.json").read_text())[task.task_id]
    config = SecurityConfig.model_validate(configuration("A0" if level == "A0" else "A1"))
    backends = [RecordingBackend(responses), RecordingBackend(responses)]
    runs = []
    runtimes: tuple[type[PreviousRuntime] | type[SecurityRuntime], ...] = (
        PreviousRuntime,
        SecurityRuntime,
    )
    for i, runtime in enumerate(runtimes):
        env = output / f"{i}_env"
        shutil.copytree(smoke, env)
        runs.append(
            runtime(backends[i], build_smoke_registry(env)).run_instrumented(
                task, output=output / str(i), security_config=config
            )
        )
    if (
        runs[0].result.model_dump(exclude={"run_id"})
        != runs[1].result.model_dump(exclude={"run_id"})
        or backends[0].messages != backends[1].messages
        or trace_events(output / "0/trace_legacy.jsonl")
        != trace_events(output / "1/trace_legacy.jsonl")
    ):
        raise ValueError("v2 changed A0/A1 behavior")
    return {
        "task_id": task.task_id,
        "level": level,
        **audit_run(runs[1], output / "1", backends[1].messages),
    }


@dataclass(frozen=True)
class SyntheticGuardFactory:
    pre_risk: str = "SAFE"
    post_risk: str = "SAFE"
    failure: str = ""

    def __call__(self) -> LLMBackend:
        if self.failure == "load_error":
            raise RuntimeError("synthetic exception text must not escape")
        return SyntheticGuard(self)


class SyntheticGuard:
    model_id = MODEL
    model_revision = REVISION

    def __init__(self, factory: SyntheticGuardFactory) -> None:
        self.factory = factory
        if factory.failure == "load_identity":
            self.model_revision = "wrong"

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        failure = self.factory.failure
        if failure in {"hang", "ignore_terminate"}:
            if failure == "ignore_terminate":
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
            time.sleep(60)  # Synthetic hung inference; parent must terminate this child.
        if failure == "crash":
            os._exit(17)
        if failure == "raise":
            raise RuntimeError("synthetic exception text must not escape")
        if failure == "mutate_identity":
            self.model_revision = "wrong"
        request = json.loads(messages[-1]["content"])
        risk = (
            self.factory.post_risk
            if request["candidate_content"] is not None
            else self.factory.pre_risk
        )
        text = canonical_json({"risk": risk, "labels": [], "confidence": "HIGH"})
        if failure == "invalid":
            text = '{"risk":"SAFE","reasoning":"not permitted"}'
        if failure == "oversize":
            text = "x" * 70_000
        return ModelResponse(text=text, model_id=MODEL, model_revision=REVISION)


def synthetic_case(root: Path, output: Path, *, pre: str, post: str) -> dict[str, Any]:
    read = Action(name="doc_read", arguments={"doc_id": "DOC_001"})
    mail = Action(
        name="send_email_mock",
        arguments={"to": "demo@example.test", "subject": "public", "body": "public"},
    )
    backend = RecordingBackend([action_response(read), action_response(mail), final_response()])
    env = output.parent / (output.name + "_env")
    shutil.copytree(root / "data/smoke", env)
    run = SecurityRuntime(backend, build_smoke_registry(env)).run_instrumented(
        PublicWorkbenchTask(task_id="awb_guardsynthetic", instruction="Tóm tắt tài liệu giả lập."),
        output=output,
        security_config=configuration("A2"),
        guard_factory=SyntheticGuardFactory(pre, post),
        guard_execution=ProcessGuardConfig(MODEL, REVISION, timeout_seconds=10),
    )
    audit = audit_run(run, output, backend.messages)
    expected_denials = int(pre == "MALICIOUS" or post == "MALICIOUS")
    if run.denied_tool_count != expected_denials:
        raise ValueError("synthetic A2 gate mismatch")
    rows = [json.loads(line) for line in (output / "trace_guard.jsonl").read_text().splitlines()]
    expected_count = 3 if expected_denials else 4
    if len(rows) != expected_count or any(r["run_id"] != run.result.run_id for r in rows):
        raise ValueError("guard trace coverage mismatch")
    metadata = json.loads((output / "run_metadata.json").read_text())
    if metadata["guard_classification_count"] != len(rows):
        raise ValueError("guard metadata mismatch")
    guard_audit = audit_guard(output)
    return {
        "pre": pre,
        "post": post,
        "denials": expected_denials,
        "classifications": len(rows),
        "valid": audit["valid"],
        **guard_audit,
    }
