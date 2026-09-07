"""Deterministic synthetic component cases; not A6 runtime or benchmark scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    ParentLink,
    Relation,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.value_origin import ValueOriginIndex, ValueType
from react_agent.security_v1.value_release import FinalValueRelease, release_final

CASES = (
    ("email", "Email: private@example.test", Effect.REDACT, "Email: [REDACTED]"),
    ("decimal", "GPA: 2.130", Effect.REDACT, "GPA: [REDACTED]"),
    ("unicode", "Email: private@exam\u200bple.test", Effect.DENY, ""),
    ("public_answer", "Nội dung công khai khác", Effect.ALLOW, "Nội dung công khai khác"),
)


def component_cases(output: Path) -> list[dict[str, Any]]:
    if output.exists():
        raise ValueError("fresh component output required")
    output.mkdir(parents=True)
    reports = []
    for sensitivity in Sensitivity:
        for trust in Trust:
            for name, text, protected_effect, protected_text in CASES:
                case_id = f"{sensitivity.value}_{trust.value}_{name}"
                store = ArtifactStore("value_" + case_id)
                raw = store.create(
                    {"email": "private@example.test", "gpa": 2.13},
                    artifact_type=ArtifactType.DOCUMENT_CONTENT,
                    source_type=SourceType.DOCUMENT,
                    source_id="synthetic_component",
                    producer="tool_source_snapshot",
                    created_step=1,
                    sensitivity=sensitivity,
                    trust=trust,
                )
                index = ValueOriginIndex(store)
                index.add_artifact(raw.artifact_id, observed_step=1)
                evidence = index.find_origins("private@example.test", ValueType.EMAIL)
                if (
                    not evidence.known
                    or evidence.max_sensitivity != sensitivity
                    or evidence.trust != trust
                ):
                    raise ValueError("origin evidence differs from synthetic host labels")
                final = store.create(
                    text,
                    artifact_type=ArtifactType.FINAL_RESPONSE,
                    source_type=SourceType.MODEL,
                    source_id=None,
                    producer="synthetic_proposed_final",
                    created_step=2,
                    sensitivity=sensitivity,
                    trust=trust,
                    parents=(
                        ParentLink(parent_id=raw.artifact_id, relation=Relation.GENERATED_USING),
                    ),
                )
                before = store.serialize()
                result = release_final(index, final.artifact_id)
                released = store.get(result.released_artifact_id)
                expected_effect = (
                    Effect.ALLOW if sensitivity == Sensitivity.PUBLIC else protected_effect
                )
                expected_text = text if sensitivity == Sensitivity.PUBLIC else protected_text
                if result.effect != expected_effect or released.content() != expected_text:
                    raise ValueError("component release differs from predeclared exact expectation")
                if (
                    not store.serialize().startswith(before)
                    or store.get(final.artifact_id) != final
                    or released.sensitivity != sensitivity
                    or released.trust != trust
                    or final.artifact_id not in {p.parent_id for p in released.parents}
                ):
                    raise ValueError("release lost raw preservation or conservative lineage")
                if index.protected_matches(str(released.content())):
                    raise ValueError("known protected value remains after release")
                restored = ArtifactStore.deserialize(store.run_id, store.serialize())
                if restored.all() != store.all():
                    raise ValueError("artifact round trip mismatch")
                if FinalValueRelease.model_validate_json(result.model_dump_json()) != result:
                    raise ValueError("release decision round trip mismatch")
                dest = output / case_id
                store.export(dest)
                (dest / "index.json").write_text(
                    json.dumps(index.snapshot(), ensure_ascii=False, indent=2) + "\n"
                )
                (dest / "release.json").write_text(result.model_dump_json(indent=2) + "\n")
                reports.append(
                    {
                        "case": case_id,
                        "sensitivity": sensitivity.value,
                        "trust": trust.value,
                        "effect": result.effect.value,
                        "artifact_count": len(store.all()),
                        "origin_count": len(index.records),
                        "index_sha256": index.identity,
                        "proposed_sha256": result.proposed_sha256,
                        "released_sha256": result.released_sha256,
                        "valid": True,
                    }
                )
    return reports
