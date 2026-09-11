"""Lazy ordinary-request sibling composition; not the agent-only runtime owner."""

from collections.abc import Callable
from pathlib import Path

from react_agent.llm.agent_mount_v1 import MODEL, no_links
from react_agent.llm.base import LLMBackend
from react_agent.llm.efficient_requests_v1 import GUARD_REVISION, EfficientRequestFactory
from react_agent.llm.guard_snapshot_v1 import MODEL_ID
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig, ReadyFactory
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory


def request_pair(
    agent_factory: Callable[[], LLMBackend],
    guard_factory: Callable[[], LLMBackend],
    config: PairConfig,
    attention: Path,
) -> ModelPair:
    """Plan before spawn; native loader admission remains in each child factory."""
    no_links(attention)
    if attention.exists():
        raise ValueError("fresh attention root required")
    if config.agent != ModelIdentity(MODEL, AGENT_REVISION) or config.guard != ModelIdentity(
        MODEL_ID, GUARD_REVISION
    ):
        raise ValueError("pinned ordinary-request pair identities required")
    for factory in (agent_factory, guard_factory):
        if not callable(factory) or isinstance(
            factory, (ReadyFactory, ThreadProgressFactory, EfficientRequestFactory)
        ):
            raise ValueError("unwrapped native factories required")
    return ModelPair(
        ThreadProgressFactory(EfficientRequestFactory(agent_factory, "agent", attention / "agent")),
        ThreadProgressFactory(EfficientRequestFactory(guard_factory, "guard", attention / "guard")),
        config,
    )
