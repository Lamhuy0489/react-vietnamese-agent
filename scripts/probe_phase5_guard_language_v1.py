"""Exhaustively check the finite language using synthetic ASCII-pair tokens only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.guard_token_language_v1 import compile_language, documents
from react_agent.security_v1.guard import parse_guard


class SyntheticCodec:
    def encode(self, text: str) -> list[int]:
        if not text.isascii():
            raise ValueError("synthetic ASCII only")
        return [
            128 + ord(text[i]) * 128 + ord(text[i + 1]) if i + 1 < len(text) else ord(text[i])
            for i in range(0, len(text), 2)
        ]

    def decode(self, tokens: list[int]) -> str:
        return "".join(
            chr(t) if t < 128 else chr((t - 128) // 128) + chr((t - 128) % 128) for t in tokens
        )


def probe() -> dict[str, Any]:
    language = compile_language(
        SyntheticCodec(),
        tokenizer_sha256=text_hash("synthetic_ascii_pair_v1"),
        vocabulary_size=16512,
        eos=(0, 1),
    )
    traversals = 0
    for text, tokens in zip(documents(), language.sequences, strict=True):
        parse_guard(text)
        for i, token in enumerate(tokens):
            allowed = language.allowed(tokens[:i])
            if token not in allowed or set(allowed).intersection(language.eos):
                raise ValueError("incorrect prefix constraint")
            traversals += 1
        if language.allowed(tokens) != language.eos:
            raise ValueError("terminal must allow EOS only")
        for eos in language.eos:
            language.verify_completion((*tokens, eos))
    return dict(
        protocol="guard_token_language_synthetic_probe_v1",
        valid=True,
        codec="synthetic_ascii_pair_v1",
        identity_sha256=language.identity_sha256,
        schema_value_combinations=len(language.sequences),
        trie_nodes=len(language.edges),
        prefix_membership_checks=traversals,
        terminal_eos_checks=len(language.sequences) * 2,
        max_response_tokens_with_eos=max(len(t) + 1 for t in language.sequences),
        phase5_accepted=False,
        native_tokenizer_validated=False,
        native_generation_validated=False,
        guard_quality_validated=False,
        model_inference_runs=0,
        test_payload_accessed=False,
        private_ground_truth_accessed=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    no_links(args.output)
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or not args.output.resolve().is_relative_to(root / "results"):
        raise ValueError("fresh receipt under results required")
    result = probe()
    write_receipt(args.output, result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
