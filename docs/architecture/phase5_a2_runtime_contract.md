# Phase 5 A2 integration contract v2

Implementation scope: new files only; selected v1 source, rules, prompt, parser,
configuration and receipts stay byte-identical. No held-out payload access or
benchmark tuning. This is local architecture QA, not guard quality acceptance.

## Gates

- A0/A1 retain the v1 policy and exact agent messages/observable behavior.
- A2 runs the frozen A1 component plus the frozen ModelGuard on each proposed
  action (Pre) and source-native tool-result JSON (Post). Guard input contains
  only raw user instruction, source type, and the current candidate. It cannot
  receive evaluator ground truth or development memory.
- MALICIOUS and errors on observed sources remain sticky for this task. Either
  signal, or a MALICIOUS/error current action, denies external mock sinks before
  Broker execution. SAFE later does not erase earlier signals. SUSPICIOUS is
  recorded/TAG only. Reads remain allowed, including guard failures. A1 denials
  are never undone by the guard or by raw-user authorization anchors.
- This coarse source veto is intentionally conservative, not value-origin proof;
  A6 will need its own adjudication contract. Final is still pass-through, not
  final-answer leak protection. A3–A6 remain rejected.
- One fresh guard/cache/policy per task. Guard decisions and timing are sidecar
  records only, never added to the agent prompt. Generic denial feedback stays v1.

## Bounded local inference

The host supplies a spawn-picklable, no-argument factory that constructs the
backend **inside** a new local child process. Never pass a loaded GPU model, fork
CUDA, or use a thread timeout. The child must own all inference; remote requests,
detached jobs and descendant worker processes are outside this adapter's contract.
No model download or account operation is performed by this implementation.

Each uncached classification spawns one process; the deadline includes startup,
model loading and generation. On expiry, terminate then kill/reap with separately
bounded grace periods; retire the backend after infrastructure failure. There is
no automatic retry/restart. Parent reads a bounded shared-memory JSON response
only after child exit, avoiding a potentially blocking partial pipe read. Child
stdout/stderr and exception text are not retained. Only observable typed results,
error codes, identity, hashes and host wall-clock durations enter the sidecar.

Cold loading every cache miss is deliberate for this first safe adapter: durations
are **end-to-end cold guard latency**, not token throughput or warm GPU latency.
Do not use these CPU fake-backend results to claim model efficiency. A persistent
GPU worker would require a separately tested lifecycle/version before experiments.
Backend identity is explicitly supplied and checked before and after generation;
an immutable production model revision still needs selection and verification.

## Acceptance for this bounded milestone

Synthetic tests must cover process timeout/reaping, crash/invalid output, identity,
cache/no retry, malicious/suspicious/error Pre/Post, sticky/fresh state, cumulative
A1, no denied Broker call, trace linkage, A0/A1 differential parity, and all normal
quality gates. No real guard model or full Phase 5 acceptance is implied.
