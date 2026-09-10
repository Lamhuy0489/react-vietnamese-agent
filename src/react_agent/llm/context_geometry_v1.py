"""Deterministic synthetic token geometry; not model inference or quality evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal, Protocol

INPUT_TOKENS = 4096
SEED_TEXT = "Đây là văn bản tổng hợp để kiểm tra độ dài ngữ cảnh của hệ thống. "
Role = Literal["agent", "guard"]


class GeometryTokenizer(Protocol):
    all_special_ids: list[int]

    def __len__(self) -> int: ...

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]: ...


def digest_ids(ids: tuple[int, ...]) -> str:
    return hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest()


def _valid_ids(ids: list[int] | tuple[int, ...], vocab_size: int) -> bool:
    return bool(ids) and all(type(n) is int and 0 <= n < vocab_size for n in ids)


@dataclass(frozen=True)
class InputGeometry:
    role: Role
    tokenizer_identity: str
    vocab_size: int
    seed_ids: tuple[int, ...]
    special_ids: tuple[int, ...]
    input_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.role not in ("agent", "guard"):
            raise ValueError("fixed stress role required")
        if not isinstance(self.tokenizer_identity, str) or not self.tokenizer_identity.strip():
            raise ValueError("caller-bound immutable tokenizer identity required")
        if type(self.vocab_size) is not int or self.vocab_size <= 0:
            raise ValueError("positive tokenizer vocabulary size required")
        for ids in (self.seed_ids, self.special_ids, self.input_ids):
            if type(ids) is not tuple or (ids and not _valid_ids(ids, self.vocab_size)):
                raise ValueError("immutable in-vocabulary integer IDs required")
        if not 1 <= len(self.seed_ids) <= INPUT_TOKENS:
            raise ValueError("nonempty bounded synthetic seed required")
        if set(self.seed_ids) & set(self.special_ids):
            raise ValueError("synthetic seed must not contain special/padding/EOS tokens")
        repetitions, prefix = divmod(INPUT_TOKENS, len(self.seed_ids))
        expected = self.seed_ids * repetitions + self.seed_ids[:prefix]
        if self.input_ids != expected:
            raise ValueError("exact repeated-seed geometry required; no padding or truncation")

    @property
    def output_tokens(self) -> int:
        return 512 if self.role == "agent" else 128

    def receipt(self) -> dict[str, str | int]:
        return {
            "protocol": "context_geometry_v1",
            "construction": "encode_no_specials_repeat_then_seed_prefix_v1",
            "role": self.role,
            "tokenizer_identity": self.tokenizer_identity,
            "vocab_size": self.vocab_size,
            "seed_text_sha256": hashlib.sha256(SEED_TEXT.encode()).hexdigest(),
            "seed_token_count": len(self.seed_ids),
            "seed_ids_sha256": digest_ids(self.seed_ids),
            "special_ids_sha256": digest_ids(self.special_ids),
            "input_tokens": len(self.input_ids),
            "input_ids_sha256": digest_ids(self.input_ids),
            "required_new_tokens": self.output_tokens,
            "scope": "Synthetic token geometry, not natural chat-context utility",
        }


def build_geometry(tokenizer: GeometryTokenizer, role: Role, identity: str) -> InputGeometry:
    """Encode the fixed public seed once; never tokenize a benchmark/user request."""
    vocab_size = len(tokenizer)
    seed = tokenizer.encode(SEED_TEXT, add_special_tokens=False)
    special = tokenizer.all_special_ids
    if type(seed) is not list or type(special) is not list:
        raise ValueError("flat tokenizer ID lists required")
    if not 1 <= len(seed) <= INPUT_TOKENS:
        raise ValueError("nonempty bounded synthetic seed required")
    repetitions, prefix = divmod(INPUT_TOKENS, len(seed))
    return InputGeometry(
        role,
        identity,
        vocab_size,
        tuple(seed),
        tuple(special),
        tuple(seed * repetitions + seed[:prefix]),
    )


def summarize_generation(
    geometry: InputGeometry,
    sequence_ids: list[int],
    *,
    cache_length_after_generation: int | None,
    cache_length_after_final_forward: int | None = None,
) -> dict[str, str | int | bool | None]:
    """Only counts/hashes survive; the caller must never decode or retain text.

    Generation normally emits the last token without forwarding it into cache.
    A separate final-token forward must be actually observed before claiming
    cache coverage of the full input+output boundary. This helper performs no
    forward and provides no assertion about resident bytes or continuous peak.
    """
    expected_length = INPUT_TOKENS + geometry.output_tokens
    if (
        type(sequence_ids) is not list
        or len(sequence_ids) != expected_length
        or not _valid_ids(sequence_ids, geometry.vocab_size)
        or tuple(sequence_ids[:INPUT_TOKENS]) != geometry.input_ids
    ):
        raise ValueError("exact unchanged input prefix and forced output length required")
    if cache_length_after_generation is not None and (
        type(cache_length_after_generation) is not int
        or cache_length_after_generation != expected_length - 1
    ):
        raise ValueError("native generation cache boundary mismatch")
    if cache_length_after_final_forward is not None and (
        cache_length_after_generation is None
        or type(cache_length_after_final_forward) is not int
        or cache_length_after_final_forward != expected_length
    ):
        raise ValueError("separate final-forward cache boundary required")
    return {
        "protocol": "context_generation_geometry_v1",
        "role": geometry.role,
        "input_tokens": INPUT_TOKENS,
        "new_tokens": geometry.output_tokens,
        "sequence_tokens": len(sequence_ids),
        "sequence_ids_sha256": digest_ids(tuple(sequence_ids)),
        "output_ids_sha256": digest_ids(tuple(sequence_ids[INPUT_TOKENS:])),
        "cache_length_after_generation": cache_length_after_generation,
        "cache_length_after_final_forward": cache_length_after_final_forward,
        "full_boundary_cache_observed": cache_length_after_final_forward == expected_length,
        "generated_text_retained": False,
        "scope": "Caller-supplied token/cache observations, not GPU allocation certification",
    }
