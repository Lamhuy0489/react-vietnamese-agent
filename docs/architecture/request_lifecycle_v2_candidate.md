# Request lifecycle v2 candidate — CPU state machine

2026-09-28. This versioned component is not installed in the running Kaggle
worker. Frozen structured_api_v1 and earlier evidence remain unchanged.

`RequestLifecycle.complete(instance_id, body)` admits exactly one engine request
at a time. Client must provide request_id. Persistent started state is fsynced
before engine invocation; state includes only identity/hash and lifecycle fields.
No prompt, model text, key or exception string is persisted. Terminal results
are copied in memory for idempotent repeat delivery. Reused ID with different
request hash conflicts. Capacity exhaustion refuses new IDs rather than evicting
IDs and risking accidental reexecution. Instance storage is single-use.

`status(instance_id, request_id)` is read-only. `cancel` sets a per-request event
and returnsCANCEL_REQUESTED while the engine is still running. It does not report
CANCELLED until the engine callback returns/raises; late generated content is
withheld after cancellation. Cancel after terminal completion preserves the
terminal outcome. Duplicate cancel does not start inference; next request gets
a fresh event. Unknown/stale instance/request identity is rejected.

A completed callback means engine_returned, not GPU quiescence attestation.
The eventual native engine adapter must observe the stop event, synchronize
its native work and record cleanup before reporting quiescence. A hung engine
retains the active slot; cancellation cannot claim success just because the
client asked. Worker/process death leaves started evidence and requires a new
boot instance ID. No automatic recovery/retry within this component.

HTTP candidate implemented in `src/react_agent/serving/request_http_v2.py`:
authenticated GET `/v1/requests/{id}` and POST `/v1/requests/{id}/cancel`, with
`X-Instance-ID` binding on these routes and completion. Authentication precedes
body reading, identity checks and lookup. GET `/v1/models` publishes the random
boot instance ID and explicit public source/session/model pins. Status also binds
the request hash, without exposing prompts/results. Pending cancel returns202;
terminal cancellation returns200 for status and409 for cached completion.
Completion uses a versioned envelope with identity, request status and result;
it is deliberately not accepted by old v1 clients. Body size/framing and duplicate
authorization/instance headers are checked. Access logging is disabled.

A ThreadingHTTPServer adapter supports cancel/status while completion runs.
CPU loopback testing covers that concurrency and cached duplicate delivery. This
is not a production server or a notebook entrypoint: connection/thread limits,
TLS deployment, result-byte limits and native cleanup still need integration.
Old v1 sessions can be reused on notebook restart and cannot attest a unique boot.

Remaining before GPU use: cooperative HF stopping + actual CUDA
quiescence, bounded server result retention, host status reconciliation, exact
standalone package QA, committed source freeze and new notebook version. Do not
point existing v1 clients to this component or mark lifecycle DoD accepted.
