"""Native route correction: the admitted guard factory owns the constraint root."""

from __future__ import annotations

from typing import Any, cast

from react_agent.llm import clause_dev_dispatch_v1 as previous
from react_agent.security_v1.clause_pair_runtime_v1 import run_pair_task
from react_agent.security_v1.guard_bare_json_v1 import bind


def native_runtime(task: Any, **kwargs: Any) -> Any:
    # Native topology admission derives this path from the guard factory.
    # Only the explicitly synthetic route accepts a caller-supplied root.
    if "constrained" in kwargs:
        raise ValueError("native constraint root is owned by the admitted factory")
    return run_pair_task(task, **kwargs)


def run(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return cast(dict[str, Any], bind(previous.run, native_runtime=native_runtime)(*args, **kwargs))
