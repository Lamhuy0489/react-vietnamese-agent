"""Opt-in A6 ticket ablation on the unchanged v12 loop and other gates."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.normalization import Profile
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.foundation.runtime_qa import RecordingBackend
from react_agent.llm.base import LLMBackend
from react_agent.llm.replay import ReplayBackend
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.a2_qa import MODEL, REVISION, SyntheticGuardFactory
from react_agent.security_v1.contracts import SecurityConfig
from react_agent.security_v1.final_entitlements_v2 import FinalEntitlement
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.public_field_ticket_policy_v1 import RUNTIME_VERSION, TicketA6Policy
from react_agent.security_v1.public_field_ticket_v1 import (
    PROFILE as TICKET_PROFILE,
)
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v12 import SecurityRuntime as V12Runtime
from react_agent.security_v1.warm_guard import WarmGuardBackend, WarmGuardConfig
from react_agent.tools.cached_fetch import CachedFetchTool
from react_agent.tools.cached_search import CachedSearchTool
from react_agent.tools.calculator import CalculatorTool
from react_agent.tools.db_query import DbQueryTool
from react_agent.tools.doc_read import DocReadTool
from react_agent.tools.doc_search import DocSearchTool
from react_agent.tools.post_webhook_mock import PostWebhookMockTool
from react_agent.tools.send_email_mock import SendEmailMockTool

CATALOG_VERSION = "host_source_catalog_v2_annotations"
SYNTHETIC_TOOLS = {
    "doc_search": DocSearchTool,
    "doc_read": DocReadTool,
    "db_query": DbQueryTool,
    "cached_search": CachedSearchTool,
    "cached_fetch": CachedFetchTool,
    "calculator": CalculatorTool,
    "send_email_mock": SendEmailMockTool,
    "post_webhook_mock": PostWebhookMockTool,
}


class SecurityRuntime(V12Runtime):
    def _admit_synthetic_cpu(
        self,
        security: SecurityConfig | None,
        catalog: SourceCatalog | None,
        guard_factory: Callable[[], LLMBackend] | None,
        guard_execution: WarmGuardConfig | None,
    ) -> None:
        if security is None or security.level != "A6" or not isinstance(catalog, SourceCatalog):
            raise ValueError("ticket ablation requires explicit A6 and host source catalog")
        if catalog.version != CATALOG_VERSION:
            raise ValueError("ticket ablation requires versioned host annotations")
        if type(self.backend) not in (ReplayBackend, RecordingBackend) or (
            self.backend.model_id,
            self.backend.model_revision,
        ) != (ReplayBackend.model_id, ReplayBackend.model_revision):
            raise ValueError("ticket ablation requires the synthetic replay agent")
        if (
            type(guard_factory) is not SyntheticGuardFactory
            or type(guard_execution) is not WarmGuardConfig
            or (guard_execution.model_id, guard_execution.model_revision) != (MODEL, REVISION)
        ):
            raise ValueError("ticket ablation requires the synthetic warm guard")
        if self.registry.names != tuple(sorted(SYNTHETIC_TOOLS)) or any(
            type(self.registry.get(name)) is not tool_type
            for name, tool_type in SYNTHETIC_TOOLS.items()
        ):
            raise ValueError("ticket ablation requires the fixed eight synthetic tools")

    def run_instrumented(
        self,
        task: RuntimeTask,
        *,
        output: Path,
        source_catalog: SourceCatalog | None = None,
        audit_profile: Profile = "raw_v1",
        security_config: SecurityConfig | None = None,
        guard_factory: Callable[[], LLMBackend] | None = None,
        guard_execution: WarmGuardConfig | None = None,
        entitlement: FinalEntitlement | None = None,
    ) -> SecurityRun:
        # Reject unsupported dependencies before constructing a worker or output.
        self._admit_synthetic_cpu(
            security_config, source_catalog, guard_factory, guard_execution
        )
        return super().run_instrumented(
            task,
            output=output,
            source_catalog=source_catalog,
            audit_profile=audit_profile,
            security_config=security_config,
            guard_factory=guard_factory,
            guard_execution=guard_execution,
            entitlement=entitlement,
        )

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        self._admit_synthetic_cpu(
            kwargs.get("security_config"),
            kwargs.get("source_catalog"),
            kwargs.get("guard_factory"),
            kwargs.get("guard_execution"),
        )
        worker = kwargs.get("_worker")
        if worker is not None and (
            type(worker) is not WarmGuardBackend
            or worker.factory is not kwargs.get("guard_factory")
            or worker.config is not kwargs.get("guard_execution")
        ):
            raise ValueError("ticket ablation requires its task-owned synthetic worker")
        body = bind(
            V12Runtime._run_task,
            ClauseA6Policy=TicketA6Policy,
            RUNTIME_VERSION=RUNTIME_VERSION,
        )
        result = cast(SecurityRun, body(self, task, **kwargs))
        path = Path(kwargs["output"]) / "run_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata["ticket_ablation"] = {
            "profile": TICKET_PROFILE,
            "catalog_version": CATALOG_VERSION,
            "host_inventory_attested": False,
            "scope": "synthetic_cpu_candidate_only",
        }
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
