"""Lazy native v2 observer composition with an independent host witness sink."""

from collections.abc import Callable
from pathlib import Path
from typing import cast

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.base import LLMBackend
from react_agent.llm.efficient_requests_v1 import GUARD_REVISION, EfficientRequestFactory
from react_agent.llm.guard_diagnostic_backend_v1 import validate_output
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticFactory
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.guard_hf_v1 import GuardHFConfig, GuardHFFactory
from react_agent.llm.guard_snapshot_v1 import MODEL_ID, GuardSnapshot
from react_agent.llm.model_pair_hf_v1 import AgentFactoryV2, GuardFactory
from react_agent.llm.native_shutdown_v2 import native_config
from react_agent.llm.ordinary_pair_probe_v1 import fresh_roots
from react_agent.llm.request_policy_v1 import RequestPolicyFactory
from react_agent.llm.worker_progress_v1 import ThreadProgressFactory

PROFILE = "native_guard_diagnostics_v2"


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
) -> DiagnosticPair:
    """Witness parent must exist; native metrics roots must still be fresh."""
    fresh_roots(output, attention, policy)
    validate_output(witness)
    if not isinstance(snapshot, GuardSnapshot) or (snapshot.model_id, snapshot.model_revision) != (
        MODEL_ID,
        GUARD_REVISION,
    ):
        raise ValueError("exact content-bound guard snapshot required")
    for source in (agent, inventory, guard, output, attention, policy):
        no_links(source)
        if witness.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(
            witness.resolve()
        ):
            raise ValueError("witness must not overlap model or native roots")
    for source in (agent, inventory, guard):
        if any(
            root.resolve().is_relative_to(source.resolve())
            or source.resolve().is_relative_to(root.resolve())
            for root in (output, attention, policy)
        ):
            raise ValueError("outputs must not overlap model inputs")
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
    return DiagnosticPair(
        agent_factory,
        cast(
            Callable[[], LLMBackend],
            DiagnosticFactory(guard_factory, output / "guard_response_diagnostics.jsonl"),
        ),
        native_config(),
        witness,
    )
