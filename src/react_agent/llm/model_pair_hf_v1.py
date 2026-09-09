"""Explicit pinned real-model factories; constructing factories never loads weights."""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from react_agent.llm.agent_hf_v2 import AgentHFBackendV2
from react_agent.llm.agent_mount_v1 import MODEL, REVISION
from react_agent.llm.base import LLMBackend
from react_agent.llm.guard_hf_v1 import GuardHFConfig, GuardHFFactory
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.llm.model_pair_v1 import ModelIdentity, ModelPair, PairConfig

AGENT_CONTENT = "24b62737df7885edc2facccd6ca172c0266bccec85c30080a9fcb45adad6d19b"
AGENT_REVISION = REVISION + ":runtime-sha256:" + AGENT_CONTENT


def verify_gpu_environment() -> dict[str, str]:
    import torch  # type: ignore[import-not-found]
    import transformers  # type: ignore[import-not-found]

    observed = {
        "torch": str(torch.__version__),
        "cuda": str(torch.version.cuda),
        "transformers": str(transformers.__version__),
    }
    if observed != {"torch": "2.10.0+cu128", "cuda": "12.8", "transformers": "5.5.0"}:
        raise ValueError("declared GPU dependency versions changed")
    return observed


@dataclass(frozen=True)
class AgentFactoryV2:
    model_path: Path
    inventory_path: Path
    metrics_path: Path

    def __call__(self) -> LLMBackend:
        return AgentHFBackendV2(self.model_path, self.inventory_path, self.metrics_path)


@dataclass(frozen=True)
class GuardFactory:
    hf: GuardHFFactory

    def __call__(self) -> LLMBackend:
        # Widen the immutable Literal identity for the mutable backend protocol;
        # transport never writes these attributes and checks them on every call.
        return cast(LLMBackend, self.hf())


def hf_pair(
    agent_path: Path, inventory_path: Path, guard_path: Path, snapshot: GuardSnapshot, output: Path
) -> ModelPair:
    if snapshot.upstream_revision != "989aa7980e4cf806f80c7fef2b1adb7bc71aa306":
        raise ValueError("fixed guard revision required")
    config = PairConfig(
        ModelIdentity(MODEL, AGENT_REVISION),
        ModelIdentity(snapshot.model_id, snapshot.model_revision),
    )
    return ModelPair(
        AgentFactoryV2(agent_path, inventory_path, output / "agent_hf_metrics.jsonl"),
        GuardFactory(
            GuardHFFactory(guard_path, snapshot, GuardHFConfig(), output / "guard_hf_metrics.jsonl")
        ),
        config,
    )
