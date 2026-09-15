"""Opt-in finite guard token language; no model loading or output repair."""

from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import product
from typing import Protocol

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.guard import GuardResult, parse_guard

PROFILE = "guard_token_language_v1"
RISKS = ("SAFE", "SUSPICIOUS", "MALICIOUS")
LABELS = (
    "instruction_override",
    "external_exfiltration",
    "unauthorized_action",
    "control_influence",
)
CONFIDENCES = ("LOW", "MEDIUM", "HIGH")


class Codec(Protocol):
    """Caller binds an authenticated tokenizer; encode must not add special tokens."""

    def encode(self, text: str) -> list[int]: ...

    def decode(self, tokens: list[int]) -> str: ...


class TokenRow(Protocol):
    def tolist(self) -> list[int]: ...


def documents() -> tuple[str, ...]:
    """All 3,069 schema value combinations, including ordered/repeated labels."""
    return tuple(
        json.dumps(dict(risk=risk, labels=labels, confidence=confidence), separators=(",", ":"))
        for risk in RISKS
        for size in range(5)
        for labels in product(LABELS, repeat=size)
        for confidence in CONFIDENCES
    )


def _tokens(tokens: tuple[int, ...], vocabulary_size: int) -> None:
    if type(tokens) is not tuple:
        raise ValueError("immutable token tuple required")
    if any(type(token) is not int or not 0 <= token < vocabulary_size for token in tokens):
        raise ValueError("invalid token identifier")


@dataclass(frozen=True)
class TokenLanguage:
    edges: tuple[tuple[tuple[int, int], ...], ...]
    terminals: frozenset[int]
    sequences: tuple[tuple[int, ...], ...]
    eos: tuple[int, ...]
    vocabulary_size: int
    max_new_tokens: int
    identity_sha256: str

    def _node(self, prefix: tuple[int, ...]) -> int:
        _tokens(prefix, self.vocabulary_size)
        node = 0
        for token in prefix:
            following = dict(self.edges[node]).get(token)
            if following is None:
                raise ValueError("prefix outside constrained language")
            node = following
        return node

    def allowed(self, prefix: tuple[int, ...]) -> tuple[int, ...]:
        node = self._node(prefix)
        result = tuple(token for token, _ in self.edges[node])
        if node in self.terminals:
            result += self.eos
        if not result:
            raise ValueError("unsatisfiable token constraint")
        return result

    def verify_completion(self, generated: tuple[int, ...]) -> None:
        """Reject truncation, early EOS, trailing bytes and off-language sequences."""
        _tokens(generated, self.vocabulary_size)
        if not 2 <= len(generated) <= self.max_new_tokens or generated[-1] not in self.eos:
            raise ValueError("complete bounded response with EOS required")
        if self._node(generated[:-1]) not in self.terminals:
            raise ValueError("EOS before complete JSON")

    def request(self, prompt_tokens: tuple[int, ...]) -> PrefixConstraint:
        _tokens(prompt_tokens, self.vocabulary_size)
        if not prompt_tokens:
            raise ValueError("explicit prompt tokens required")
        return PrefixConstraint(self, prompt_tokens)


@dataclass(frozen=True)
class PrefixConstraint:
    language: TokenLanguage
    prompt_tokens: tuple[int, ...]

    def __call__(self, batch_id: int, input_ids: TokenRow) -> list[int]:
        # Only the predeclared single-sequence greedy mode is supported.
        if type(batch_id) is not int or batch_id != 0:
            raise ValueError("single batch required")
        values = tuple(input_ids.tolist())
        _tokens(values, self.language.vocabulary_size)
        count = len(self.prompt_tokens)
        if values[:count] != self.prompt_tokens:
            raise ValueError("request prompt identity changed")
        return list(self.language.allowed(values[count:]))


def compile_language(
    codec: Codec,
    *,
    tokenizer_sha256: str,
    vocabulary_size: int,
    eos: tuple[int, ...],
    max_new_tokens: int = 128,
) -> TokenLanguage:
    """Reject the entire language if any schema value cannot fit; never prune labels."""
    if len(tokenizer_sha256) != 64 or any(c not in "0123456789abcdef" for c in tokenizer_sha256):
        raise ValueError("explicit tokenizer hash required")
    if type(vocabulary_size) is not int or vocabulary_size <= 0:
        raise ValueError("positive vocabulary size required")
    if type(max_new_tokens) is not int or not 2 <= max_new_tokens <= 128:
        raise ValueError("bounded generation budget required")
    _tokens(eos, vocabulary_size)
    if not eos or tuple(sorted(set(eos))) != eos:
        raise ValueError("unique sorted EOS identifiers required")
    texts = documents()
    edges: list[dict[int, int]] = [{}]
    terminals: set[int] = set()
    sequences = []
    for text in texts:
        parse_guard(text)  # Frozen parser is also the admission boundary.
        tokens = tuple(codec.encode(text))
        _tokens(tokens, vocabulary_size)
        if not tokens or len(tokens) + 1 > max_new_tokens or any(t in eos for t in tokens):
            raise ValueError("language exceeds token budget or contains special EOS")
        if codec.decode(list(tokens)) != text or tuple(codec.encode(text)) != tokens:
            raise ValueError("non-exact or unstable tokenization")
        node = 0
        for token in tokens:
            if token not in edges[node]:
                edges[node][token] = len(edges)
                edges.append({})
            node = edges[node][token]
        terminals.add(node)
        sequences.append(tokens)
    if len(set(sequences)) != len(texts):
        raise ValueError("tokenization collision")
    identity = text_hash(
        canonical_json(
            dict(
                profile=PROFILE,
                tokenizer_sha256=tokenizer_sha256,
                schema=GuardResult.model_json_schema(),
                documents_sha256=text_hash(canonical_json(list(texts))),
                sequences_sha256=text_hash(canonical_json([list(s) for s in sequences])),
                vocabulary_size=vocabulary_size,
                eos=list(eos),
                max_new_tokens=max_new_tokens,
            )
        )
    )
    return TokenLanguage(
        tuple(tuple(sorted(edge.items())) for edge in edges),
        frozenset(terminals),
        tuple(sequences),
        eos,
        vocabulary_size,
        max_new_tokens,
        identity,
    )
