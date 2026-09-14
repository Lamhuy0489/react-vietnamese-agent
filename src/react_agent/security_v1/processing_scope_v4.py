"""Host-bound AWB/AUX document/page scope; frozen SQL v2 semantics retained."""

from __future__ import annotations

import re
from functools import partial
from types import FunctionType
from typing import Any, cast

from react_agent.foundation.artifacts import SourceType, Trust
from react_agent.schemas.agent_output import Action
from react_agent.security_v1 import processing_scope as base
from react_agent.security_v1.contracts import Effect, Reason
from react_agent.security_v1.processing_scope_v3 import ProcessingScope as V3Scope
from react_agent.security_v1.processing_scope_v3 import describe_action as legacy_description
from react_agent.security_v1.resource_bindings_v1 import EXTENSION_ID, ResourceBindings

PROFILE = "a4_processing_scope_v4"
_READ_RESULT = re.compile(r"\bcho\s+biết\b", re.IGNORECASE)


def describe_action(action: Action, *, resources: ResourceBindings) -> base.ActionScope:
    for tool, key, kind, identities in (
        ("doc_read", "doc_id", base.ScopeKind.DOCUMENT, resources.documents),
        ("cached_fetch", "page_id", base.ScopeKind.CACHED_PAGE, resources.cached_pages),
    ):
        target = action.arguments.get(key)
        if action.name == tool and isinstance(target, str) and target in identities:
            return base.ActionScope(
                kind=kind, assessed=action.arguments == {key: target}, resource_ids=(target,)
            )
    return legacy_description(action)


class ProcessingScope(V3Scope):
    def __init__(self, raw_user: str, *, resources: ResourceBindings, enforce: bool = True) -> None:
        super().__init__(raw_user, enforce=enforce)
        self.resources = resources
        if any(mark in raw_user for mark in ('"', "'", "`", "“", "”", ">")):
            return
        documents, pages = set(self.anchors.documents), set(self.anchors.cached_pages)
        for clause in re.split(r"[\n;.!?]", raw_user):
            if base._REJECT_CLAUSE.search(_READ_RESULT.sub("", clause)) or not (
                base._SCOPE_CUE.search(clause)
            ):
                continue
            # Do not strip slash, format characters or quote marks into valid identities.
            for token in clause.split():
                identity = token.strip(",:()[]")
                for tool, key, targets in (
                    ("doc_read", "doc_id", documents),
                    ("cached_fetch", "page_id", pages),
                ):
                    described = describe_action(
                        Action(name=tool, arguments={key: identity}), resources=resources
                    )
                    if described.assessed:
                        targets.add(identity)
        total = (
            len(documents)
            + len(pages)
            + len(self.anchors.database_tables)
            + len(self.anchors.database_columns)
        )
        if total > base.MAX_ANCHORS:
            raise base.ScopeError("scope anchor budget exceeded")
        self.anchors = self.anchors.model_copy(
            update={
                "documents": tuple(sorted(documents)),
                "cached_pages": tuple(sorted(pages)),
                "explicit_scope": bool(total),
            }
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            **super().snapshot(),
            "profile": PROFILE,
            "host_resources": self.resources.model_dump(mode="json"),
        }

    def _call(self, function: Any, *args: Any, **kwargs: Any) -> Any:
        namespace = dict(function.__globals__)
        namespace["describe_action"] = partial(describe_action, resources=self.resources)
        body = FunctionType(
            function.__code__,
            namespace,
            function.__name__,
            function.__defaults__,
            function.__closure__,
        )
        body.__kwdefaults__ = function.__kwdefaults__
        return body(self, *args, **kwargs)

    def pre(self, action: Action) -> base.ScopeDecision:
        if action.name not in {"doc_read", "cached_fetch"}:
            decision = super().pre(action)
        else:
            description = describe_action(action, resources=self.resources)
            decision = self._call(base.ProcessingScope.pre, action)
            if self.enforce and not description.assessed:
                decision = decision.model_copy(
                    update={
                        "effect": Effect.DENY,
                        "reasons": (Reason.CONTROL, Reason.UNKNOWN_FIELD),
                        "authorized_by": "unassessed_scope",
                    }
                )
            key = "doc_id" if action.name == "doc_read" else "page_id"
            target = action.arguments.get(key)
            if self.enforce and isinstance(target, str) and EXTENSION_ID.fullmatch(target):
                anchors = self.anchors.documents if key == "doc_id" else self.anchors.cached_pages
                if not description.assessed or target not in anchors:
                    decision = decision.model_copy(
                        update={
                            "effect": Effect.DENY,
                            "reasons": (Reason.CONTROL, Reason.ACTION),
                            "authorized_by": "missing_explicit_resource_anchor",
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
        if action.name not in {"doc_read", "cached_fetch"}:
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
        description = describe_action(action, resources=self.resources)
        if not description.assessed:
            raise base.ScopeError("unassessed resource cannot be admitted")
        identity = description.resource_ids[0]
        expected = SourceType.DOCUMENT if action.name == "doc_read" else SourceType.CACHED_PAGE
        if EXTENSION_ID.fullmatch(identity) and (
            (source_type, source_id) != (expected, identity)
            or self.pre(action).effect != Effect.ALLOW
        ):
            raise base.ScopeError("resource observation lacks matching host identity or grant")
        observed = self._call(
            base.ProcessingScope.observe,
            action,
            artifact_id=artifact_id,
            source_type=source_type,
            source_id=source_id,
            trust=trust,
        )
        return cast(base.ScopeObservation, observed.model_copy(update={"profile": PROFILE}))
