# Task-local warm guard v1

Phase 5 lifecycle optimization, not guard-model selection or GPU evidence.
New modules/version only; all previous source/receipts stay immutable.
Reuse model weights within ONE task, never a worker/cache across tasks.

## Execution boundary

- Spawn lazily on the first cache miss, load the explicitly pinned backend once.
  Each request passes the full frozen guard prompt/input/generation. The backend
  must not retain conversational/KV history between generate calls; real-model
  adapter conformance remains required. Warm worker alone cannot prove this.
- Bounded shared-memory JSON request (128 KiB) and response (64 KiB), sequence
  IDs and synchronization events; no executable deserialization of child output.
  Single in-flight request; concurrent calls rejected, not queued. Host-only
  factory is necessarily spawn-serialized; never supplied by model/tool text.
- Same inclusive request deadline as the cold worker: first request includes
  process startup + model load + generation, subsequent requests include transfer
  and generation. Log total request latency and child startup/generation timing,
  cold/warm flag, request/generation/config hashes, PID and exit/cleanup outcome.
  Do not report warm timing alone as end-to-end throughput.
- Verify backend and response identities before/after every generation. Crash,
  timeout, backend exception, oversized/invalid packet or identity drift retires
  the worker. No automatic restart/retry. Invalid guard JSON also retires the
  warm worker and clears cache. Check liveness before serving any cached SAFE.
- Timeout/interrupt cleanup uses terminate, bounded join, kill, bounded join and
  reap. No response is accepted when cancellation fails. Keep a live process
  handle if cleanup fails so close can retry; do not claim it was reaped.
- Explicit close/context manager handles graceful idle shutdown, then forced
  cleanup if necessary. Close during an in-flight request is rejected; timeout
  or owner-thread interruption is the supported cancellation mechanism. Host
  process hard-kill/orphan recovery is outside this local lifecycle contract.

## Runtime integration

Versioned v5 uses the same A0–A6 policies and tool loop as v4, with a task-owned
warm guard. Close on successful/failed terminal paths and unexpected exceptions;
record lifecycle metadata after close. A0/A1 never instantiate a guard. Freeze
new runtime/lifecycle identity; do not combine cold/warm latency as one method.
Guard prompt, parser, generation, rule/policy profiles and dataset remain fixed.
Retirement on malformed guard output is a predeclared fail-closed lifecycle
change; valid deterministic trajectories must retain v4 observable behavior.
A6 Post envelopes contain run-local source IDs. Cross-run comparison renames
only that host field using its source ID/type/hash/step/labels; all other context
bytes, raw saved contexts, tool results and released answers remain compared.

## Acceptance and limits

Synthetic tests: one load/multiple distinct requests, cache without generation,
identity drift, cold/warm timeouts, crash, oversized input/output, invalid output,
cache invalidation after idle death, no retry, graceful and forced cleanup,
context-manager exception cleanup, per-task isolation and runtime parity.
Verify setup/Ruff/mypy/full pytest, frozen-source hashes and Test seals (hash only).
Synthetic timing is diagnostic, never model/GPU performance or benchmark ASR.
Production guard model/revision, GPU memory fit, warm backend statelessness and
grouped Dev evaluation remain open. No hidden chain-of-thought or Test payloads.
