"""Keep host readiness outside the single-use native stress instrumentation."""

from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.generation_policy_v1 import PolicyStressFactory
from react_agent.llm.model_pair_v1 import ModelPair, ReadyFactory, Role
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory


def instrument_pair(pair: ModelPair, output: Path, policy: Path) -> None:
    """Plan factories before startup; no native imports, readiness or model calls."""
    if pair.state != "NEW":
        raise ValueError("fresh unstarted pair required")
    for root in (output, policy):
        no_links(root)
        if root.exists():
            raise ValueError("fresh diagnostic roots required")
    if output.resolve().is_relative_to(policy.resolve()) or policy.resolve().is_relative_to(
        output.resolve()
    ):
        raise ValueError("separate diagnostic roots required")
    roles: tuple[Role, Role] = ("agent", "guard")
    # Validate both sides before mutating either factory. Do not recursively
    # unwrap unknown decorators or relax the native loader's exact-type check.
    factories: dict[Role, ReadyFactory] = {}
    for role in roles:
        ready = pair._workers[role].factory
        if type(ready) is not ReadyFactory:
            raise ValueError("one exact host ReadyFactory per role required")
        if isinstance(ready.factory, (ReadyFactory, ThreadProgressFactory, PolicyStressFactory)):
            raise ValueError("unmodified inner model factory required")
        factories[role] = ready
    for role, ready in factories.items():
        pair._workers[role].factory = ReadyFactory(
            ThreadProgressFactory(
                PolicyStressFactory(ready.factory, role, output / f"{role}_stress", policy / role)
            )
        )
