"""Lazy agent-only composition matching the frozen ordinary pair's agent stack."""

from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.efficient_requests_v1 import EfficientRequestFactory
from react_agent.llm.model_pair_hf_v1 import AgentFactoryV2
from react_agent.llm.request_policy_v1 import RequestPolicyFactory, paths
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory


def native_agent(
    agent: Path, inventory: Path, metrics: Path, attention: Path, policy: Path
) -> ThreadProgressFactory:
    """No guard object, transport allocation, native import or model load here."""
    paths(policy, attention)
    for path in (agent, inventory, metrics):
        no_links(path)
    if metrics.exists():
        raise ValueError("fresh native metrics required")
    outputs = (metrics, attention, policy)
    for i, output in enumerate(outputs):
        if any(
            output.resolve().is_relative_to(other.resolve())
            or other.resolve().is_relative_to(output.resolve())
            for other in (*outputs[i + 1 :], agent, inventory)
        ):
            raise ValueError("disjoint native input/evidence paths required")
    return ThreadProgressFactory(
        RequestPolicyFactory(
            EfficientRequestFactory(AgentFactoryV2(agent, inventory, metrics), "agent", attention),
            policy,
        )
    )
