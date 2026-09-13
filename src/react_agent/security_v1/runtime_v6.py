"""Versioned A6 adapter that composes raw-user final entitlements.

The established v5 loop remains the implementation of task execution.  This
module supplies its final-bound dependency per call, without mutating v5 or
creating a second ReAct loop.  The adapter is host-only and serializes no raw
user text into metadata; the entitlement component binds that text by hash.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path
from types import FunctionType
from typing import Any, cast

from react_agent.foundation.normalization import Profile, text_hash
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.base import LLMBackend
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import SecurityConfig, configuration
from react_agent.security_v1.final_entitlements import (
    RELEASE_PROFILE,
    EntitlementError,
    FinalEntitlement,
    extract_final_entitlement,
    release_final_with_entitlement,
)
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5SecurityRuntime
from react_agent.security_v1.warm_guard import WarmGuardConfig

_ACTIVE_ENTITLEMENT: ContextVar[FinalEntitlement | None] = ContextVar(
    "phase5_active_final_entitlement", default=None
)
_V5_RUN_TASK = V5SecurityRuntime._run_task


class SecurityRuntime(V5SecurityRuntime):
    """A v5-compatible runtime with an opt-in host-bound final entitlement."""

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
        security = security_config or configuration("A0")
        if entitlement is not None and security.level != "A6":
            raise ValueError("final entitlement requires A6")
        if entitlement is not None and text_hash(task.instruction) != entitlement.raw_user_sha256:
            raise EntitlementError("entitlement is not bound to the raw user")
        token = _ACTIVE_ENTITLEMENT.set(entitlement)
        try:
            result = super().run_instrumented(
                task,
                output=output,
                source_catalog=source_catalog,
                audit_profile=audit_profile,
                security_config=security,
                guard_factory=guard_factory,
                guard_execution=guard_execution,
            )
        finally:
            _ACTIVE_ENTITLEMENT.reset(token)
        self._annotate_metadata(output.resolve(), supplied=entitlement is not None)
        return result

    def _run_task(self, *args: Any, **kwargs: Any) -> SecurityRun:
        """Run the frozen v5 body with a per-call final-bound global map.

        ``runtime_v5`` resolves ``final_bound`` as a module global.  Cloning its
        function with a private globals mapping keeps that source byte-for-byte
        intact and avoids a process-global monkeypatch, so concurrent adapter
        instances cannot exchange entitlements.
        """

        supplied = _ACTIVE_ENTITLEMENT.get()

        def entitled_bound(index: Any, proposal_id: str, user_id: str) -> Any:
            user = index.store.get(user_id)
            raw_user = user.content()
            if not isinstance(raw_user, str):
                raise EntitlementError("raw host user text required")
            entitlement = supplied
            if entitlement is None:
                try:
                    entitlement = extract_final_entitlement(raw_user)
                except EntitlementError:
                    # Oversized/malformed raw input receives the same empty
                    # grant as an implicit non-entitled user; no private value
                    # can become authorized from an extraction failure.
                    entitlement = FinalEntitlement(raw_user_sha256=text_hash(raw_user))
            return release_final_with_entitlement(index, proposal_id, user_id, entitlement)

        namespace = dict(_V5_RUN_TASK.__globals__)
        namespace["final_bound"] = entitled_bound
        namespace["FINAL_POLICY"] = RELEASE_PROFILE
        body = FunctionType(
            _V5_RUN_TASK.__code__,
            namespace,
            _V5_RUN_TASK.__name__,
            _V5_RUN_TASK.__defaults__,
            _V5_RUN_TASK.__closure__,
        )
        body.__kwdefaults__ = _V5_RUN_TASK.__kwdefaults__
        return cast(SecurityRun, body(self, *args, **kwargs))

    @staticmethod
    def _annotate_metadata(output: Path, *, supplied: bool) -> None:
        metadata_path = output / "run_metadata.json"
        if not metadata_path.is_file():
            return
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["runtime_version"] = "security_runtime_v6_entitlement_adapter"
        metadata["entitlement_adapter_profile"] = RELEASE_PROFILE
        metadata["entitlement_supplied_by_host"] = supplied
        metadata["a6_policy_profile"] = "a6_composition_with_final_entitlement_v1"
        metadata["final_policy"] = RELEASE_PROFILE
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


__all__ = ["SecurityRuntime"]
