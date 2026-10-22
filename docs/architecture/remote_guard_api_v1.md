# Remote guard API transport v1 candidate

Scope: Phase5 host integration over the unchanged structured API worker. No Test,
GT, model/prompt/threshold changes or notebook resubmission. Not acceptance.

1. `SessionJournal(transport, root, identity, task_id)` wraps only GET/models and
   POST/chat/completions. Identity binds role/session/model/source/worker. Under
   a per-session OS lock it durably records request ID/hash before any POST.
2. A valid transport response records `response_received`, not semantic success.
   Exceptions record `uncertain`; process death leaves a started-only record.
   Either state blocks future POSTs for that session, across tasks/processes.
   There is no automatic retry, ledger reset, or inference-producing recovery.
3. `StructuredSessionFactory` carries local file paths, hashes and public pins,
   never an SSLContext, open socket or API key. It constructs and probes the HTTP
   backend inside the spawned guard process. Per-task ModelGuard cache is fresh.
4. The existing public SecurityRuntime.run_instrumented owns WarmGuardBackend.
   Reaping/termination refers only to the host HTTP process. Remote GPU cancellation
   is unsupported by this worker API. A versioned public wrapper annotates this
   distinction; no direct `_run_task` invocation or policy bypass.
5. Agent uses the same durable transport, without a new security defense in A0.
   Checkpoint/identity/network-failure bookkeeping is common to every level.
6. CPU controls cover success, timeout, interruption, stale started records,
   duplicates, concurrent attempts, identity mismatch, fresh tasks and A0–A6
   dispatch. Native inference must have a separate prospective declaration.

Boundaries: an HTTP socket timeout is not a total request deadline. The local
WarmGuardBackend adds a process deadline; a timeout still leaves remote work
uncertain. SessionJournal provides admission/delivery evidence, not remote
cancellation, external-client exclusion or exactly-once execution. `/models`
readiness cannot clear an uncertain inference record. Interrupted network writes
may reach the server; retain every attempt. Existing server generation limit90s
is not an independent proof of completion. Phase5 lifecycle acceptance stays open.
