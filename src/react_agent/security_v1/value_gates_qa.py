"""Synthetic-only PreGate/Broker and Post-view component evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from react_agent.broker import ToolBroker
from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Relation,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.foundation.runtime_hooks import derive
from react_agent.logging import TraceLogger
from react_agent.schemas.agent_output import Action, ActionTurn
from react_agent.schemas.tool import ToolResult
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.value_gates import ValuePreDecision, post_data_view, value_pre_check
from react_agent.security_v1.value_origin import ValueOriginIndex
from react_agent.tools.factory import build_smoke_registry

PUBLIC = "Lịch học công khai học phần CS101"
SUBJECT = "Thông báo lịch học công khai"


def fixture(
    *,
    sensitivity: Sensitivity = Sensitivity.PUBLIC,
    trust: Trust = Trust.TRUSTED,
    authorized: bool = True,
    webhook: bool = False,
    unrelated_secret: bool = False,
) -> tuple[ArtifactStore, ValueOriginIndex, str, str]:
    store = ArtifactStore("synthetic_value_gate")
    user_text = (
        ("Post webhook to mock://report" if webhook else "Gửi kết quả đến demo@example.test")
        if authorized
        else "Chỉ đọc và trả lời."
    )
    user = store.create(
        user_text,
        artifact_type=ArtifactType.USER_INPUT,
        source_type=SourceType.USER,
        source_id="synthetic",
        producer="host_context",
        created_step=0,
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.UNTRUSTED,
    )
    raw = store.create(
        {
            "content": PUBLIC,
            "subject": SUBJECT,
            "email": "demo@example.test",
            "endpoint": "mock://report",
        },
        artifact_type=ArtifactType.DOCUMENT_CONTENT,
        source_type=SourceType.DOCUMENT,
        source_id="synthetic",
        producer="tool_source_snapshot",
        created_step=1,
        sensitivity=sensitivity,
        trust=trust,
    )
    index = ValueOriginIndex(store)
    index.add_artifact(user.artifact_id, observed_step=0)
    index.add_artifact(raw.artifact_id, observed_step=1)
    if unrelated_secret:
        secret = store.create(
            {"email": "private@example.test"},
            artifact_type=ArtifactType.DOCUMENT_CONTENT,
            source_type=SourceType.DOCUMENT,
            source_id="synthetic_secret",
            producer="tool_source_snapshot",
            created_step=1,
            sensitivity=Sensitivity.CONFIDENTIAL,
            trust=Trust.TRUSTED,
        )
        index.add_artifact(secret.artifact_id, observed_step=1)
    return store, index, user.artifact_id, raw.artifact_id


def action_artifact(store: ArtifactStore, action: Action) -> str:
    roots = tuple(a.artifact_id for a in store.all() if not a.parents)
    model = derive(
        store,
        ActionTurn(action=action).model_dump_json(),
        kind=ArtifactType.MODEL_OUTPUT,
        parents=roots,
        step=2,
        relation=Relation.GENERATED_USING,
    )
    return derive(
        store,
        model.content(),
        kind=ArtifactType.MODEL_OUTPUT,
        parents=(model.artifact_id,),
        step=2,
        relation=Relation.EXTRACTED_FROM,
    ).artifact_id


def external_action(webhook: bool = False) -> Action:
    return Action(
        name="post_webhook_mock" if webhook else "send_email_mock",
        arguments={
            "endpoint": "mock://report",
            "payload": {"message": PUBLIC},
        }
        if webhook
        else {"to": "demo@example.test", "subject": SUBJECT, "body": PUBLIC},
    )


def component_cases(root: Path, output: Path) -> list[dict[str, Any]]:
    if output.exists():
        raise ValueError("fresh QA output required")
    output.mkdir(parents=True)
    reports = []
    for sensitivity in Sensitivity:
        for trust in Trust:
            for authorized in (False, True):
                for webhook in (False, True):
                    case = f"{sensitivity.value}_{trust.value}_{authorized}_{webhook}"
                    store, index, user_id, _ = fixture(
                        sensitivity=sensitivity, trust=trust, authorized=authorized, webhook=webhook
                    )
                    action = external_action(webhook)
                    proposal = action_artifact(store, action)
                    registry = build_smoke_registry(root / "data/smoke")
                    raw_before = store.serialize()
                    decision = value_pre_check(index, proposal, user_id, registry)
                    expected = (
                        Effect.ALLOW
                        if sensitivity == Sensitivity.PUBLIC and authorized
                        else Effect.DENY
                    )
                    if decision.effect != expected or store.serialize() != raw_before:
                        raise ValueError("gate expectation/raw preservation mismatch")
                    if ValuePreDecision.model_validate_json(decision.model_dump_json()) != decision:
                        raise ValueError("decision round-trip mismatch")
                    dest = output / case
                    store.export(dest)
                    (dest / "index.json").write_text(
                        json.dumps(index.snapshot(), ensure_ascii=False, indent=2) + "\n"
                    )
                    (dest / "decision.json").write_text(decision.model_dump_json(indent=2) + "\n")
                    result = None
                    if decision.effect == Effect.ALLOW:
                        result = ToolBroker(registry, TraceLogger(dest / "trace.jsonl")).execute(
                            action.name,
                            action.arguments,
                            run_id=store.run_id,
                            task_id="synthetic",
                            step=2,
                        )
                        if not result.ok:
                            raise ValueError("authorized mock Broker execution failed")
                        (dest / "broker.json").write_text(result.model_dump_json(indent=2) + "\n")
                    restored = ArtifactStore.deserialize(store.run_id, store.serialize())
                    rebuilt = ValueOriginIndex(restored)
                    for identity in index.snapshot()["source_sha256"]:
                        rebuilt.add_artifact(
                            identity, observed_step=restored.get(identity).created_step
                        )
                    if value_pre_check(rebuilt, proposal, user_id, registry) != decision:
                        raise ValueError(
                            "gate decision does not reconstruct from serialized evidence"
                        )
                    reports.append(
                        {
                            "case": case,
                            "effect": decision.effect.value,
                            "broker_calls": int(result is not None),
                            "fields": len(decision.fields),
                            "index_sha256": index.identity,
                            "valid": True,
                        }
                    )
    return reports


def post_cases(output: Path) -> list[dict[str, Any]]:
    if output.exists():
        raise ValueError("fresh Post QA required")
    output.mkdir(parents=True)
    reports = []
    for sensitivity in Sensitivity:
        for trust in Trust:
            store, _, _, source_id = fixture(sensitivity=sensitivity, trust=trust)
            source = store.get(source_id)
            result = ToolResult(
                call_id="call_000001", tool_name="doc_read", ok=True, content=source.content()
            )
            observation = derive(
                store,
                result.model_dump_json(),
                kind=ArtifactType.TOOL_RESULT,
                parents=(source_id,),
                step=1,
                source_type=SourceType.TOOL,
                producer="record_only_post",
            )
            before = store.serialize()
            view = post_data_view(store, source_id, observation.artifact_id)
            if (
                not store.serialize().startswith(before)
                or view.trust != trust
                or view.sensitivity != sensitivity
            ):
                raise ValueError("Post view lost labels or raw data")
            if trust == Trust.UNTRUSTED:
                if json.loads(str(view.content()))["data"] != result.model_dump(mode="json"):
                    raise ValueError("Post view data differs from raw ToolResult")
            elif view != observation:
                raise ValueError("trusted Post must retain the observation")
            case = sensitivity.value + "_" + trust.value
            store.export(output / case)
            if ArtifactStore.deserialize(store.run_id, store.serialize()).all() != store.all():
                raise ValueError("Post artifact round-trip mismatch")
            reports.append(
                {
                    "case": case,
                    "view_created": view != observation,
                    "view_sha256": view.content_hash,
                    "valid": True,
                }
            )
    return reports
