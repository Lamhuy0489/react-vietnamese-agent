"""Native guard observer outside the frozen attention/policy loader topology."""

from collections.abc import Callable
from pathlib import Path
from typing import cast

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.base import LLMBackend
from react_agent.llm.efficient_requests_v1 import GUARD_REVISION, EfficientRequestFactory
from react_agent.llm.guard_diagnostic_backend_v1 import DiagnosticFactory
from react_agent.llm.guard_hf_v1 import GuardHFConfig, GuardHFFactory
from react_agent.llm.guard_snapshot_v1 import MODEL_ID, GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AgentFactoryV2, GuardFactory
from react_agent.llm.model_pair_v2 import ShutdownPair
from react_agent.llm.native_shutdown_v2 import native_config
from react_agent.llm.ordinary_pair_probe_v1 import fresh_roots
from react_agent.llm.request_policy_v1 import RequestPolicyFactory
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory

PROFILE = "native_guard_diagnostics_v1"


def native_pair(
    agent: Path,
    inventory: Path,
    guard: Path,
    snapshot: GuardSnapshot,
    output: Path,
    attention: Path,
    policy: Path,
) -> ShutdownPair:
    """Construct lazily. Caller creates output after validation, before pair.start()."""
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
    # EfficientRequestFactory must see the actual HF backend, not an observer.
    agent_factory = ThreadProgressFactory(
        RequestPolicyFactory(
            EfficientRequestFactory(
                AgentFactoryV2(agent, inventory, output / "agent_hf_metrics.jsonl"),
                "agent",
                attention / "agent",
            ),
            policy / "agent",
        )
    )
    guard_factory = ThreadProgressFactory(
        RequestPolicyFactory(
            EfficientRequestFactory(
                GuardFactory(
                    GuardHFFactory(
                        guard, snapshot, GuardHFConfig(), output / "guard_hf_metrics.jsonl"
                    )
                ),
                "guard",
                attention / "guard",
            ),
            policy / "guard",
        )
    )
    return ShutdownPair(
        agent_factory,
        cast(
            Callable[[], LLMBackend],
            DiagnosticFactory(guard_factory, output / "guard_response_diagnostics.jsonl"),
        ),
        native_config(),
    )
