# Phase 5 — observed-shutdown runtime integration v3

2026-09-14. CPU integration scope; not a native package or Phase 5 freeze.

## Versioned interfaces

- `ShutdownPairConfig` extends frozen PairConfig with a separately hashed normal
  shutdown budget. `ShutdownPair` constructs two ShutdownBackend workers directly;
  it inherits frozen start/generate/close/ownership/fail-stop methods. Snapshot
  protocol is `model_pair_shutdown_v2`; no legacy workers are allocated then swapped.
- `AgentWorkerConfig` supplies separate startup and call deadlines plus the same
  graceful/terminate/kill budgets. Default agent deadlines 1200s/180s now match
  paired agent defaults. This is a new execution identity, not a rewrite of the
  historical 1200s single-deadline calculator pilot.
- `pair_runtime_v3.run_pair_task` accepts only these typed configurations and
  pair, uses ShutdownBackend also for A0/A1, and switches to warm deadline after
  the host READY acknowledgement. A0/A1 allocate no guard. V7 security logic,
  model prompts, tools, decoding and final/scope behavior are unchanged.
- Dedicated receipt profile `model_pair_security_runtime_v3`. The independent
  auditor retains v2 host/worker/failure/gate joins and adds cold/warm execution
  hashes, pair protocol/config/owner, sibling PID isolation, READY identity and
  shutdown-event PID/grace binding. A single event's ACK is never GPU proof.

## Acceptance for this bounded CPU milestone

Seven-level observable/context parity and four terminal states; startup and
generation failure, separate agent-only timeout, post-response death for both
roles/victims, interrupted guard startup, invalid-guard retirement, external sink
veto, entitlement/scope regressions. Pair-role slow/hung teardown and mutation
controls preserve original raw files. Full repository quality checks and source/
raw/data re-audit must pass before selecting a receipt.

All data are synthetic fixtures; no Test/private ground truth parsing, native
model load or GPU submission. Native factory composition/package is still old
until separately versioned and rehearsed; do not pass this pair into frozen
native auditors and relabel their output. Preserve all previous source/receipts.

Remaining: native pair/agent-only factory wiring, exact mount package preflight,
versioned native/release auditor, new predeclared lifecycle/guard-path diagnostic,
grouped Dev guard quality and formal freeze. Do not retry the old calculator
semantic outcome or claim default 2s graceful budget fixes native teardown.
