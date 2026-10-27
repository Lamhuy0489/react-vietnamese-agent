# Phase 5 native closure protocol v1 — C1–C12

> Historical protocol: both v1 epochs stopped with unresolved delivery. The
> current script's revised fixture definitions are CPU-only; its native CLI is
> retired and must not strip manifest pins. A new native protocol/run identity
> must precede further requests. [Root-fix report](phase5_root_fix_20260929.md).

This is a new Dev-only closure run. It uses the cumulative Phase 5 runtime,
one fixed Qwen task agent, one fixed Llama guard, the same synthetic tools and
the same decoding across A0–A6. Only `SecurityConfig` and the required guard
activation vary by level. The run uses package
`build/kaggle/structured_pair_release04a_20260929` and a fresh journal; it does
not resume or rewrite any earlier run.

The schedule has twelve synthetic controls (C1–C12) crossed with A0–A6. The
task instruction, source catalog, model identity, generation settings, and
tool environment are frozen before the first request. Evaluator labels are
host-only and are never loaded into the runtime, prompt, policy, or worker.
No Test payload, private ground truth, semantic retry, real network sink, or
hidden chain-of-thought is permitted.

The closure target is operational evidence for DoD 1–20, not a Phase 6/7
statistical benchmark. A failed/denied result remains in the denominator. The
run stops on an unresolved journal record or a started-only condition.

## Recovery epoch boundary

The first deployment is recorded at
`build/evaluation/phase5_native_closure01` with journal
`structured_api_sessions_phase5_closure01_20260929`. It completed C1–C3 across
all seven levels, then stopped at C4/A0 after one API request became
delivery-uncertain following an observable mock-tool execution. That record is
historical evidence and must not be deleted, rewritten, or semantically
retried.

If access is restored, the recovery deployment uses the same frozen package,
worker identities, task fixtures, generation settings, and runtime source, but
the fresh journal
`structured_api_sessions_phase5_closure_recovery01_20260929` and output
`build/evaluation/phase5_native_closure_recovery01`. It schedules only C4–C12
(63 conditions), beginning with the blocked C4/A0 slot. This is an
infrastructure recovery epoch, not a second semantic sample: the combined
evaluator retains the C1–C3 records from epoch one, excludes epoch one's
uncertain C4/A0 from the completed denominator, and accepts the recovery record
for each missing condition only when its request journal is fully resolved and
its artifact hashes verify. If recovery encounters another uncertain request,
it stops fail-closed and reports both epochs separately.
