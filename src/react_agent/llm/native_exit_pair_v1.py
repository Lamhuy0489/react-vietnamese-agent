"""Lazy native constrained composition with an explicit observed-exit pair."""

from typing import Any, cast

from react_agent.llm import native_constrained_pair_v1 as constrained
from react_agent.llm.exit_pair_v1 import ExitPair
from react_agent.llm.native_guard_diagnostics_v2 import native_pair as observer_pair
from react_agent.security_v1.guard_bare_json_v1 import bind


def native_pair(*args: Any, **kwargs: Any) -> ExitPair:
    observed = bind(observer_pair, DiagnosticPair=ExitPair)
    # Constrained builder binds its DiagnosticFactory privately on this copy.
    return cast(ExitPair, bind(constrained.native_pair, observer_pair=observed)(*args, **kwargs))
