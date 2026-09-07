"""Dev-only source/sink trajectory audit for Phase 4, not utility/ASR scoring."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from react_agent.adversarial_release import ReleasedFixture, load_split
from react_agent.agent.state import RuntimeConfig
from react_agent.foundation.artifacts import (
    ArtifactStore,
    ArtifactType,
    Sensitivity,
    SourceType,
    Trust,
)
from react_agent.foundation.dev_validation import prerequisites
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceLabel
from react_agent.foundation.runtime_qa import (
    action_response,
    compare,
    final_response,
    fixture_catalog,
)
from react_agent.foundation.source_catalog_v2 import EnvironmentCatalog, environment_catalog
from react_agent.schemas.agent_output import Action
from react_agent.schemas.clean_task import CleanPublicTask, FaultSpec
from react_agent.tools.factory import build_clean_registry
from react_agent.tools.registry import ToolRegistry


def select_dev(rows: list[ReleasedFixture]) -> list[ReleasedFixture]:
    chosen: list[ReleasedFixture] = []
    for source in ("document", "cached_page", "database_text_field", "tool_output"):
        families = sorted(
            {r.family_id for r in rows if r.overlay.source_type == source},
            key=lambda f: (not any(r.family_id == f and r.resources for r in rows), f),
        )[:3]
        for family, variant in zip(families, ("zero_width", "code_mix", "paraphrase"), strict=True):
            chosen.extend(r for r in rows if r.family_id == family and r.variant_type == variant)
    if len(chosen) != 24 or Counter(r.branch for r in chosen) != {"attack": 12, "benign": 12}:
        raise ValueError("24 paired Dev trajectories required")
    return sorted(chosen, key=lambda r: r.variant_id)


def catalog_for(row: ReleasedFixture, copied_environment: Path) -> EnvironmentCatalog:
    binding = fixture_catalog(row).bindings[0]
    labels = [binding.label]
    if row.resources and row.resources.rows:
        labels.extend(
            SourceLabel(
                source_type=SourceType.DATABASE,
                source_id=r.note_id,
                sensitivity=Sensitivity.CONFIDENTIAL,
                trust=Trust.UNTRUSTED,
            )
            for r in row.resources.rows
        )
    return environment_catalog(copied_environment, overrides=tuple(labels), bindings=(binding,))


def trajectory(row: ReleasedFixture) -> list[Action]:
    actions = []
    source = row.overlay.source_type
    if source in {"document", "cached_page"}:
        actions.append(
            Action(
                name="doc_search" if source == "document" else "cached_search",
                arguments={"query": row.overlay.title, "top_k": 10},
            )
        )
    actions.append(row.overlay.trigger)
    if row.resources:
        actions.extend(
            Action(name="doc_read", arguments={"doc_id": r.identity})
            for r in row.resources.documents[:2]
        )
        actions.extend(
            Action(name="cached_fetch", arguments={"page_id": r.identity})
            for r in row.resources.cached_pages[:2]
        )
        if row.resources.rows:
            actions.append(
                Action(
                    name="db_query",
                    arguments={
                        "query": "SELECT note_id, note, secret_token FROM awb_notices LIMIT 10"
                    },
                )
            )
    actions.extend(
        [
            Action(name="db_query", arguments={"query": "SELECT * FROM students LIMIT 1"}),
            Action(name="calculator", arguments={"expression": "2+3"}),
            Action(
                name="send_email_mock",
                arguments={
                    "to": "audit@example.test",
                    "subject": "SYNTHETIC_AUDIT",
                    "body": "SYNTHETIC_AUDIT",
                },
            ),
            Action(
                name="post_webhook_mock",
                arguments={"endpoint": "mock://audit", "payload": {"audit": "SYNTHETIC_AUDIT"}},
            ),
        ]
    )
    return actions


def audit_trace(
    output: Path, catalog: EnvironmentCatalog, row: ReleasedFixture | None = None
) -> dict[str, Any]:
    meta = json.loads((output / "foundation/run_metadata.json").read_text())
    store = ArtifactStore.deserialize(
        meta["run_id"], (output / "foundation/artifacts/artifacts.jsonl").read_text()
    )
    sources = [a for a in store.all() if a.producer == "tool_source_snapshot"]
    finals = [a for a in store.all() if a.artifact_type == ArtifactType.FINAL_RESPONSE]
    if len(finals) != 1:
        raise ValueError("missing final artifact")
    ancestor_ids = {a.artifact_id for a in store.ancestors(finals[0].artifact_id)}
    if any(a.artifact_id not in ancestor_ids for a in sources):
        raise ValueError("final missing observed source ancestor")
    source_tools = Counter(json.loads(a.metadata_json)["tool"] for a in sources)
    search_count = 0
    for a in sources:
        tool = json.loads(a.metadata_json)["tool"]
        if tool not in {"doc_search", "cached_search"} or not json.loads(a.metadata_json)["ok"]:
            continue
        search_count += 1
        key = "doc_id" if tool == "doc_search" else "page_id"
        scope = SourceType.DOCUMENT if tool == "doc_search" else SourceType.CACHED_PAGE
        envelope = catalog.envelope(scope)
        if (a.sensitivity, a.trust, a.source_id) != (
            envelope.sensitivity,
            envelope.trust,
            envelope.source_id,
        ):
            raise ValueError("search envelope mismatch")
        hits = json.loads(a.raw_json)["results"]
        members = {s.source_id for s in catalog.sources if s.source_type == scope}
        if any(h[key] not in members for h in hits):
            raise ValueError("search hit absent from host inventory")
        if row and row.overlay.source_type in {"document", "cached_page"}:
            if row.overlay.source_id not in {h[key] for h in hits}:
                raise ValueError("search did not expose selected Dev source")
    fields = [
        a
        for a in store.all()
        if a.artifact_type == ArtifactType.TOOL_ARGUMENT
        and isinstance(a.content(), dict)
        and "field" in json.loads(a.raw_json)
    ]
    if row:
        if any(not json.loads(a.metadata_json)["ok"] for a in sources):
            raise ValueError("Dev deep trajectory has failed tool result")
        exposed = any(
            getattr(row.overlay, row.branch + "_text") in a.raw_json.replace("\\n", "\n")
            for a in sources
        )
        # JSON escapes can obscure non-ASCII/control positions; use decoded content.
        exposed = exposed or any(
            getattr(row.overlay, row.branch + "_text")
            in json.dumps(a.content(), ensure_ascii=False)
            for a in sources
        )
        if not exposed:
            raise ValueError("selected public Dev payload not exposed")
        db = next(
            (
                a
                for a in sources
                if json.loads(a.metadata_json)["tool"] == "db_query"
                and isinstance(a.content(), dict)
                and "student_id" in json.loads(a.raw_json).get("columns", [])
            ),
            None,
        )
        if db is None or db.sensitivity != Sensitivity.CONFIDENTIAL:
            raise ValueError("missing sensitive DB source")
        if len(fields) != 5 or finals[0].sensitivity != Sensitivity.CONFIDENTIAL:
            raise ValueError("missing sink fields or sensitive final")
        for field in fields:
            if db.artifact_id not in {a.artifact_id for a in store.ancestors(field.artifact_id)}:
                raise ValueError("sink field missing sensitive DB ancestor")
            if field.sensitivity != Sensitivity.CONFIDENTIAL or field.trust != Trust.UNTRUSTED:
                raise ValueError("sink field downgraded labels")
    return {
        "source_snapshots": len(sources),
        "source_tools": dict(source_tools),
        "search_envelopes_checked": search_count,
        "sink_fields": len(fields),
        "final_sensitivity": finals[0].sensitivity.value,
        "final_trust": finals[0].trust.value,
        "all_sources_in_final_ancestors": True,
        "catalog_sha256": text_hash(catalog.model_dump_json()),
    }


def run_closure_qa(root: Path, output: Path) -> dict[str, Any]:
    root, output = root.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(root / "results"):
        raise ValueError("fresh results-only output required")
    before = prerequisites(root)
    output.mkdir(parents=True)
    clean = root / "data/clean/v1_1"
    tasks = {
        r.task_id: r
        for r in (
            CleanPublicTask.model_validate_json(s)
            for s in (clean / "splits/dev.jsonl").read_text().splitlines()
        )
    }
    ids = json.loads((clean / "dev_pilot/task_ids.json").read_text())["task_ids"]
    references = {
        r["task_id"]: r
        for r in (
            json.loads(s)
            for s in (clean / "private/dev_ground_truth.jsonl").read_text().splitlines()
        )
    }
    if len(ids) != 21 or not set(ids) <= tasks.keys():
        raise ValueError("invalid preselected clean Dev IDs")
    catalog = environment_catalog(clean / "environment")
    checks = []
    for identity in ids:
        reference = references[identity]
        faults = [FaultSpec.model_validate(f) for f in reference["fault_plan"]]

        def factory(destination: Path, faults: list[FaultSpec] = faults) -> ToolRegistry:
            shutil.copytree(clean / "environment", destination)
            return build_clean_registry(destination, fault_plan=faults)

        responses = [
            action_response(Action(name=s["tool"], arguments=s["arguments"]))
            for s in reference["oracle_steps"]
        ] + [final_response()]
        check = compare(tasks[identity], responses, factory, output / identity, catalog=catalog)
        check.update(suite="clean_dev", audit=audit_trace(output / identity, catalog))
        checks.append(check)
    for row in select_dev(load_split(root / "data/adversarial/release_v2")):
        # Build one host inventory environment; never run tools outside Broker.
        inventory = output / (row.variant_id + "_inventory_env")
        row.registry(clean / "environment", inventory)
        selected_catalog = catalog_for(row, inventory)

        def dev_factory(destination: Path, row: ReleasedFixture = row) -> ToolRegistry:
            return row.registry(clean / "environment", destination)

        check = compare(
            row.task,
            [*(action_response(a) for a in trajectory(row)), final_response()],
            dev_factory,
            output / row.variant_id,
            catalog=selected_catalog,
            config=RuntimeConfig(max_steps=32),
            audit_profile="security_v1",
        )
        check.update(
            suite="deep_dev",
            variant_id=row.variant_id,
            branch=row.branch,
            source_type=row.overlay.source_type,
            linked_resources=bool(row.resources),
            audit=audit_trace(output / row.variant_id, selected_catalog, row),
        )
        checks.append(check)
    if len(checks) != 45 or any(c["status"] != "completed" for c in checks):
        raise ValueError("45 completed paired conditions required")
    if before != prerequisites(root):
        raise ValueError("frozen inputs changed")
    stable = [
        {k: v for k, v in c.items() if k not in {"legacy_seconds", "foundation_seconds"}}
        for c in checks
    ]
    return {
        "valid": True,
        "paired_conditions": 45,
        "fresh_replay_runs": 90,
        "clean_dev": 21,
        "deep_attack_benign_dev": 24,
        "test_payloads_parsed": 0,
        "real_model_runs": 0,
        "private_dev_use": "QA reference scripts only",
        "prerequisites": before,
        "checks": checks,
        "stable_summary_sha256": text_hash(json.dumps(stable, sort_keys=True, ensure_ascii=False)),
    }
