"""CPU-only opt-in A6 sentence authorization candidate; frozen v10 stays unchanged."""

from __future__ import annotations

from functools import partial
from typing import Any, cast

from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.a6_policy import A6Policy
from react_agent.security_v1.authorization_anchors_v2 import PROFILE, extract_anchors
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.processing_scope_v5 import PROFILE as SCOPE_PROFILE
from react_agent.security_v1.processing_scope_v5 import ProcessingScope, describe_action
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v7 import SecurityRuntime as V7Runtime
from react_agent.security_v1.runtime_v10 import SecurityRuntime as V10Runtime
from react_agent.security_v1.sql_rows_v1 import RowBindings
from react_agent.security_v1.value_gates import value_pre_check

RUNTIME_VERSION = "security_runtime_v11_a6_sentence_candidate"


class SentenceA6Policy(A6Policy):
    def __init__(self, config: Any, raw_user: str, guard: Any) -> None:
        super().__init__(config, raw_user, guard)
        self.component.anchors = extract_anchors(raw_user)

    def pre_bound(self, *args: Any, **kwargs: Any) -> Any:
        check = bind(value_pre_check, extract_anchors=extract_anchors)
        return bind(A6Policy.pre_bound, value_pre_check=check)(self, *args, **kwargs)


class SecurityRuntime(V10Runtime):
    """Explicit experiment only; does not replace native dispatch or A0–A5."""

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        security = kwargs.get("security_config") or configuration("A0")
        if security.level != "A6":
            return super()._run_task(task, **kwargs)
        catalog = kwargs.get("source_catalog") or SourceCatalog()
        resources = ResourceBindings.from_catalog(catalog)
        rows = RowBindings.from_catalog(catalog)
        body = bind(
            V7Runtime._run_task,
            A6Policy=SentenceA6Policy,
            ProcessingScope=partial(ProcessingScope, resources=resources, rows=rows),
            describe_action=partial(describe_action, resources=resources),
            SCOPE_PROFILE=SCOPE_PROFILE,
            RUNTIME_VERSION=RUNTIME_VERSION,
        )
        return cast(SecurityRun, body(self, task, **kwargs))


def candidate_identity() -> dict[str, str | bool]:
    return dict(runtime=RUNTIME_VERSION, anchor_profile=PROFILE, native_dispatch_allowed=False)
