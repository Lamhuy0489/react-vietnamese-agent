"""Geometry controls use synthetic tokenizers/IDs, never benchmark or model outputs."""

from dataclasses import replace
from typing import Any

import pytest

from react_agent.llm.context_geometry_v1 import (
    INPUT_TOKENS,
    SEED_TEXT,
    build_geometry,
    summarize_generation,
)


class Tokenizer:
    all_special_ids = [0, 1]

    def __init__(self, ids: list[int] | None = None) -> None:
        self.ids = [2, 3, 4] if ids is None else ids
        self.calls: list[tuple[str, bool]] = []

    def __len__(self) -> int:
        return 10000

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        self.calls.append((text, add_special_tokens))
        return self.ids.copy()


@pytest.mark.parametrize("role,count", [("agent", 512), ("guard", 128)])
@pytest.mark.parametrize("seed_length", [1, 3, 17, 4096])
def test_exact_reproducible_geometry(role: Any, count: int, seed_length: int) -> None:
    tokenizer = Tokenizer(list(range(2, seed_length + 2)))
    geometry = build_geometry(tokenizer, role, "synthetic-tokenizer:v1")
    assert tokenizer.calls == [(SEED_TEXT, False)]
    assert len(geometry.input_ids) == INPUT_TOKENS
    assert geometry.output_tokens == count
    assert geometry.input_ids == tuple(tokenizer.ids[i % seed_length] for i in range(INPUT_TOKENS))
    assert geometry.receipt() == build_geometry(tokenizer, role, "synthetic-tokenizer:v1").receipt()


@pytest.mark.parametrize("ids", [[], [True], [-1], [10000], [2.5], [0], [1], [2] * 4097])
def test_reject_invalid_seed(ids: Any) -> None:
    with pytest.raises(ValueError):
        build_geometry(Tokenizer(ids), "agent", "synthetic:v1")


@pytest.mark.parametrize(
    "mode", ["role", "identity", "short", "long", "prefix", "mutable", "vocab"]
)
def test_geometry_mutation_rejected(mode: str) -> None:
    geometry = build_geometry(Tokenizer(), "agent", "synthetic:v1")
    changes = {
        "role": {"role": "other"},
        "identity": {"tokenizer_identity": ""},
        "short": {"input_ids": geometry.input_ids[:-1]},
        "long": {"input_ids": geometry.input_ids + (2,)},
        "prefix": {"input_ids": (9,) + geometry.input_ids[1:]},
        "mutable": {"input_ids": list(geometry.input_ids)},
        "vocab": {"vocab_size": True},
    }
    with pytest.raises(ValueError):
        replace(geometry, **changes[mode])  # type: ignore[arg-type]


@pytest.mark.parametrize("role", ["agent", "guard"])
def test_output_count_does_not_certify_cache(role: Any) -> None:
    geometry = build_geometry(Tokenizer(), role, "synthetic:v1")
    sequence = list(geometry.input_ids) + [9] * geometry.output_tokens
    unknown = summarize_generation(geometry, sequence, cache_length_after_generation=None)
    native = summarize_generation(
        geometry, sequence, cache_length_after_generation=len(sequence) - 1
    )
    full = summarize_generation(
        geometry,
        sequence,
        cache_length_after_generation=len(sequence) - 1,
        cache_length_after_final_forward=len(sequence),
    )
    assert not unknown["full_boundary_cache_observed"]
    assert not native["full_boundary_cache_observed"]
    assert full["full_boundary_cache_observed"]
    assert all(not isinstance(v, list | tuple) for v in full.values())
    assert not full["generated_text_retained"]


@pytest.mark.parametrize(
    "mode",
    [
        "short",
        "long",
        "prefix",
        "bool",
        "oov",
        "cache_full",
        "cache_short",
        "cache_bool",
        "forward_without_cache",
        "forward_short",
    ],
)
def test_output_and_cache_mismatches(mode: str) -> None:
    geometry = build_geometry(Tokenizer(), "guard", "synthetic:v1")
    sequence = list(geometry.input_ids) + [9] * geometry.output_tokens
    cache: Any = len(sequence) - 1
    forward: Any = None
    if mode == "short":
        sequence.pop()
    elif mode == "long":
        sequence.append(9)
    elif mode == "prefix":
        sequence[0] = 9
    elif mode == "bool":
        sequence[-1] = True
    elif mode == "oov":
        sequence[-1] = 10000
    elif mode == "cache_full":
        cache = len(sequence)
    elif mode == "cache_short":
        cache -= 1
    elif mode == "cache_bool":
        cache = True
    elif mode == "forward_without_cache":
        cache, forward = None, len(sequence)
    elif mode == "forward_short":
        forward = len(sequence) - 1
    with pytest.raises(ValueError):
        summarize_generation(
            geometry,
            sequence,
            cache_length_after_generation=cache,
            cache_length_after_final_forward=forward,
        )
