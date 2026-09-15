# Phase5 — constrained guard adapter CPU implementation

2026-09-16. [Contract](../architecture/phase5_constrained_guard_v1_contract.md).

Implemented isolated request hooks for exact repetition1.1 → prefix-constraint
admission, native/effective generation checks, ordered callback accounting,
token/EOS/text completion validation, hook restoration and backend retirement.
The new classifier keeps the bare-JSON prompt and strict parser unchanged and
separates cache identity by constrained decoding configuration.

## Verification

47 new synthetic tests cover success across two requests, conflicting chains,
policy/callback drift, generation bypass, duplicate calls, incomplete/invalid
output, exceptions/interruptions, cache isolation, retirement, and post-generation
model/tokenizer/config/response identity changes. Post-generation faults cannot
leave a completed receipt. Internal model/tokenizer/config/publisher drift cannot
serve a cached success even if public identifiers are unchanged; identity-check
interruption retires the backend. Evidence files do not contain raw candidate text.

[Selected QA receipt](../../experiments/manifests/phase5_constrained_guard_cpu_qa02.json):
source `964c51bac46d06691d1571f404c548f9398a649f`; **340 focused tests/15.57s**
(47 new). Setup, Ruff, mypy426, knowledge-check and diff-check pass. All175
frozen baseline pins and86 native-CPU package source pins remain unchanged.
Full commands and source/log hashes are in the receipt. Raw logs remain under
`results/phase5_constrained_guard_cpu_qa02`; local preliminary QA01 at source
99fb189 (333tests) is preserved but superseded by the live-cache identity checks.
These timings measure local CPU tests, **not model latency or throughput**.
Dirty Phase6–9 plans and the user's progress-report/figures are not candidate inputs.

## Limits

No new Kaggle submission, model loading or GPU inference. The 47 tests use
synthetic codec/model fixtures and do not prove actual GenerationMixin execution.
The adapter has not been wired into the paired factory/runtime/observer auditor;
that integration is the next bounded task. Previous actual tokenizer/248mask
CPU evidence remains [separate](phase5_guard_language_native_v1_run.md).

No held-out Test/private ground truth used; no full-repository pytest because
it includes Test-assigned authoring fixtures. Phase5 remains4/7≈57% acceptance
groups, not complete. Correct JSON alone is not classification correctness,
benign utility, stable graceful shutdown or final freeze.
