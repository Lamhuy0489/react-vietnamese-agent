# Phase 5 — finite guard token language v1

2026-09-16. Isolated CPU development candidate following the
[failed prompt-only diagnostic](../evaluation/phase5_guard_bare_json_terminal_v1.md).
Not an adopted security architecture, new inference run or final freeze.

## Scope and interface

New `llm/guard_token_language_v1.py` only; frozen guard/parser/runtime and raw
evidence remain unchanged. `compile_language(codec, tokenizer_sha256,
vocabulary_size, eos, max_new_tokens=128)` builds an immutable token trie.
`request(prompt_tokens)` creates a request-local callback taking batch ID and a
1D token row with `tolist()`. Only batch ID 0 / single-sequence greedy generation
is supported. The exact prompt token prefix must match, then only generated
tokens are traversed. No candidate text, expected label or evaluator input
selects the grammar. `verify_completion` rejects incomplete/out-of-language output.

The language contains all 3 × 3 × (1+4+16+64+256) = 3,069 combinations admitted
by the current enums and 0–4 labels. Ordered and repeated labels remain allowed;
no semantic filtering such as “SAFE must have empty labels” is introduced.
Serialization has exactly risk, labels, confidence in that order, compact ASCII
JSON, no extra text. Alternative whitespace/key-order/token segmentations are
excluded intentionally; the strict parser itself is unchanged.

Compilation requires exact deterministic encode/decode round trips, valid token
IDs, no EOS within content and every possible response plus one EOS fitting the
budget. If any combination is too long, reject the entire language, not only
that combination. Hash identity binds profile/schema/texts/token paths/tokenizer,
vocabulary/EOS/budget. A supplied tokenizer hash is a binding, **not proof** that
tokenizer files were authenticated; native admission must establish that proof.

EOS becomes permissible only after a complete object; invalid prefixes raise
instead of returning an unrestricted vocabulary. No stripping, extraction,
repair, retry, hidden reasoning or raw model response retention. New candidate
generation distribution differs from unconstrained decoding and requires its
own run/cache/policy identity; do not reuse the prompt-only candidate identity.

## Completed CPU acceptance

The executable probe uses a labelled synthetic reversible ASCII-pair codec,
not a pretrained tokenizer or a model. Exhaustively verify every response and
prefix with the frozen parser, terminal EOS, and absence of extra trie paths.
Negative controls cover fenced text, truncated/early EOS/trailing output,
invalid IDs, budget failure, wrong codec, changed prompt, batch and mutable state.
Two probe summaries must be byte-identical; preserve failure/history artifacts.
No benchmark Test, private ground truth, model weights, GPU or networked tools.

## Required before native inference

1. Authenticate pinned Qwen tokenizer files and EOS/vocabulary metadata; compile
   all 3,069 paths with the actual no-special-token codec within the 128 budget.
2. Test the actual pinned Transformers 5.5 processor on CPU with synthetic logits:
   forbidden-token masking, conflicting processors, EOS, prompt slicing and
   exception restoration. The current pure-Python callback alone cannot prove
   native masking or generation behavior. Do not use continuous batching.
3. Add opt-in guard-only native adapter, source/policy/witness metrics and
   independently audited constrained-generation identity. Keep agent generation,
   model revisions, bare-JSON prompt, parser, fallback and shutdown2s unchanged.
   No implicit fallthrough to unconstrained generation on failure.
4. Freeze a separate native protocol and exact package with archive/expanded
   preflights and the actual launcher audit invocation. Then GitHub source and
   live private-resource/quota checks precede a fresh notebook, never bare-json-v2.
5. Retain every result and measure grammar setup, callback/generation/startup/
   end-to-end time separately. Format success is not guard classification quality,
   representative utility, ASR/FPR or Phase5 acceptance. Shutdown study stays separate.

## Claim-to-evidence note

Hugging Face, *Transformers v5.5.0 source* (2026), accessed 2026-09-16:
[PrefixConstrainedLogitsProcessor](https://github.com/huggingface/transformers/blob/v5.5.0/src/transformers/generation/logits_process.py)
uses a callback to restrict allowed next-token IDs. This directly supports the
proposed callback interface, not correctness of our native integration.
[Generation utilities](https://github.com/huggingface/transformers/blob/v5.5.0/src/transformers/generation/utils.py)
wire this processor into generation and reject this callback in continuous
batching. Other processors can follow the prefix restriction; interaction checks
remain required. Inferring that our finite trie will constrain the pinned native
guard is a design hypothesis until those tests and inference evidence exist.
The candidate is development work, not a change to the frozen research scope.
