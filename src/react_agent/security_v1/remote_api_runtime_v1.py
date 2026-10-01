"""Public runtime adapter labels local process cleanup separately from remote work."""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from react_agent.foundation.normalization import Profile
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.base import LLMBackend
from react_agent.llm.structured_session_factory_v1 import StructuredSessionFactory
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import SecurityConfig, configuration
from react_agent.security_v1.final_entitlements_v2 import FinalEntitlement
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v12 import SecurityRuntime as ClauseRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig


class RemoteAPIRuntime(ClauseRuntime):
    def run_instrumented(
        self, task: RuntimeTask, *, output: Path, source_catalog: SourceCatalog | None = None,
        audit_profile: Profile = "raw_v1", security_config: SecurityConfig | None = None,
        guard_factory: Callable[[], LLMBackend] | None = None,
        guard_execution: WarmGuardConfig | None = None,
        entitlement: FinalEntitlement | None = None,
    ) -> SecurityRun:
        security = security_config or configuration("A0")
        if security.llm_guard:
            if not isinstance(guard_factory, StructuredSessionFactory) or guard_execution is None:
                raise ValueError("explicit journaled remote guard factory required")
            if (guard_factory.role != "guard" or guard_factory.task_id != task.task_id
                    or (guard_factory.model_id, guard_factory.model_revision) != (
                        guard_execution.model_id, guard_execution.model_revision)):
                raise ValueError("task-bound guard identity required")
        # All lifecycle creation, validation and gates remain in the public inherited API.
        result = super().run_instrumented(task, output=output, source_catalog=source_catalog,
            audit_profile=audit_profile, security_config=security, guard_factory=guard_factory,
            guard_execution=guard_execution, entitlement=entitlement)
        path = output / "run_metadata.json"
        metadata = json.loads(path.read_text())
        metadata["transport_profile"] = "journaled_remote_api_v1"
        metadata["guard_lifecycle_scope"] = "host_http_process_only" if security.llm_guard else None
        metadata["remote_cancellation_supported"] = False
        metadata["remote_guard_identity"] = (
            guard_factory.public_identity() if isinstance(guard_factory, StructuredSessionFactory)
            else None)
        metadata["phase5_accepted"] = False
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
        return result
