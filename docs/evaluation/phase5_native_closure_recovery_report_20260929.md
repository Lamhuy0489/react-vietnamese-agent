# Phase 5 native closure deployment and recovery — 2026-09-29

## Decision

The closure deployment remains **NO-GO**. The first epoch produced 21 valid
completed conditions (C1–C3 across A0–A6). It stopped at C4/A0 after a request
became delivery-uncertain. A fresh recovery epoch was deployed against the
same identity-verified release, but the same C4/A0 slot again ended with an
uncertain third agent request. The runner stopped without scheduling any
semantic retry. Phase 5 is not accepted.

## Deployment evidence

- Package: `build/kaggle/structured_pair_release04a_20260929`.
- Read-only status immediately before recovery: agent and guard both
  `KernelWorkerStatus.RUNNING`.
- Authenticated discovery immediately before recovery: agent `READY
  qwen3-8b`; guard `READY llama-3.2-3b-instruct`.
- First epoch output: `build/evaluation/phase5_native_closure01`.
- First epoch journal: `build/evaluation/structured_api_sessions_phase5_closure01_20260929`.
- Recovery output: `build/evaluation/phase5_native_closure_recovery01`.
- Recovery journal: `build/evaluation/structured_api_sessions_phase5_closure_recovery01_20260929`.
- Combined evaluator:
  `build/evaluation/phase5_native_closure_combined01_20260929.json`.
- Deployment receipt:
  `experiments/manifests/phase5_native_closure_recovery01.json`.

The two epochs use the same frozen task fixtures, source catalog, generation
settings, runtime configuration, and public worker identities. Recovery changes
only the journal/output boundary and schedules C4–C12 (63 conditions), as
declared in the [protocol](phase5_native_closure_protocol_v1.md).

## What was preserved

The original C4/A0 `model_error` record and its one uncertain journal request
were not deleted, edited, or retried. The recovery C4/A0 record is separately
stored and also remains excluded from the completed denominator. The combined
evaluator therefore reports 21/84 completed conditions, 63 missing, and zero
Test/private-ground-truth reads. This is an infrastructure limitation, not a
policy result and not evidence for relaxing a security gate.

The saved evaluator now counts `broker_result` security events for executed
Broker calls and reads guard risk from the versioned `outcome.result` field.
Both changes are read-only scoring corrections; they do not alter raw traces.

## Next admissible step

Do not launch a third semantic retry or change the package, model, prompt,
threshold, or journal to force completion. A future attempt requires a new
infrastructure recovery decision with a demonstrably resolved request-delivery
path, a fresh declared journal, and a source/input identity review. Until then,
the formal freeze remains `decision=NO_GO` and `phase5_accepted=false`.
