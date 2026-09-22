"""Opt-in cumulative clause authorization; preserve frozen v10 and raw A0."""

from __future__ import annotations

import json
from dataclasses import asdict
from functools import partial
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.a2_policy import A2Policy
from react_agent.security_v1.a6_policy import A6Policy
from react_agent.security_v1.authorization_anchors_v3 import audit_anchors, extract_anchors
from react_agent.security_v1.contracts import SecurityConfig, configuration
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.processing_scope_v5 import PROFILE as SCOPE_PROFILE
from react_agent.security_v1.processing_scope_v5 import ProcessingScope, describe_action
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_policy import RuntimePolicy
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v7 import SecurityRuntime as V7Runtime
from react_agent.security_v1.runtime_v10 import SecurityRuntime as V10Runtime
from react_agent.security_v1.session_policy import SessionPolicy
from react_agent.security_v1.sql_rows_v1 import RowBindings
from react_agent.security_v1.value_gates import value_pre_check
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex

RUNTIME_VERSION = "security_runtime_v12_clause_candidate"


class ClauseRuntimePolicy(RuntimePolicy):
    def __init__(self, config: SecurityConfig, raw_user: str) -> None:
        super().__init__(config, raw_user)
        self.component.anchors = extract_anchors(raw_user)


class ClauseA2Policy(A2Policy, ClauseRuntimePolicy):
    """A2's super initializes clause anchors; preserve isinstance checks."""


class ClauseSessionPolicy(SessionPolicy, ClauseA2Policy):
    """A3–A5 inherit the identical A1 destination parser."""


class ClauseA6Policy(A6Policy, ClauseSessionPolicy):
    def pre_bound(self, *args: Any, **kwargs: Any) -> Any:
        check = bind(value_pre_check, extract_anchors=extract_anchors)
        return bind(A6Policy.pre_bound, value_pre_check=check)(self, *args, **kwargs)


class SecurityRuntime(V10Runtime):
    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        security = kwargs.get("security_config") or configuration("A0")
        if security.level == "A0":
            return super()._run_task(task, **kwargs)
        catalog = kwargs.get("source_catalog") or SourceCatalog()
        resources = ResourceBindings.from_catalog(catalog)
        rows = RowBindings.from_catalog(catalog)
        inner = bind(
            V5Runtime._run_task,
            RuntimePolicy=ClauseRuntimePolicy,
            A2Policy=ClauseA2Policy,
        )
        body = bind(
            V7Runtime._run_task,
            _V5_RUN_TASK=inner,
            SessionPolicy=ClauseSessionPolicy,
            A6Policy=ClauseA6Policy,
            ProcessingScope=partial(ProcessingScope, resources=resources, rows=rows),
            describe_action=partial(describe_action, resources=resources),
            SCOPE_PROFILE=SCOPE_PROFILE,
            RUNTIME_VERSION=RUNTIME_VERSION,
            ValueOriginIndex=ValueOriginIndex,
        )
        result = cast(SecurityRun, body(self, task, **kwargs))
        audit = audit_anchors(task.instruction)
        path = Path(kwargs["output"]) / "run_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata["authorization"] = dict(
            profile=audit.profile,
            raw_user_sha256=audit.anchors.raw_user_sha256,
            blocked_by=audit.blocked_by,
            clauses=[asdict(c) for c in audit.clauses],
            anchors=audit.anchors.model_dump(mode="json"),
        )
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
