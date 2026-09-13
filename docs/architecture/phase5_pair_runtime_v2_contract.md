# Pair/runtime v2 — failure evidence contract

Versioned successor to the bounded CPU02 v1 snapshot; old source and raw evidence
remain unchanged. Public `run_pair_task` arguments and the security v7 loop are
unchanged. No model, prompt, policy, decoding, dataset or Tool Broker change.

- Each host role proposal binds a half-open range in the existing pair event
  ledger, in addition to before/after worker-attempt counts and request hashes.
  A worker can return OK and the pair can then fail its sibling liveness check.
  Preserve worker OK, host ERROR and the pair generate ERROR event independently;
  do not promote a discarded worker response to a successful runtime model call.
- The joined auditor requires matching pair events, non-overlapping ranges,
  complete generate-event coverage and a consistent error class. A retired pair
  may reject a host proposal with no new pair event or worker attempt. Host OK
  can never explain worker ERROR. No raw evidence is rewritten during audit.
- `startup_completed` is an explicit boolean. `startup_seconds` measures elapsed
  initialization on success, load failure and interruption, before outer cleanup.
  Pair startup failure may include its own internal cleanup. Worker attempt
  timings remain separate; do not interpret this interval as weight-load time.
  Total time must contain startup, runtime (including inner cleanup), and outer
  cleanup intervals. Validation failures before output allocation leave no run.
- Receipt profile is `model_pair_security_runtime_v2`; guard row structure stays
  `guard_trace_pair_v1` because READY/transport numbering is unchanged.

CPU acceptance: real-spawn all-level regression/parity, startup failure timing,
actual process termination after a worker response (both roles and either
worker), pre-dispatch rejection, mutation-negative ledger/timing audits, full
development QA and prior/current source/raw/data integrity. These tests do not
prove native GPU memory recovery, guard quality or complete Phase 5 acceptance.
