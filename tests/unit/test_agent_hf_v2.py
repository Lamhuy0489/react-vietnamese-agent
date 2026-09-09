"""Pinned native buffer shape regression using the frozen v1 CPU fake fixtures."""

import json
import sys
from types import SimpleNamespace

import pytest
from test_agent_hf_v1 import fake as fake

from react_agent.llm.agent_hf_v1 import AgentHFBackend
from react_agent.llm.agent_hf_v2 import AgentHFBackendV2
from react_agent.llm.base import GenerationConfig


def native(fake: SimpleNamespace) -> None:
    sys.modules["transformers"].__version__ = "5.5.0"
    fake.buffers.append(
        (
            "model.rotary_emb.original_inv_freq",
            SimpleNamespace(shape=(64,), device="cuda:1", dtype="float32"),
        )
    )


def test_native_two_buffers_v1_rejects_v2_accepts(fake: SimpleNamespace) -> None:
    native(fake)
    with pytest.raises(ValueError, match="unexpected model buffer"):
        AgentHFBackend(fake.root, fake.inventory, fake.metrics)
    # Fresh fake allocator; actual failed load would retire its owning process.
    fake.state.loaded = False
    backend = AgentHFBackendV2(fake.root, fake.inventory, fake.metrics)
    assert backend.generate([{"role": "user", "content": "fixture"}], GenerationConfig()).text
    record = json.loads(fake.metrics.read_text().splitlines()[0])
    assert record["adapter_protocol"] == "agent_hf_dual_gpu_v2_tf550"
    assert record["protocol"] == "agent_hf_dual_gpu_v1"  # inherited behavior identified separately


@pytest.mark.parametrize(
    "case", ["version", "missing", "extra", "duplicate", "shape", "device", "dtype", "parameter"]
)
def test_v2_rejects_unexpected_inventory(fake: SimpleNamespace, case: str) -> None:
    native(fake)
    if case == "version":
        sys.modules["transformers"].__version__ = "other"
    elif case == "missing":
        fake.buffers.pop()
    elif case == "extra":
        fake.buffers.append(("model.rotary_emb.extra", fake.buffers[0][1]))
    elif case == "duplicate":
        fake.buffers[1] = fake.buffers[0]
    elif case == "shape":
        fake.buffers[1][1].shape = (128,)
    elif case == "device":
        fake.buffers[1][1].device = "cpu"
    elif case == "dtype":
        fake.buffers[1][1].dtype = "bfloat16"
    else:
        fake.parameters[0][1].dtype = "float32"
    with pytest.raises(ValueError):
        AgentHFBackendV2(fake.root, fake.inventory, fake.metrics)
