"""Lazy native observed-shutdown composition; immutable underlying HF factories."""

from pathlib import Path

from react_agent.llm.agent_mount_v1 import MODEL, no_links
from react_agent.llm.efficient_requests_v1 import GUARD_REVISION
from react_agent.llm.guard_hf_v1 import GuardHFConfig, GuardHFFactory
from react_agent.llm.guard_snapshot_v1 import MODEL_ID, GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AGENT_REVISION, AgentFactoryV2, GuardFactory
from react_agent.llm.model_pair_v1 import ModelIdentity
from react_agent.llm.model_pair_v2 import AgentWorkerConfig, ShutdownPair, ShutdownPairConfig
from react_agent.llm.ordinary_pair_probe_v1 import fresh_roots
from react_agent.llm.request_policy_pair_v2 import policy_pair


def native_config() -> ShutdownPairConfig:
    return ShutdownPairConfig(
        ModelIdentity(MODEL, AGENT_REVISION), ModelIdentity(MODEL_ID, GUARD_REVISION)
    )


def native_pair(
    agent: Path,
    inventory: Path,
    guard: Path,
    snapshot: GuardSnapshot,
    output: Path,
    attention: Path,
    policy: Path,
) -> ShutdownPair:
    """Original immutable native factories, no private factory replacement or eager load."""
    fresh_roots(output, attention, policy)
    if not isinstance(snapshot, GuardSnapshot) or (snapshot.model_id, snapshot.model_revision) != (
        MODEL_ID,
        GUARD_REVISION,
    ):
        raise ValueError("exact content-bound guard snapshot required")
    for source in (agent, inventory, guard):
        no_links(source)
        if any(
            root.resolve().is_relative_to(source.resolve())
            or source.resolve().is_relative_to(root.resolve())
            for root in (output, attention, policy)
        ):
            raise ValueError("outputs must not overlap model inputs")
    return policy_pair(
        AgentFactoryV2(agent, inventory, output / "agent_hf_metrics.jsonl"),
        GuardFactory(
            GuardHFFactory(guard, snapshot, GuardHFConfig(), output / "guard_hf_metrics.jsonl")
        ),
        native_config(),
        attention,
        policy,
    )


def agent_config(config: ShutdownPairConfig) -> AgentWorkerConfig:
    """Agent-only gets the same role deadlines and shutdown budgets as the pair."""
    if not isinstance(config, ShutdownPairConfig):
        raise TypeError("observed-shutdown config required")
    return AgentWorkerConfig(
        config.agent.model_id,
        config.agent.model_revision,
        config.agent_start_seconds,
        config.agent_call_seconds,
        config.terminate_grace_seconds,
        config.kill_grace_seconds,
        config.graceful_shutdown_seconds,
    )
