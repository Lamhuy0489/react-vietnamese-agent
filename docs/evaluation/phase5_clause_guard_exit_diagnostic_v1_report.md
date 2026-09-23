# Phase 5 Dev32 v2 — guard process exit diagnostic

2026-09-23. The read-only [protocol](phase5_clause_guard_exit_diagnostic_protocol_v1.md)
and [script](../../scripts/diagnose_phase5_clause_guard_exit_v1.py) examined
all 32 authenticated public Dev task receipts, joining pair shutdown snapshots
to observed worker milestones. Two runs from the independent terminal audits
were byte-identical (SHA-256
`1ced49b8d0adecbf5ced88b9f674cc8ea15849c7383eb1b9e6f2281ebdbbcb54`).
[Receipt](../../experiments/manifests/phase5_clause_guard_exit_diagnostic_v1_receipt.json)
links the generated JSON. No new inference, Test/oracle access, or runtime
change occurred.

All 64 workers were reaped. Agent exits were 32/32 `GRACEFUL`; guard exits
were 31/32 `GRACEFUL` and one `TERMINATE/-15`. The single anomaly was the
first task, `ATK_CAND_LINKMAIL_PARAPHRASE__A2`. Its guard made **zero host
classification calls** after one cold-start attempt. The pair recorded STOP
received, serve loop returned approximately 0.046 s after STOP, target and
finalizer/thread milestones returned without recorded errors, and zero
non-daemon threads at return. Nevertheless the owner observed no process exit
within the configured 2.0 s graceful window and reaped it via `TERMINATE`
after 2.327 s. Median guard shutdown elapsed across all 32 tasks was 1.363 s.

These observations place the delay **after the recorded Python serve/finalizer
milestones and before OS process exit**, but do not establish whether CUDA,
PyTorch, Python interpreter shutdown, IPC, scheduler delay or another
component caused it. The successful task and reaped worker do not turn
`TERMINATE` into graceful cleanup. The frozen v2 run remains 31/32 all-workers
graceful, so lifecycle acceptance and Phase 5 freeze remain open. A future
prospective instrumented startup/exit control may investigate cause; it must
use a new run identity and must not replay Dev32 to select a better result.
