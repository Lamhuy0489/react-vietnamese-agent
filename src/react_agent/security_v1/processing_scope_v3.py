"""Bounded clean-document identifiers, retaining v2 table/column isolation.

Only the documented CDOC namespace is added. Identifiers are never rewritten
or aliased, and source labels still come from the independent host catalog.
"""

from __future__ import annotations

import re
from types import FunctionType
from typing import Any, cast

from react_agent.foundation.artifacts import SourceType, Trust
from react_agent.schemas.agent_output import Action
from react_agent.security_v1 import processing_scope as base
from react_agent.security_v1.processing_scope_v2 import ProcessingScope as V2Scope

PROFILE = "a4_processing_scope_v3"
_CLEAN_DOC = re.compile(r"\bCDOC_[A-Za-z0-9][A-Za-z0-9_-]{0,63}\b")


def describe_action(action: Action) -> base.ActionScope:
    scope = base.describe_action(action)
    target = action.arguments.get("doc_id")
    if action.name == "doc_read" and isinstance(target, str) and _CLEAN_DOC.fullmatch(target):
        return base.ActionScope(kind=base.ScopeKind.DOCUMENT, assessed=True, resource_ids=(target,))
    return scope


def _body(function: Any) -> Any:
    namespace = dict(function.__globals__)
    namespace["describe_action"] = describe_action
    body = FunctionType(
        function.__code__, namespace, function.__name__, function.__defaults__, function.__closure__
    )
    body.__kwdefaults__ = function.__kwdefaults__
    return body


class ProcessingScope(V2Scope):
    def __init__(self, raw_user: str, *, enforce: bool = True) -> None:
        super().__init__(raw_user, enforce=enforce)
        # Match v2's whole-input quoted/indirect authorization rejection.
        if any(c in raw_user for c in ('"', "'", "`", "“", "”", ">")):
            return
        documents = set(self.anchors.documents)
        for clause in re.split(r"[\n;.!?]", raw_user):
            if base._REJECT_CLAUSE.search(clause) or not base._SCOPE_CUE.search(clause):
                continue
            documents.update(_CLEAN_DOC.findall(clause))
        total = len(documents) + sum(
            len(getattr(self.anchors, field))
            for field in ("cached_pages", "database_tables", "database_columns")
        )
        if total > base.MAX_ANCHORS:
            raise base.ScopeError("scope anchor budget exceeded")
        self.anchors = self.anchors.model_copy(
            update={"documents": tuple(sorted(documents)), "explicit_scope": bool(total)}
        )

    def snapshot(self) -> dict[str, Any]:
        return {**super().snapshot(), "profile": PROFILE}

    def pre(self, action: Action) -> base.ScopeDecision:
        decision = (
            _body(base.ProcessingScope.pre)(self, action)
            if action.name == "doc_read"
            else super().pre(action)
        )
        return cast(
            base.ScopeDecision,
            decision.model_copy(update={"profile": PROFILE, "component": PROFILE}),
        )

    def observe(
        self,
        action: Action,
        *,
        artifact_id: str,
        source_type: SourceType,
        source_id: str | None,
        trust: Trust,
    ) -> base.ScopeObservation:
        if action.name != "doc_read":
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
        if not describe_action(action).assessed:
            raise base.ScopeError("unassessed resource cannot be admitted")
        observed = _body(base.ProcessingScope.observe)(
            self,
            action,
            artifact_id=artifact_id,
            source_type=source_type,
            source_id=source_id,
            trust=trust,
        )
        return cast(base.ScopeObservation, observed.model_copy(update={"profile": PROFILE}))
