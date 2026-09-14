"""Host-bound scope runtime v9 with unchanged observed-shutdown v3 transport."""

from functools import partial
from types import FunctionType
from typing import Any, cast

from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.pair_runtime_v3 import run_pair_task as original
from react_agent.security_v1.processing_scope_v4 import ProcessingScope
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v9 import SecurityRuntime


def run_pair_task(task: RuntimeTask, **kwargs: Any) -> SecurityRun:
    catalog = kwargs.get("source_catalog")
    if not isinstance(catalog, SourceCatalog):
        raise ValueError("typed host source catalog required")
    resources = (
        ResourceBindings.from_catalog(catalog)
        if kwargs["security"].session_trust
        else ResourceBindings()
    )
    namespace = dict(original.__globals__)
    namespace.update(
        ProcessingScope=partial(ProcessingScope, resources=resources),
        SecurityRuntime=SecurityRuntime,
    )
    body = FunctionType(
        original.__code__,
        namespace,
        original.__name__,
        original.__defaults__,
        original.__closure__,
    )
    body.__kwdefaults__ = original.__kwdefaults__
    return cast(SecurityRun, body(task, **kwargs))
