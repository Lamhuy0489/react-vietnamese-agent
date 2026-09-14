"""Finite row-and-column SQL authorization composed with frozen v4 resources."""

from __future__ import annotations

import re
from typing import Any

from react_agent.foundation.artifacts import SourceType, Trust
from react_agent.schemas.agent_output import Action
from react_agent.security_v1 import processing_scope as base
from react_agent.security_v1.contracts import Effect, Reason
from react_agent.security_v1.processing_scope_v4 import ProcessingScope as V4Scope
from react_agent.security_v1.processing_scope_v4 import describe_action as v4_description
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.security_v1.sql_rows_v1 import IDENT, RowBindings, RowSelection, parse_rows

PROFILE = "a4_processing_scope_v5"
_READ = re.compile(r"\b(?:đọc|tra|truy\s+vấn|read|query)\b", re.IGNORECASE)
_COLUMN = re.compile(rf"\b(?:cột|column|trường|field)\s+({IDENT})\b", re.IGNORECASE)
_LIST = re.compile(
    rf"^\s*(?:đọc|read)\s+(?P<names>{IDENT}(?:\s*(?:,|và|and)\s+{IDENT})*)\s+(?:của|of)\b",
    re.IGNORECASE,
)


def describe_action(action: Action, *, resources: ResourceBindings) -> base.ActionScope:
    selection = parse_rows(action.arguments.get("query")) if action.name == "db_query" else None
    if selection is not None and set(action.arguments) == {"query"}:
        return base.ActionScope(
            kind=base.ScopeKind.DATABASE,
            assessed=True,
            table=selection.table,
            columns=selection.accessed_columns,
            resource_ids=selection.values,
        )
    return v4_description(action, resources=resources)


class ProcessingScope(V4Scope):
    def __init__(
        self, raw_user: str, *, resources: ResourceBindings, rows: RowBindings, enforce: bool = True
    ) -> None:
        super().__init__(raw_user, resources=resources, enforce=enforce)
        self.rows = rows
        self.row_grants: set[tuple[str, str, str, str]] = set()
        self.row_observations: list[RowSelection] = []
        if any(mark in raw_user for mark in ('"', "'", "`", "“", "”", ">")):
            return
        for clause in re.split(r"[\n;.!?]", raw_user):
            if base._REJECT_CLAUSE.search(clause) or not _READ.search(clause):
                continue
            tokens = {token.strip(",:()[]") for token in clause.split()}
            bindings = [row for row in rows.rows if row.value in tokens]
            if len(bindings) != 1:
                continue
            row = bindings[0]
            tables = {m.group(1).casefold() for m in base._TABLE_CUE.finditer(clause)}
            tables.update(
                m.group(1).casefold()
                for m in re.finditer(rf"\b(?:trong|in)\s+({IDENT})\b", clause, re.IGNORECASE)
            )
            if tables and tables != {row.table}:
                continue
            source_tokens = [
                t
                for t in tokens
                if re.search(r"(?:AWB|AUX|DOC|CDOC|CACHE)_", t, re.IGNORECASE)
                and t.casefold() not in tables
            ]
            if source_tokens != [row.value]:
                continue
            columns = {m.group(1).casefold() for m in _COLUMN.finditer(clause)}
            names = _LIST.match(clause)
            if names:
                columns.update(re.split(r"\s*(?:,|\bvà\b|\band\b)\s*", names["names"].casefold()))
            self.row_grants.update((row.table, row.key, row.value, column) for column in columns)
        if len(self.row_grants) > base.MAX_ANCHORS:
            raise base.ScopeError("SQL row grant budget exceeded")

    def snapshot(self) -> dict[str, Any]:
        return {
            **super().snapshot(),
            "profile": PROFILE,
            "host_rows": self.rows.model_dump(mode="json"),
            "row_grants": [list(g) for g in sorted(self.row_grants)],
            "row_observations": [row.model_dump(mode="json") for row in self.row_observations],
        }

    def _allowed(self, selection: RowSelection) -> bool:
        inventory = {(row.table, row.key, row.value) for row in self.rows.rows}
        return all(
            (selection.table, selection.key, value) in inventory
            and all(
                (selection.table, selection.key, value, column) in self.row_grants
                for column in selection.columns
            )
            for value in selection.values
        )

    def pre(self, action: Action) -> base.ScopeDecision:
        decision = super().pre(action)
        if action.name == "db_query" and self.enforce:
            selection = parse_rows(action.arguments.get("query"))
            # Preserve legacy unfiltered SQL only outside a row-bound environment.
            if self.rows.rows or selection is not None or not base.describe_action(action).assessed:
                allowed = (
                    selection is not None
                    and set(action.arguments) == {"query"}
                    and self._allowed(selection)
                )
                decision = decision.model_copy(
                    update={
                        "effect": Effect.ALLOW if allowed else Effect.DENY,
                        "reasons": (Reason.PASS,) if allowed else (Reason.CONTROL, Reason.ACTION),
                        "authorized_by": "bound_row_columns"
                        if allowed
                        else "row_column_scope_denial",
                        "table": selection.table if selection else None,
                        "columns": selection.accessed_columns if selection else (),
                        "resource_ids": selection.values if selection else (),
                    }
                )
        return decision.model_copy(update={"profile": PROFILE, "component": PROFILE})

    def observe(
        self,
        action: Action,
        *,
        artifact_id: str,
        source_type: SourceType,
        source_id: str | None,
        trust: Trust,
    ) -> base.ScopeObservation:
        selection = parse_rows(action.arguments.get("query")) if action.name == "db_query" else None
        if action.name == "db_query" and (self.rows.rows or selection is not None):
            if (
                selection is None
                or source_type != SourceType.DATABASE
                or self.pre(action).effect != Effect.ALLOW
                or not artifact_id
            ):
                raise base.ScopeError("SQL observation lacks supported granted row scope")
            # Reuse the public base state shape without granting prior-observation expansion.
            observation = super().observe(
                action,
                artifact_id=artifact_id,
                source_type=source_type,
                source_id=source_id,
                trust=trust,
            )
            self.row_observations.append(selection)
            return observation.model_copy(
                update={
                    "profile": PROFILE,
                    "action_scope": describe_action(action, resources=self.resources),
                }
            )
        return (
            super()
            .observe(
                action,
                artifact_id=artifact_id,
                source_type=source_type,
                source_id=source_id,
                trust=trust,
            )
            .model_copy(update={"profile": PROFILE})
        )
