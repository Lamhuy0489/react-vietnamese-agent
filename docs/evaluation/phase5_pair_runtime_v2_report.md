# Phase 5 — pair outcome and failed-startup evidence v2

2026-09-13. Focused integration and full repository CPU QA passed.
This is synthetic CPU fault evidence, not native model performance or guard quality.

## Measured focused scope

- 64 tests passed in 70.69s; 63 task receipts joined with runtime and worker
  evidence. Fresh-output rejection produces no new receipt.
- Seven exact v7 observable/context parity cases; 28 level/terminal combinations;
  preserved final entitlement, scope and external guard veto regressions.
- Real process termination after a worker response: both requesting roles and
  both victims, four combinations. The old auditor rejects these consistent
  traces; v2 preserves worker OK, pair ERROR and rejected host response.
- Nine worker-OK/host-ERROR observations include those four combinations and
  five additional mutation controls reusing one fault setup. They are not nine
  independent failure mechanisms or successful agent responses.
- Five incomplete startups, including agent-only load failure and interruption
  during guard startup, retain nonzero elapsed intervals (0.526–1.112s in this
  synthetic CPU run). These intervals include process/initialization overhead
  and possibly pair-internal cleanup, not native model weight-load latency.
- Cleanup: 90 GRACEFUL, 13 TERMINATE and nine EXITED records; no pending handles.
  EXITED includes processes deliberately terminated by the test. Active child
  PIDs are checked in addition to receipt flags.
- Corruption controls reject changed event status/ranges, missing startup time,
  inconsistent completion, NaN totals and earlier schema/request/count mutations.

## Reproducibility and remaining work

Raw root: `results/phase5_pair_runtime_v2_cpu01`. Validator:
`scripts/verify_phase5_pair_runtime_v2.py`. Prior CPU02 v1 source/raw audit passed
971 entries unchanged before execution and again after completion.

Full QA: **2,560 passed, one skipped in 551.55s**. The skip is the local missing
native tqdm dependency, not a failed assertion. Setup, Ruff, mypy (320 source
files) and knowledge checks all passed. Independent audit matched 445 source
and 641 raw hashes; all 169 tracked data hashes stayed unchanged. All 63 task
receipts passed the joined auditor again after the suite completed.

[Selected bounded CPU receipt](../../experiments/manifests/phase5_pair_runtime_v2_cpu01.json)
SHA-256: `0832ae8c29f925f8bc522ac3138fa6d41132d3dae53ac68d44ffd7bd58a453b9`.
This is working-tree CPU QA anchored to parent `817da23`; actual source bytes
are bound by the source inventory. It is not a clean-source native release.

Policy, prompts, models, decoding, tools and the v7 security loop are unchanged;
only host outcome evidence and initialization timing are versioned. Original
v1 source and raw receipts are preserved. No held-out payloads are parsed.
Exact native package, equivalent agent-only policy/attention, GPU lifecycle,
guard quality/grouped Dev, broader semantic coverage and Phase 5 freeze remain.

[Contract](../architecture/phase5_pair_runtime_v2_contract.md) ·
[Knowledge](../../knowledge/phase5_pair_runtime_v2.md).
