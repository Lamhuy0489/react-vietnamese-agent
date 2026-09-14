"""Run-local CDOC scope dependency on the otherwise unchanged v7 security loop."""

from types import FunctionType
from typing import Any, cast

from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.processing_scope_v3 import PROFILE, ProcessingScope, describe_action
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v7 import SecurityRuntime as V7Runtime

RUNTIME_VERSION = "security_runtime_v8"


class SecurityRuntime(V7Runtime):
    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        original = V7Runtime._run_task
        namespace = dict(original.__globals__)
        namespace.update(
            ProcessingScope=ProcessingScope,
            describe_action=describe_action,
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
