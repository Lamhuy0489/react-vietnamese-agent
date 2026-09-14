"""Pinned public Dev inputs and host catalog; no evaluator or private loader."""

from __future__ import annotations

import hashlib
from pathlib import Path

from react_agent.adversarial_release import ReleasedFixture, load_split
from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.llm.agent_mount_v1 import no_links
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.validation.grouped_dev_plan_v1 import DEV_SHA256, plan


def selected_fixtures(release: Path) -> tuple[ReleasedFixture, ...]:
    schedule = plan(release)
    rows = {row.variant_id: row for row in load_split(release)}
    selected = []
    for pair in schedule["selected_pairs"]:
        for branch in ("attack", "benign"):
            meta = pair[branch]
            row = rows[meta["variant_id"]]
            if any(getattr(row, key) != value for key, value in meta.items()):
                raise ValueError("selected public fixture scheduling identity mismatch")
            selected.append(row)
    for name, expected in DEV_SHA256.items():
        path = release / name
        no_links(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Dev input changed during load")
    return tuple(selected)


def fixture_catalog(row: ReleasedFixture) -> SourceCatalog:
    # Revalidate mutable public fixtures; caller changes cannot bypass schema checks.
    row = ReleasedFixture.model_validate(row.model_dump(mode="json"))
    if row.split != "dev":
        raise ValueError("only public Dev fixtures are in scope")
    source_type = {
        "document": SourceType.DOCUMENT,
        "cached_page": SourceType.CACHED_PAGE,
        "database_text_field": SourceType.DATABASE,
        "tool_output": SourceType.CALCULATOR,
    }[row.overlay.source_type]
    bindings = [
        SourceBinding(
            tool=row.overlay.trigger.name,
            arguments_json=canonical_json(row.overlay.trigger.arguments),
            label=SourceLabel(
                source_type=source_type,
                source_id=row.overlay.source_id,
                sensitivity=Sensitivity(row.overlay.sensitivity),
                trust=Trust.TRUSTED if row.overlay.trust == "T0" else Trust.UNTRUSTED,
                legacy_trust=row.overlay.trust,
            ),
        )
    ]
    if row.resources is not None:
        for additions, tool, key, kind in (
            (row.resources.documents, "doc_read", "doc_id", SourceType.DOCUMENT),
            (row.resources.cached_pages, "cached_fetch", "page_id", SourceType.CACHED_PAGE),
        ):
            for item in additions:
                bindings.append(
                    SourceBinding(
                        tool=tool,
                        arguments_json=canonical_json({key: item.identity}),
                        label=SourceLabel(
                            source_type=kind,
                            source_id=item.identity,
                            sensitivity=Sensitivity.CONFIDENTIAL,
                            trust=Trust.UNTRUSTED,
                        ),
                    )
                )
    catalog = SourceCatalog(bindings=tuple(bindings))
    ResourceBindings.from_catalog(catalog)
    return catalog
