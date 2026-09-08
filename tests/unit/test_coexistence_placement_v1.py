"""CPU arithmetic and fail-closed placement admission; no model or Test data."""

import json
from pathlib import Path
from typing import Any

import pytest

from react_agent.llm.coexistence_placement_v1 import (
    GIB,
    PARAMETERS,
    DeviceMemory,
    PlacementPlan,
    admit_context,
    admit_devices,
    validate_agent_geometry,
    validate_tensor_placement,
)


def test_identity_arithmetic() -> None:
    plan = PlacementPlan()
    assert PARAMETERS == 7_615_616_512
    assert sum(plan.weight_bytes()) == PARAMETERS * 2
    assert sum(plan.kv_bytes()) == 2 * 28 * 4 * 128 * 2 * 4608
    assert plan.required_free_bytes() == (13 * GIB, 13 * GIB)
    assert plan.sha256 == PlacementPlan.model_validate_json(plan.model_dump_json()).sha256
    assert plan.sha256 != PlacementPlan(first_device_layers=19).sha256
    assert plan.device_map()["model.layers.19"] == 0
    assert plan.device_map()["model.layers.20"] == 1
    assert len(plan.device_map()) == 32


@pytest.mark.parametrize(
    "change",
    [
        {"first_device_layers": 0},
        {"first_device_layers": 28},
        {"first_device_layers": True},
        {"agent_caps": [True, 7 * GIB]},
        {"agent_caps": [12 * GIB, "7500000000"]},
        {"agent_caps": [12 * GIB]},
        {"agent_caps": [1, 1]},
        {"global_headroom": 1},
        {"workspace_per_device": 0},
        {"guard_cap": 4 * GIB},
        {"input_limit": 8192},
        {"output_limit": 128},
        {"guard_device": 0},
        {"unknown": 1},
    ],
)
def test_bad_plan(change: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        PlacementPlan(**change)


@pytest.mark.parametrize("n", [1, 4096])
def test_context_boundary(n: int) -> None:
    admit_context(PlacementPlan(), n, 512)


@pytest.mark.parametrize("i,o", [(0, 512), (4097, 512), (True, 512), (1, 128), (1, 512.0)])
def test_bad_context(i: Any, o: Any) -> None:
    with pytest.raises(ValueError):
        admit_context(PlacementPlan(), i, o)


@pytest.mark.parametrize("missing", [False, True])
def test_device_headroom(missing: bool) -> None:
    samples = [
        DeviceMemory(
            index=i,
            name="Tesla T4",
            total_bytes=15636037632,
            free_bytes=13 * GIB - (1 if missing and i == 1 else 0),
        )
        for i in (0, 1)
    ]
    if missing:
        with pytest.raises(ValueError):
            admit_devices(PlacementPlan(), samples)
    else:
        admit_devices(PlacementPlan(), reversed(samples))
    with pytest.raises(ValueError):
        admit_devices(PlacementPlan(), [samples[0], samples[0]])
    with pytest.raises(ValueError):
        admit_devices(PlacementPlan(), samples[:1])


@pytest.mark.parametrize(
    "change",
    [
        {"free_bytes": -1},
        {"free_bytes": 17 * GIB},
        {"free_bytes": True},
        {"total_bytes": 0},
        {"name": "P100"},
        {"index": 2},
    ],
)
def test_invalid_observation(change: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        DeviceMemory(
            **(
                {"index": 0, "name": "Tesla T4", "free_bytes": 13 * GIB, "total_bytes": 15636037632}
                | change
            )
        )


@pytest.mark.parametrize(
    "change", ["", "offload", "wrong_gpu", "unknown", "duplicate", "missing", "prefix"]
)
def test_tensor_inventory(change: str) -> None:
    plan = PlacementPlan()
    tensors = [
        (m + ".weight", f"cuda:{d}")
        for m, d in plan.device_map().items()
        if m != "model.rotary_emb"
    ]
    if change == "offload":
        tensors[0] = tensors[0][0], "cpu"
    elif change == "wrong_gpu":
        tensors[0] = tensors[0][0], "cuda:1"
    elif change == "unknown":
        tensors.append(("unknown.weight", "cuda:0"))
    elif change == "duplicate":
        tensors.append(tensors[0])
    elif change == "missing":
        tensors.pop()
    elif change == "prefix":
        tensors.append(("model.layers.200.weight", "cuda:1"))
    if change:
        with pytest.raises(ValueError):
            validate_tensor_placement(plan, tensors)
    else:
        validate_tensor_placement(plan, tensors)


def test_contract_is_explicit_about_estimate() -> None:
    root = Path(__file__).resolve().parents[2]
    contract = (root / "docs/architecture/phase5_coexistence_placement_v1_contract.md").read_text()
    assert "not combined GPU fit" in contract and "does not authenticate weights" in contract
    assert "max_memory" not in json.dumps(PlacementPlan().model_dump())


@pytest.mark.parametrize(
    "change",
    [
        {},
        {"num_hidden_layers": 24},
        {"num_attention_heads": 32},
        {"num_key_value_heads": 8},
        {"tie_word_embeddings": True},
        {"use_sliding_window": 0},
        {"head_dim": 64},
        {"attention_bias": False},
        {"mlp_bias": True},
        {"auto_map": {}},
        {"quantization_config": {}},
        {"rope_scaling": None},
        {"architectures": ["OtherModel"]},
    ],
)
def test_geometry(change: dict[str, Any]) -> None:
    config = {
        "model_type": "qwen2",
        "architectures": ["Qwen2ForCausalLM"],
        "num_hidden_layers": 28,
        "hidden_size": 3584,
        "intermediate_size": 18944,
        "num_attention_heads": 28,
        "num_key_value_heads": 4,
        "vocab_size": 152064,
        "tie_word_embeddings": False,
        "max_position_embeddings": 32768,
        "use_sliding_window": False,
    } | change
    if change:
        with pytest.raises(ValueError):
            validate_agent_geometry(config)
    else:
        validate_agent_geometry(config)


@pytest.mark.parametrize(
    "change",
    [
        {"guard_device": True},
        {"input_limit": 4096.0},
        {"output_limit": 512.0},
        {"guard_cap": 5368709120.0},
    ],
)
def test_no_literal_coercion(change: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        PlacementPlan(**change)


def test_wrong_t4_substring() -> None:
    with pytest.raises(ValueError):
        DeviceMemory(index=0, name="Not T4 compatible", total_bytes=16 * GIB, free_bytes=14 * GIB)
