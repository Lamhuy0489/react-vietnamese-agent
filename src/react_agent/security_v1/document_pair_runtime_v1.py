"""Document diagnostic using unchanged v3 transport and versioned v8 policy.

The transport schema remains v3; runtime identity is separately bound by the
document probe checkpoint. No process-global patch or second agent loop.
"""

from types import FunctionType
from typing import Any, cast

from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.pair_runtime_v3 import run_pair_task as original
from react_agent.security_v1.processing_scope_v3 import ProcessingScope
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v8 import SecurityRuntime


def run_pair_task(task: RuntimeTask, **kwargs: Any) -> SecurityRun:
    namespace = dict(original.__globals__)
    namespace.update(ProcessingScope=ProcessingScope, SecurityRuntime=SecurityRuntime)
    body = FunctionType(
        original.__code__, namespace, original.__name__, original.__defaults__, original.__closure__
    )
    body.__kwdefaults__ = original.__kwdefaults__
    return cast(SecurityRun, body(task, **kwargs))
