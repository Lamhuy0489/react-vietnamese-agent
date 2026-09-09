"""Pinned Transformers 5.5 native rotary-buffer compatibility; v1 stays frozen."""

from typing import Any

from react_agent.llm.agent_hf_v1 import AgentHFBackend
from react_agent.llm.agent_runtime_input_v1 import parameter_shapes
from react_agent.llm.coexistence_placement_v1 import validate_tensor_placement


class AgentHFBackendV2(AgentHFBackend):
    def validate_loaded_tensors(self) -> None:
        if self.transformers.__version__ != "5.5.0":
            raise ValueError("adapter v2 requires pinned Transformers 5.5.0")
        parameters = list(self.model.named_parameters(remove_duplicate=False))
        buffers = list(self.model.named_buffers(remove_duplicate=False))
        shapes = parameter_shapes()
        if len(parameters) != len(shapes) or {n for n, _ in parameters} != set(shapes):
            raise ValueError("loaded parameter inventory mismatch")
        if any(tuple(t.shape) != shapes[n] or t.dtype != self.torch.float16 for n, t in parameters):
            raise ValueError("loaded parameter shape/dtype mismatch")
        expected = {"model.rotary_emb.inv_freq", "model.rotary_emb.original_inv_freq"}
        if len(buffers) != 2 or {n for n, _ in buffers} != expected:
            raise ValueError("exact native 5.5 rotary buffer inventory required")
        if any(
            tuple(t.shape) != (64,) or t.dtype not in (self.torch.float16, self.torch.float32)
            for _, t in buffers
        ):
            raise ValueError("unexpected rotary buffer shape/dtype")
        validate_tensor_placement(self.plan, [(n, str(t.device)) for n, t in parameters + buffers])

    def _write(self, record: dict[str, Any], *, exclusive: bool = False) -> None:
        super()._write(
            record | {"adapter_protocol": "agent_hf_dual_gpu_v2_tf550"}, exclusive=exclusive
        )
