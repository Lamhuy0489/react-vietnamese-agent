# Phase 5 — finite token-language CPU evidence

2026-09-16. Source `2017e2468467cf3d13d4facbc60e977562e9fd8d`.
[Design, interfaces and primary-source evidence](../architecture/phase5_guard_token_language_v1_contract.md).

Implemented an opt-in immutable token trie and request-local prefix callback.
It restricts the next token rather than extracting/repairing a generated JSON
object. No current model/backend/runtime is switched to this candidate.

The synthetic ASCII-pair probe checks all 3,069 schema value combinations,
202,846 prefix-membership assertions and 6,138 terminal/EOS completions.
The trie contains 30,016 nodes; the longest synthetic response including EOS
is 76 tokens. This is **not a Qwen token count** or native model result.
Ordered/repeated labels and every risk/confidence value remain reachable.
Full trie traversal in tests excludes unexpected terminal paths.

46 focused tests passed (30 new), including prompt/batch/state isolation,
malformed/early/truncated/trailing output rejection, tokenizer mismatch,
identity changes and whole-language budget rejection. Setup, Ruff and mypy
(420 source files) passed. Full pytest was excluded because it includes
Test-assigned authoring fixtures; these tests use synthetic controls only.

[Frozen CPU receipt](../../experiments/manifests/phase5_guard_token_language_cpu01.json)
records the exact Git source, source/log hashes, command timing and two
byte-identical probes. Committed-source runs are
`results/phase5_guard_language_cpu03.json` and `..._cpu04.json`;
working-tree checks01/02 are retained as development history.
QA logs: `results/phase5_guard_language_qa01`.
175 baseline source pins and 184 prior bare-JSON evidence/source files remain
unchanged. No new inference, GPU, Test/private ground truth or Kaggle submission.

## What remains

This closes only the bounded CPU language component. Local `.venv` has no
Torch/Transformers/tokenizers; no new heavyweight dependency or model was loaded.
Next: authenticate the real Qwen tokenizer, verify every language path within
128 tokens, and test the actual Transformers5.5 prefix masking with CPU synthetic
logits. Then wire an opt-in guard adapter with separate generation/cache/audit
identity and exact package preflight before a new GPU protocol/submission.

Grammar-constrained decoding changes the output distribution; it does not prove
correct risk classification or utility. Phase5 stays 4/7 acceptance groups
(about57%). Do not rerun the closed bare-JSON candidate or submit its preparedv2.
Keep lifecycle wait experiments separate from this decoding candidate.
