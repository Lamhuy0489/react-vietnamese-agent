"""Lazy constrained guard pair; unchanged agent, worker lifecycle and host witness."""

from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from react_agent.llm.base import LLMBackend
from react_agent.llm.constrained_policy_v1 import ConstrainedPolicyFactory
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticFactory
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.native_guard_diagnostics_v2 import native_pair as observer_pair
from react_agent.llm.ordinary_pair_probe_v1 import fresh_roots
from react_agent.security_v1.guard_bare_json_v1 import bind


def native_pair(
    agent: Path,
    inventory: Path,
    guard: Path,
    snapshot: GuardSnapshot,
    output: Path,
    attention: Path,
    policy: Path,
    *,
    witness: Path,
    constrained: Path,
) -> DiagnosticPair:
    fresh_roots(output, attention, policy, constrained)
    for source in (agent, inventory, guard, witness):
        if constrained.resolve().is_relative_to(
            source.resolve()
        ) or source.resolve().is_relative_to(constrained.resolve()):
            raise ValueError("constraint evidence must not overlap inputs or witness")

    def observe(inner: Any, destination: Path) -> DiagnosticFactory:
        return DiagnosticFactory(
            cast(Callable[[], LLMBackend], ConstrainedPolicyFactory(inner, constrained, snapshot)),
            destination,
        )

    # Private function globals, not a global patch and not a replaced live worker.
    # The returned dataclass factories remain spawn-picklable; this closure is not retained.
    build = bind(observer_pair, DiagnosticFactory=observe)
    return cast(
        DiagnosticPair,
        build(
            agent,
            inventory,
            guard,
            snapshot,
            output,
            attention,
            policy,
            witness=witness,
        ),
    )
