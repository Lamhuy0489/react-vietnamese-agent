"""Versioned A4 scope with table/column pairs instead of Cartesian grants."""

from __future__ import annotations

import re
from typing import Any

from react_agent.foundation.artifacts import SourceType, Trust
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import Effect, Reason
from react_agent.security_v1.processing_scope import (
    _COLUMN_CUE,
    _REJECT_CLAUSE,
    _SCOPE_CUE,
    _TABLE_CUE,
    ScopeDecision,
    ScopeError,
    ScopeKind,
    ScopeObservation,
    describe_action,
)
from react_agent.security_v1.processing_scope import (
    ProcessingScope as LegacyScope,
)

PROFILE = "a4_processing_scope_v2"


class ProcessingScope(LegacyScope):
    def __init__(self, raw_user: str, *, enforce: bool = True) -> None:
        super().__init__(raw_user, enforce=enforce)
        quoted = any(c in raw_user for c in ('"', "'", "`", "“", "”", ">"))
        if quoted:
            self.anchors = self.anchors.model_copy(
                update={
                    "documents": (),
                    "cached_pages": (),
                    "database_tables": (),
                    "database_columns": (),
                    "explicit_scope": False,
                }
            )
        self.database_grants: set[tuple[str, str]] = set()
        self.observed_database_pairs: set[tuple[str, str]] = set()
        for clause in [] if quoted else re.split(r"[\n;.!?]", raw_user):
            if _REJECT_CLAUSE.search(clause) or not _SCOPE_CUE.search(clause):
                continue
            tables = {m.group(1).casefold() for m in _TABLE_CUE.finditer(clause)}
            columns = {m.group(1).casefold() for m in _COLUMN_CUE.finditer(clause)}
            if len(tables) == 1:
                self.database_grants.update((next(iter(tables)), col) for col in columns)

    def snapshot(self) -> dict[str, Any]:
        return {
            **super().snapshot(),
            "profile": PROFILE,
            "database_grants": [list(pair) for pair in sorted(self.database_grants)],
            "observed_database_pairs": [
                list(pair) for pair in sorted(self.observed_database_pairs)
            ],
        }

    def pre(self, action: Action) -> ScopeDecision:
        base = super().pre(action).model_copy(update={"profile": PROFILE, "component": PROFILE})
        scope = describe_action(action)
        if not self.enforce or scope.kind != ScopeKind.DATABASE:
            return base
        if not (self.anchors.explicit_scope or self.state.untrusted_seen):
            return base
        pairs = (
            self.database_grants if self.anchors.explicit_scope else self.observed_database_pairs
        )
        allowed = (
            scope.assessed
            and scope.table is not None
            and bool(scope.columns)
            and all((scope.table, column) in pairs for column in scope.columns)
        )
        return base.model_copy(
            update={
                "effect": Effect.ALLOW if allowed else Effect.DENY,
                "reasons": (Reason.PASS,) if allowed else (Reason.CONTROL, Reason.ACTION),
                "authorized_by": "bound_table_columns" if allowed else "table_column_scope_denial",
            }
        )

    def observe(
        self,
        action: Action,
        *,
        artifact_id: str,
        source_type: SourceType,
        source_id: str | None,
        trust: Trust,
    ) -> ScopeObservation:
        scope = describe_action(action)
        if scope.kind in {ScopeKind.DOCUMENT, ScopeKind.CACHED_PAGE} and not scope.assessed:
            raise ScopeError("unassessed resource cannot be admitted")
        observation = super().observe(
            action,
            artifact_id=artifact_id,
            source_type=source_type,
            source_id=source_id,
            trust=trust,
        )
        if scope.assessed and scope.table is not None:
            self.observed_database_pairs.update((scope.table, column) for column in scope.columns)
        return observation.model_copy(update={"profile": PROFILE})
