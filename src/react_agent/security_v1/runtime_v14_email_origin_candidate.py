"""Opt-in v14 runtime for the safe-email grammar and origin candidate.

This adapter is a bounded CPU/Dev candidate.  It keeps the v12/v13 loop and
all existing A0--A5/session gates, replacing only the raw-user anchor parser
and the host destination origin index.  The production/frozen runtimes are
not modified and this module must not be used as Phase 5 acceptance evidence
until a separately declared matched API run is completed.
"""

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
from react_agent.security_v1.authorization_anchors_v4 import audit_anchors, extract_anchors
from react_agent.security_v1.contracts import SecurityConfig, configuration
from react_agent.security_v1.email_value_gates_v1 import value_pre_check
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
from react_agent.security_v1.value_origin_v4_email_candidate import (
    PROFILE as ORIGIN_PROFILE,
)
from react_agent.security_v1.value_origin_v4_email_candidate import (
    ValueOriginIndex,
)

RUNTIME_VERSION = "security_runtime_v14_email_origin_candidate"


class CandidateRuntimePolicy(RuntimePolicy):
    def __init__(self, config: SecurityConfig, raw_user: str) -> None:
        super().__init__(config, raw_user)
        self.component.anchors = extract_anchors(raw_user)


class CandidateA2Policy(A2Policy, CandidateRuntimePolicy):
    """A2 policy with v4 raw-user anchors and frozen A2 behavior."""


class CandidateSessionPolicy(SessionPolicy, CandidateA2Policy):
    """A3--A5 inherit the frozen session gates with v4 anchors."""


class CandidateA6Policy(A6Policy, CandidateSessionPolicy):
    def pre_bound(self, *args: Any, **kwargs: Any) -> Any:
        check = bind(value_pre_check, extract_anchors=extract_anchors)
        return bind(A6Policy.pre_bound, value_pre_check=check)(self, *args, **kwargs)


class SecurityRuntime(V10Runtime):
    """Candidate runtime; callers must opt in explicitly."""

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        security = kwargs.get("security_config") or configuration("A0")
        if security.level == "A0":
            return super()._run_task(task, **kwargs)
        catalog = kwargs.get("source_catalog") or SourceCatalog()
        resources = ResourceBindings.from_catalog(catalog)
        rows = RowBindings.from_catalog(catalog)
        inner = bind(
            V5Runtime._run_task,
            RuntimePolicy=CandidateRuntimePolicy,
            A2Policy=CandidateA2Policy,
        )
        body = bind(
            V7Runtime._run_task,
            _V5_RUN_TASK=inner,
            SessionPolicy=CandidateSessionPolicy,
            A6Policy=CandidateA6Policy,
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
        metadata["candidate_runtime"] = {
            "profile": "authorization_anchors_v4_candidate",
            "value_origin_profile": ORIGIN_PROFILE,
            "value_pre_gate_profile": "value_pre_gate_v2_email_subject_candidate",
            "a6_native_ready": False,
            "a6_native_ready_reason": "CPU/Dev candidate; no API acceptance run",
            "scope": "CPU/Dev destination-provenance diagnostic only",
        }
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
