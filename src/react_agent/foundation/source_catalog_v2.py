"""Host-only source metadata, with conservative collection/search envelopes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Self

from pydantic import model_validator

from react_agent.foundation.artifacts import (
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
    join_sensitivity,
    join_trust,
)
from react_agent.foundation.normalization import text_hash
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.schemas.agent_output import Action


class EnvironmentCatalog(SourceCatalog):
    version: str = "environment_source_catalog_v2"
    sources: tuple[SourceLabel, ...] = ()
    environment_sha256: str

    @model_validator(mode="after")
    def unique_sources(self) -> Self:
        keys = [(s.source_type, s.source_id) for s in self.sources]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate host source identity")
        return self

    def envelope(self, source_type: SourceType) -> SourceLabel:
        members = tuple(s for s in self.sources if s.source_type == source_type)
        default_s = Sensitivity.CONFIDENTIAL
        default_t = Trust.TRUSTED if source_type == SourceType.DATABASE else Trust.UNTRUSTED
        return SourceLabel(
            source_type=source_type,
            source_id="collection:"
            + source_type.value
            + ":"
            + text_hash(canonical_json([s.model_dump(mode="json") for s in members])),
            sensitivity=join_sensitivity(*(s.sensitivity for s in members))
            if members
            else default_s,
            trust=join_trust(*(s.trust for s in members)) if members else default_t,
        )

    def resolve(self, action: Action) -> SourceLabel:
        # The DB adapter is not a SQL-policy parser: join the whole DB scope even
        # for an exact trigger binding. A projection cannot silently upgrade trust.
        if action.name == "db_query":
            return self.envelope(SourceType.DATABASE)
        for tool, source_type in (
            ("doc_search", SourceType.DOCUMENT),
            ("cached_search", SourceType.CACHED_PAGE),
        ):
            if action.name == tool:
                return self.envelope(source_type)
        for tool, key, source_type in (
            ("doc_read", "doc_id", SourceType.DOCUMENT),
            ("cached_fetch", "page_id", SourceType.CACHED_PAGE),
        ):
            if action.name == tool:
                for source in self.sources:
                    if (
                        source.source_type == source_type
                        and source.source_id == action.arguments.get(key)
                    ):
                        return source
        return super().resolve(action)


def environment_catalog(
    environment: Path,
    *,
    overrides: tuple[SourceLabel, ...] = (),
    bindings: tuple[SourceBinding, ...] = (),
) -> EnvironmentCatalog:
    """Read only host environment inventories; never catalog facts or evaluator GT.

    Caller supplies explicit source labels for overlays. Unknown auxiliary IDs
    receive S2/UNTRUSTED regardless of content or presence of secret-like text.
    """
    known: dict[tuple[SourceType, str], SourceLabel] = {}
    hashes = {}
    for relative, key, source_type, prefix, sensitivity, trust in (
        (
            "documents/documents.json",
            "doc_id",
            SourceType.DOCUMENT,
            "CDOC_",
            Sensitivity.INTERNAL,
            Trust.TRUSTED,
        ),
        (
            "cached_pages/pages.json",
            "page_id",
            SourceType.CACHED_PAGE,
            "CPAGE_",
            Sensitivity.PUBLIC,
            Trust.UNTRUSTED,
        ),
    ):
        payload = (environment / relative).read_bytes()
        hashes[relative] = text_hash(payload.decode("utf-8"))
        for row in json.loads(payload):
            identity = row[key]
            trusted_namespace = identity.startswith(prefix)
            label = SourceLabel(
                source_type=source_type,
                source_id=identity,
                sensitivity=sensitivity if trusted_namespace else Sensitivity.CONFIDENTIAL,
                trust=trust if trusted_namespace else Trust.UNTRUSTED,
            )
            if (source_type, identity) in known:
                raise ValueError("duplicate source in environment inventory")
            known[source_type, identity] = label
    import hashlib

    hashes["database/university.db"] = hashlib.sha256(
        (environment / "database/university.db").read_bytes()
    ).hexdigest()
    database = SourceLabel(
        source_type=SourceType.DATABASE,
        source_id="database:all_tables",
        sensitivity=Sensitivity.CONFIDENTIAL,
        trust=Trust.TRUSTED,
    )
    known[database.source_type, database.source_id] = database
    seen: set[tuple[SourceType, str]] = set()
    for label in overrides:
        key_pair = label.source_type, label.source_id
        if key_pair in seen:
            raise ValueError("duplicate source override")
        seen.add(key_pair)
        if (
            label.source_type in {SourceType.DOCUMENT, SourceType.CACHED_PAGE}
            and key_pair not in known
        ):
            raise ValueError("override source absent from environment")
        known[key_pair] = label
    return EnvironmentCatalog(
        sources=tuple(known[k] for k in sorted(known)),
        bindings=bindings,
        environment_sha256=text_hash(canonical_json(hashes)),
    )
