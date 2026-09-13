# Phase 5 — observed worker shutdown v2

Standalone, opt-in worker. Do not rewrite frozen `warm_guard.py`, ModelPair,
runtime v7, native loaders or the seven-level calculator pilot. No policy,
model, tool, prompt, decoding or benchmark change. No new Test access.

`ShutdownConfig` extends the frozen warm execution config with a separately
hashed `graceful_shutdown_seconds` (default 2 seconds). Cancellation still uses
the original terminate/kill budgets; errors/timeouts never wait for normal stop.
`ShutdownBackend` retains ownership, idle-lock, byte bounds, request sequence,
retirement and no-retry behavior. AST regression checks the copied `generate`
method against v1 except its observed worker target/two shared timestamp values.

The target wraps v1 `_serve`. A stop-event facade timestamps the first positive
stop observation without changing transport/generation. A finally block records
return from `_serve`, including local-reference teardown. This return is not a
CUDA-recovery or multiprocessing-finalizer acknowledgement. No backend close
method is invented; Python teardown may still hang and require cancellation.

Lifecycle schema `worker_shutdown_v2` retains method/PID/reaped/exit/timing and
adds stop-request, stop-observed and serve-returned observations. GRACEFUL
requires a requested/observed stop, observed serve return, process exit 0 and
successful reap. An acknowledged `os._exit(0)` without observed return is EXITED,
not GRACEFUL. Bounded fallback remains TERMINATE then KILL. Never-started close
does not manufacture a lifecycle/acknowledgement.

CPU scope: normal and slow teardown, old short-budget control, acknowledged but
hung destructor, SIGTERM-ignoring destructor, nonzero/abrupt-zero exit, backend
failure, timeout, never-started close, owner/idle restrictions, frozen transport
AST equivalence and malformed receipt negatives. All fixtures are synthetic;
timestamps are observable milestones, not model reasoning.

This does not identify the native v1 forced-cleanup cause, prove native resource
cleanup, integrate v2 into ModelPair/runtime, or close Phase 5. Before GPU:
version the pair/agent-only wiring and auditor together, freeze input identities,
rehearse exact mounts, then run a predeclared separate lifecycle diagnostic.
Do not rerun the calculator semantic outcome or silently increase final-benchmark
budgets. Stop budget must be equal across compared configurations when adopted.
