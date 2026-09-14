"""Task-local host-bound resource scope on the frozen v7 security loop."""

from functools import partial
from types import FunctionType
from typing import Any, cast

from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.processing_scope_v4 import PROFILE, ProcessingScope, describe_action
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v7 import SecurityRuntime as V7Runtime

RUNTIME_VERSION = "security_runtime_v9"


class SecurityRuntime(V7Runtime):
    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        security = kwargs.get("security_config") or configuration("A0")
        resources = (
            ResourceBindings.from_catalog(kwargs.get("source_catalog") or SourceCatalog())
            if security.session_trust
            else ResourceBindings()
        )
        original = V7Runtime._run_task
        namespace = dict(original.__globals__)
        namespace.update(
            ProcessingScope=partial(ProcessingScope, resources=resources),
            describe_action=partial(describe_action, resources=resources),
            SCOPE_PROFILE=PROFILE,
            RUNTIME_VERSION=RUNTIME_VERSION,
        )
        body = FunctionType(
            original.__code__,
            namespace,
            original.__name__,
            original.__defaults__,
            original.__closure__,
        )
        body.__kwdefaults__ = original.__kwdefaults__
        return cast(SecurityRun, body(self, task, **kwargs))
