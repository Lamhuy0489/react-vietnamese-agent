"""Bounded host-owned A4 processing-scope control.

This component protects a user-declared resource boundary after an untrusted
source has been observed.  It is deliberately separate from the frozen A3--A5
session policy: callers can compose the decision without changing the old
runtime or treating evaluator annotations as authorization.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import Field

from react_agent.foundation.artifacts import Immutable, SourceType, Trust, canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import Effect, Reason

PROFILE = "a4_processing_scope_v1"
MAX_USER_BYTES = 131_072
MAX_ANCHORS = 256
MAX_QUERY_CHARS = 2_000

_RESOURCE_ID = re.compile(r"\b(?:DOC|CACHE)_[A-Za-z0-9][A-Za-z0-9_-]{0,63}\b")
_SCOPE_CUE = re.compile(
    r"\b(?:đọc|xem|tra\s+cứu|tóm\s+tắt|truy\s+vấn|read|fetch|lookup|review|query|"
    r"document|tài\s+liệu|trang|page|search|tìm)\b",
    re.IGNORECASE,
)
_REJECT_CLAUSE = re.compile(
    r"\b(?:không|khong|đừng|dung|chớ|cho|nếu|neu|nếu\s+cần|if|not|never|unless|"
    r"ignore|bỏ\s+qua|bo\s+qua)\b",
    re.IGNORECASE,
)
_TABLE_CUE = re.compile(
    r"\b(?:table|bảng)\s*[:#]?\s*([A-Za-z_][A-Za-z0-9_]*)\b", re.IGNORECASE
)
_COLUMN_CUE = re.compile(
    r"\b(?:column|cột)\s*[:#]?\s*([A-Za-z_][A-Za-z0-9_]*)\b", re.IGNORECASE
)
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_SQL = re.compile(
    r"\A\s*SELECT\s+(.+?)\s+FROM\s+([A-Za-z_][A-Za-z0-9_]*)\s*\Z", re.IGNORECASE
)


class ScopeError(ValueError):
    """Sanitized scope-integrity error; source text is never included."""


class ScopeKind(StrEnum):
    DOCUMENT = "DOCUMENT"
    CACHED_PAGE = "CACHED_PAGE"
    DATABASE = "DATABASE"
    SEARCH = "SEARCH"
    CALCULATOR = "CALCULATOR"
    EXTERNAL = "EXTERNAL"
    UNKNOWN = "UNKNOWN"


class ActionScope(Immutable):
    kind: ScopeKind
    assessed: bool
    resource_ids: tuple[str, ...] = ()
    table: str | None = None
    columns: tuple[str, ...] = ()


class ScopeAnchors(Immutable):
    documents: tuple[str, ...] = ()
    cached_pages: tuple[str, ...] = ()
    database_tables: tuple[str, ...] = ()
    database_columns: tuple[str, ...] = ()
    explicit_scope: bool = False
    raw_user_sha256: str = Field(min_length=64, max_length=64)


class ScopeState(Immutable):
    untrusted_seen: bool = False
    observed_artifact_ids: tuple[str, ...] = ()
    observed_resource_ids: tuple[str, ...] = ()
    observed_database_tables: tuple[str, ...] = ()
    observed_database_columns: tuple[str, ...] = ()
    untrusted_artifact_ids: tuple[str, ...] = ()
    observation_count: int = Field(default=0, ge=0, strict=True)


class ScopeObservation(Immutable):
    profile: str = PROFILE
    artifact_id: str = Field(min_length=1)
    source_type: SourceType
    source_id: str | None = None
    trust: Trust
    action_scope: ActionScope


class ScopeDecision(Immutable):
    profile: str = PROFILE
    effect: Effect
    reasons: tuple[Reason, ...] = Field(min_length=1)
    component: str = PROFILE
    action_name: str = Field(min_length=1)
    scope_kind: ScopeKind
    authorized_by: str = Field(min_length=1)
    resource_ids: tuple[str, ...] = ()
    table: str | None = None
    columns: tuple[str, ...] = ()


def _append(values: tuple[str, ...], additions: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*values, *additions)))


def _bounded_identifier(value: str) -> bool:
    return bool(_IDENTIFIER.fullmatch(value)) and len(value) <= 64


def extract_scope_anchors(raw_user: str) -> ScopeAnchors:
    """Extract exact resource/table anchors from affirmative user clauses only."""

    if not isinstance(raw_user, str) or not raw_user.strip():
        raise ScopeError("non-empty raw user instruction required")
    if len(raw_user.encode("utf-8")) > MAX_USER_BYTES:
        raise ScopeError("raw user instruction exceeds scope budget")
    documents: set[str] = set()
    cached_pages: set[str] = set()
    database_tables: set[str] = set()
    database_columns: set[str] = set()
    for clause in re.split(r"[\n;.!?]", raw_user):
        if _REJECT_CLAUSE.search(clause) or not _SCOPE_CUE.search(clause):
            continue
        # Quoted/indirect text is not a host authorization instruction.
        if any(mark in clause for mark in ('"', "'", "`", "“", "”", ">")):
            continue
        for identity in _RESOURCE_ID.findall(clause):
            (documents if identity.startswith("DOC_") else cached_pages).add(identity)
        database_tables.update(match.group(1).casefold() for match in _TABLE_CUE.finditer(clause))
        database_columns.update(match.group(1).casefold() for match in _COLUMN_CUE.finditer(clause))
    total = len(documents) + len(cached_pages) + len(database_tables) + len(database_columns)
    if total > MAX_ANCHORS:
        raise ScopeError("scope anchor budget exceeded")
    return ScopeAnchors(
        documents=tuple(sorted(documents)),
        cached_pages=tuple(sorted(cached_pages)),
        database_tables=tuple(sorted(database_tables)),
        database_columns=tuple(sorted(database_columns)),
        explicit_scope=bool(total),
        raw_user_sha256=text_hash(raw_user),
    )


def parse_sql_scope(query: object) -> ActionScope:
    """Parse one deliberately small SELECT shape without executing SQL."""

    if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY_CHARS:
        return ActionScope(kind=ScopeKind.DATABASE, assessed=False)
    if any(marker in query for marker in (";", "--", "/*", "*/", "\\x00")):
        return ActionScope(kind=ScopeKind.DATABASE, assessed=False)
    match = _SQL.fullmatch(query)
    if match is None:
        return ActionScope(kind=ScopeKind.DATABASE, assessed=False)
    raw_columns, table = match.groups()
    columns = tuple(part.strip().casefold() for part in raw_columns.split(","))
    if not columns or any(not _bounded_identifier(column) for column in columns):
        return ActionScope(kind=ScopeKind.DATABASE, assessed=False)
    normalized_table = table.casefold()
    return ActionScope(
        kind=ScopeKind.DATABASE,
        assessed=True,
        table=normalized_table,
        columns=tuple(dict.fromkeys(columns)),
    )


def describe_action(action: Action) -> ActionScope:
    """Return a non-executing, conservative scope description for a fixed action."""

    if not isinstance(action, Action):
        raise ScopeError("typed action required")
    arguments: dict[str, Any] = action.arguments
    if action.name == "doc_read":
        target = arguments.get("doc_id")
        target_id = target if isinstance(target, str) else None
        valid = target_id is not None and bool(
            re.fullmatch(r"DOC_[A-Za-z0-9][A-Za-z0-9_-]{0,63}", target_id)
        )
        return ActionScope(
            kind=ScopeKind.DOCUMENT,
            assessed=valid,
            resource_ids=(target_id,) if valid and target_id is not None else (),
        )
    if action.name == "cached_fetch":
        target = arguments.get("page_id")
        target_id = target if isinstance(target, str) else None
        valid = target_id is not None and bool(
            re.fullmatch(r"CACHE_[A-Za-z0-9][A-Za-z0-9_-]{0,63}", target_id)
        )
        return ActionScope(
            kind=ScopeKind.CACHED_PAGE,
            assessed=valid,
            resource_ids=(target_id,) if valid and target_id is not None else (),
        )
    if action.name in {"doc_search", "cached_search"}:
        # A search can fan out to resources not named in its arguments; it is
        # therefore intentionally unassessed by this finite scope profile.
        return ActionScope(kind=ScopeKind.SEARCH, assessed=False)
    if action.name == "db_query":
        return parse_sql_scope(arguments.get("query"))
    if action.name == "calculator":
        return ActionScope(kind=ScopeKind.CALCULATOR, assessed=True)
    if action.name in {"send_email_mock", "post_webhook_mock"}:
        return ActionScope(kind=ScopeKind.EXTERNAL, assessed=True)
    return ActionScope(kind=ScopeKind.UNKNOWN, assessed=False)


class ProcessingScope:
    """Run-local A4 scope state; callers must create one instance per task."""

    def __init__(self, raw_user: str, *, enforce: bool = True) -> None:
        if type(enforce) is not bool:
            raise ScopeError("enforce must be boolean")
        self.anchors = extract_scope_anchors(raw_user)
        self.enforce = enforce
        self.state = ScopeState()

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.snapshot()))

    def snapshot(self) -> dict[str, Any]:
        return {
            "profile": PROFILE,
            "enforce": self.enforce,
            "anchors": self.anchors.model_dump(mode="json"),
            "state": self.state.model_dump(mode="json"),
        }

    def observe(
        self,
        action: Action,
        *,
        artifact_id: str,
        source_type: SourceType,
        source_id: str | None,
        trust: Trust,
    ) -> ScopeObservation:
        if not artifact_id:
            raise ScopeError("source artifact identity required")
        scope = describe_action(action)
        if (
            scope.kind == ScopeKind.DOCUMENT
            and source_id is not None
            and source_id != scope.resource_ids[0]
        ):
            raise ScopeError("document source identity differs from action scope")
        if (
            scope.kind == ScopeKind.CACHED_PAGE
            and source_id is not None
            and source_id != scope.resource_ids[0]
        ):
            raise ScopeError("cached source identity differs from action scope")
        resource_ids = scope.resource_ids if scope.assessed else ()
        tables = (scope.table,) if scope.assessed and scope.table is not None else ()
        columns = scope.columns if scope.assessed else ()
        untrusted = trust == Trust.UNTRUSTED
        self.state = self.state.model_copy(
            update={
                "untrusted_seen": self.state.untrusted_seen or untrusted,
                "observed_artifact_ids": _append(self.state.observed_artifact_ids, (artifact_id,)),
                "observed_resource_ids": _append(self.state.observed_resource_ids, resource_ids),
                "observed_database_tables": _append(
                    self.state.observed_database_tables, tuple(tables)
                ),
                "observed_database_columns": _append(
                    self.state.observed_database_columns, columns
                ),
                "untrusted_artifact_ids": _append(
                    self.state.untrusted_artifact_ids, (artifact_id,) if untrusted else ()
                ),
                "observation_count": self.state.observation_count + 1,
            }
        )
        return ScopeObservation(
            artifact_id=artifact_id,
            source_type=source_type,
            source_id=source_id,
            trust=trust,
            action_scope=scope,
        )

    @staticmethod
    def _decision(
        action: Action,
        scope: ActionScope,
        effect: Effect,
        reasons: tuple[Reason, ...],
        authorized_by: str,
    ) -> ScopeDecision:
        return ScopeDecision(
            effect=effect,
            reasons=reasons,
            action_name=action.name,
            scope_kind=scope.kind,
            authorized_by=authorized_by,
            resource_ids=scope.resource_ids,
            table=scope.table,
            columns=scope.columns,
        )

    def pre(self, action: Action) -> ScopeDecision:
        scope = describe_action(action)
        if not self.enforce:
            return self._decision(action, scope, Effect.ALLOW, (Reason.PASS,), "not_enforced")
        if scope.kind in {ScopeKind.EXTERNAL, ScopeKind.CALCULATOR}:
            # External destination and payload policy is a separate A4/A6 gate.
            return self._decision(action, scope, Effect.ALLOW, (Reason.PASS,), "delegated")
        if scope.kind == ScopeKind.UNKNOWN:
            return self._decision(
                action,
                scope,
                Effect.DENY,
                (Reason.ACTION, Reason.UNKNOWN_FIELD),
                "unknown_action",
            )
        trigger = self.anchors.explicit_scope or self.state.untrusted_seen
        if not trigger:
            return self._decision(action, scope, Effect.ALLOW, (Reason.PASS,), "no_scope_trigger")
        if not scope.assessed:
            return self._decision(
                action,
                scope,
                Effect.DENY,
                (Reason.CONTROL, Reason.UNKNOWN_FIELD),
                "unassessed_scope",
            )
        if self.anchors.explicit_scope:
            if scope.kind == ScopeKind.DOCUMENT and set(scope.resource_ids) <= set(
                self.anchors.documents
            ):
                return self._decision(
                    action, scope, Effect.ALLOW, (Reason.PASS,), "raw_user_anchor"
                )
            if scope.kind == ScopeKind.CACHED_PAGE and set(scope.resource_ids) <= set(
                self.anchors.cached_pages
            ):
                return self._decision(
                    action, scope, Effect.ALLOW, (Reason.PASS,), "raw_user_anchor"
                )
            if scope.kind == ScopeKind.DATABASE and self._database_allowed(
                scope, self.anchors.database_tables, self.anchors.database_columns
            ):
                return self._decision(
                    action, scope, Effect.ALLOW, (Reason.PASS,), "raw_user_anchor"
                )
            return self._decision(
                action,
                scope,
                Effect.DENY,
                (Reason.CONTROL, Reason.ACTION),
                "scope_expansion",
            )
        if scope.kind in {ScopeKind.DOCUMENT, ScopeKind.CACHED_PAGE} and set(
            scope.resource_ids
        ) <= set(self.state.observed_resource_ids):
            return self._decision(action, scope, Effect.ALLOW, (Reason.PASS,), "prior_observation")
        if scope.kind == ScopeKind.DATABASE and self._database_allowed(
            scope, self.state.observed_database_tables, self.state.observed_database_columns
        ):
            return self._decision(action, scope, Effect.ALLOW, (Reason.PASS,), "prior_observation")
        return self._decision(
            action,
            scope,
            Effect.DENY,
            (Reason.CONTROL, Reason.ACTION),
            "untrusted_scope_expansion",
        )

    @staticmethod
    def _database_allowed(
        scope: ActionScope, tables: tuple[str, ...], columns: tuple[str, ...]
    ) -> bool:
        return bool(
            scope.assessed
            and scope.table is not None
            and scope.table in set(tables)
            and set(scope.columns) <= set(columns)
        )
