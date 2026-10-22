# Phase 5 native delivery failure: root cause and acceptance repair

Date: 2026-09-29. This note isolates transport/lifecycle failure from the
security-policy result. It does not change either native closure epoch and does
not use Test data or private ground truth.

## Observed failure

The first native closure epoch completed all seven levels for C1--C3. The next
condition, `c4_email_private__A0`, reached two successful Qwen agent responses:
`doc_read` and `send_email_mock`. The mock tool execution is present in the
security trace. The third agent completion did not return a structured response;
the host marked the condition `model_error` with
`remote_delivery_uncertain=true`. The recovery epoch reproduced the same
condition boundary in a fresh journal. Its artifact and journal are retained:

- `build/evaluation/phase5_native_closure01/conditions/c4_email_private__A0`
- `build/evaluation/structured_api_sessions_phase5_closure01_20260929/`
- `build/evaluation/phase5_native_closure_recovery01/conditions/c4_email_private__A0`
- `build/evaluation/structured_api_sessions_phase5_closure_recovery01_20260929/`

The detailed trace records the transport exception as `HTTP_ERROR`; the durable
v1 journal intentionally records only `state=uncertain`, request hash and
identity. It never writes the HTTP body, API key, prompt or exception text.
The v3 transport keeps this boundary for proxy failures too: a non-JSON HTTP
error such as an HTML 530 response is classified as `HTTP_ERROR` with its
numeric status only; the body is discarded.

## Root cause

The deployed `structured_api_v1` worker exposes only `GET /v1/models` and
`POST /v1/chat/completions`. It has an in-memory request-id cache of 64 entries,
but it does not expose an authenticated status route or a boot instance ID.
After a response-delivery failure the host therefore cannot distinguish these
states:

1. generation completed and only the response was lost;
2. the request is still running;
3. generation failed before the worker cached a result; or
4. the worker/tunnel became unavailable.

The host `SessionJournal` correctly treats all four possibilities as
uncertain. It writes a durable started/uncertain pair and refuses every later
POST, including a different task or request ID. A health probe cannot resolve
the old request. Replaying the POST is unsafe because the v1 cache can evict an
ID and silently execute the prompt again; the 84-condition closure also exceeds
the 64-entry cache bound. This is an evidence/lifecycle limitation, not a
security-policy decision and not a reason to weaken A0--A6 controls.

## Correct repair

The repair is a new versioned worker/session, never an edit to the v1 epochs:

1. Use the CPU-tested request-worker v3 candidate in
   `src/react_agent/serving/request_lifecycle_v3.py`,
   `src/react_agent/serving/request_http_v3.py`,
   `src/react_agent/serving/quiescent_engine_v3.py` and
   `src/react_agent/serving/request_worker_v3.py`.
2. Probe an authenticated `/models` response and bind every route to the fresh
   boot `instance_id`, static source/model/session identity and model revision.
3. Persist started and terminal lifecycle receipts before admitting another
   request. Use a bounded no-eviction request table; refuse new IDs at
   capacity rather than silently reusing an old ID.
4. Expose authenticated `GET /v1/requests/{request_id}`. The response must
   include exact request hash, terminal state, engine-returned/inactive flags,
   durable receipt, quiescence evidence, instance-retired flag, HTTP status and
   response hash. Pending, unknown, mismatched or retired requests remain
   unresolved.
5. Let the host journal use `recover_cached` only after that exact terminal
   status is verified. It may issue the same request ID solely to retrieve the
   worker's cached response; the request hash, status and response hash must
   agree. This is delivery reconciliation, never semantic retry or prompt
   mutation. The original uncertain record remains immutable and a separate
   recovered receipt is appended.
6. Submit and discover the v3 package once per role with a new source/session/
   boot identity, perform exact package QA and health checks, then run a fresh
   predeclared Dev closure. Preserve both v1 epochs as historical evidence and
   do not merge their raw journals into the v3 journal.

The v3 lifecycle, HTTP, host journal and reconciliation controls already have
CPU evidence in
`docs/evaluation/request_worker_v3_cpu_report.md` and
`docs/evaluation/phase5_restart_recovery_20260929.md`. The v1-specific
regression test
`tests/unit/test_session_journal_v1.py::test_http_530_delivery_failure_is_uncertain_and_never_replayed`
locks the exact fail-closed behavior observed here.

## Acceptance boundary

Phase 5 may be considered for acceptance only after the new native run has
complete, non-uncertain condition evidence and the independent 20-item DoD
evaluator passes. A complete matrix with a terminal transport proof is still
not sufficient if negative controls, provenance/final-sink checks, identity,
hashes or Test-sealing checks fail. The old v1 `HTTP_ERROR` condition cannot be
converted into a pass by deleting its journal, changing the request ID, using a
new health result, or replaying the prompt.
