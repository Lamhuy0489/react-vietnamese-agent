# Phase5 — opt-in constrained guard adapter v1

Date: 2026-09-16. Implementation candidate only; not adopted by the paired
runtime and not evidence of native model generation or guard quality.

## Inputs and change boundary

- Continue the [finite language](phase5_guard_token_language_v1_contract.md)
  after [authenticated native CPU compatibility](phase5_guard_language_native_v1_contract.md).
  The admitted Qwen2.5-1.5B tokenizer language has SHA-256
  `f8df0c2892984e8c6520a8e3bcf4e91dc793d8950165e99284c904a93f6bc3fb`.
- New modules only: `llm/constrained_guard_v1.py` and
  `security_v1/constrained_classifier_v1.py`. Do not modify frozen guard loader,
  runtime, parser, bare-JSON prompt, model, retrieval, fallback or shutdown2s.
- Keep existing effective `repetition_penalty=1.1`, not1.0. The one experimental
  change is the finite JSON token restriction. Temperature0 at the backend API
  remains greedy at native generation; inherited sampling parameters are inactive
  and must still match the effective configuration.
- [Selected effective config](../../configs/guard/constrained_v1_effective.json)
  is the resolved configuration from the prior synthetic CALC_A2 guard request
  `results/phase5_guard_bare_json_terminal_error01/raw/observer/tasks/CALC_A2/policy/guard/request_000001/resolved.json`.
  This selection uses configuration metadata, not response labels or evaluator
  ground truth. Canonical JSON SHA-256:
  `231f3e0b7e56f54043efa1002e6d1b37c132a28ca049294a32865d49c7b2efc6`.
  `max_length=20` is the comparison placeholder; the native prepared value must
  first equal input-token count+128. No other effective field is normalized.

## Required behavior

1. Admit a fresh exact `GuardHFBackend` with frozen limits and a fresh separate
   evidence directory. Check Torch2.10.0+cu128/Transformers5.5.0 and native
   processor/generation source hashes. Model weights remain a Kaggle concern.
2. Install only request-local instance hooks under one backend lock and PID /
   thread owner. Reject pre-existing hooks; never mutate class/global methods.
   Admit exactly one native generate call with original input/mask/config.
3. Before returning the logits chain to generation, require the exact ordered
   classes `RepetitionPenaltyLogitsProcessor` then
   `PrefixConstrainedLogitsProcessor`. Admit only penalty1.1 and the exact
   request callback with beam1. Extra/reordered/subclass processors, forced
   tokens, sampling, callback replacement and policy drift are errors.
4. Each generation step must traverse the request's token language with the
   exact prompt prefix. Verify one callback per returned token, valid terminal
   JSON and EOS, and exact decoded-text/token-path correspondence. Reject
   truncation, trailing tokens, off-language output and fences; no repair or
   fallback to unrestricted generation.
5. Verify backend/model/tokenizer/config/response identity before writing
   completion. Always remove installed hooks after success, errors or
   interruption. Retire the adapter and native backend on failure; never retry
   the same retired backend. This does not change worker shutdown behavior.
6. Audit only identities, hashes, stage/counts and exception class; no raw
   candidate text, hidden reasoning, credentials or private ground truth.
   Cache keys bind model/revision, unchanged prompt, API generation, input and
   constrained execution identity (language/tokenizer, policy and source pins).
   Check live native model/tokenizer/config and publisher-policy identity, not
   only public identifier strings, before a cache hit; clear cache on any failure.

## Evidence boundaries and next gate

The generic scope and classifier can be tested with explicitly synthetic CPU
fakes. Fixture-only `object.__new__` bypasses production loader admission to
test lifecycle errors; it cannot certify the constructor's native admission.
The earlier Kaggle test ran actual tokenizer/logits processors, **not these
new hooks or model.generate**. Do not combine those facts into a native-pass claim.

Next: design a separately versioned paired-factory composition with existing
request policy/efficient-request/observer wrappers, then test actual pinned
GenerationMixin invocation and restoration on a bounded CPU fixture. Record
runtime/cache/audit identity end-to-end. Only after that admission prepare an
exact private package and preregister a new bounded GPU diagnostic. GPU quality,
utility and lifecycle evidence remain open. Do not submit old bare-json-v2 or
retry completed semantic failures; no held-out Test access.
