# Ordinary-request receipt audit v1

CPU-only milestone, separate from frozen runtime/attention sources. Inputs are
one closed role's attention directory, its original native metrics JSONL,
expected role, worker PID and request count supplied by the caller. No inference,
Test data, token values or model text is needed.

`audit(attention, metrics, *, role, worker_pid, expected_requests)` is read-only.
Require exactly request_000001 through the declared count, each containing only
entered/restored/completed JSON. Partial/error/extra records are rejected, not
retried or silently omitted. Strict JSON rejects duplicate keys and nonfinite
numbers. Expected counts/PID and geometry use strict integers, not bool/float.
Metrics must contain one load followed by exactly one successful generate row
per request, in contiguous call-index order with frozen identity/decoding hash.

Join native input/output token measurements to request input and forward groups;
recompute attention/helper counts and last-forward key length. Restore flags
must match; receipt overclaims of profiling, changed decoding or full KV proof
are rejected. Output-token consistency is now checked against native metrics;
this does not turn a sidecar into independently authenticated execution proof.
Native load and generation/call durations must be positive finite numbers, with
generation duration at most call duration. Preserve per-request observations
and load time separately, never label their sum as full task wall time.

Bind input hashes before and after reading; forbid symlinks, extra directories,
overlapping inputs and output within either input. The CLI writes a fresh
receipt only after the audit succeeds. Never rewrite source metrics or sidecars.

Scope limits: no native source/remote provenance authentication, supervisor PID
binding, resolved publisher policy, native memory/placement admission, profiler
dispatch, full-boundary KV, A/B/A numerical statelessness or task cleanup proof.
The caller-supplied PID is an expectation, not a supervisor lifecycle audit.
Unknown native metric metadata is not copied to the output; original metrics
remain hash-bound. Runtime integration and GPU preflight must add those checks.
No Phase 5 acceptance or benchmark quality/security/latency claim.
