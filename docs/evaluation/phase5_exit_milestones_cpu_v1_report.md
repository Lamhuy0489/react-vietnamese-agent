# Phase 5 — opt-in exit milestones, CPU acceptance

2026-09-20. [Protocol](../architecture/phase5_exit_milestones_v1_contract.md).
Scope: observer component and fixed synthetic controls, not a native GPU repair.

## Implementation

`MilestoneBackend` inherits the existing `ShutdownBackend.generate` and cleanup
methods unchanged. A private context adapter changes only the spawned target to
an opt-in observer wrapper. The child delegates and restores the actual CPython
multiprocessing exit function and thread-shutdown function. Host hooks, model
factory ownership, request/response transport and the 2s graceful budget remain
unchanged. Instrumented configuration has a distinct lifecycle/hash identity.

Nine fixed slots hold entry/return/error timestamps, worker PID and count of
Python-visible non-daemon threads excluding main. Timestamp is published last;
host snapshots require a reaped worker. No thread names, stacks, arbitrary error
messages, model payloads or additional model references are recorded.

The bootstrap shape and three interpreter function hashes are bound to receipts.
This modifies child-local hooks and has observation overhead; it is not claimed
to be transparent on every interpreter or native library. Exact native package
rehearsal remains required before GPU use.

## Fixed controls

18 fresh workers: six unchanged synthetic factories × three repetitions, two
public responses each. [Selected closure](../../experiments/manifests/phase5_exit_milestones_cpu_close01.json).

| Injected condition | Observed unfinished boundary | Exit (3/3) | Mean close, s |
|---|---|---|---:|
| Fast finalizer | None, all stages returned | GRACEFUL | 0.0383 |
| Bounded 0.25s finalizer | None, all stages returned | GRACEFUL | 0.2921 |
| Blocked finalizer | Multiprocessing exit function | TERMINATE | 2.0058 |
| Blocked finalizer, ignored SIGTERM | Multiprocessing exit function | KILL | 2.2056 |
| Blocked destructor | Target has not returned | TERMINATE | 2.0055 |
| Live non-daemon thread | Thread-shutdown function | TERMINATE | 2.0048 |

All 18 reaped. The 6 GRACEFUL/9 TERMINATE/3 KILL pattern, public responses and
normalized attempt fields match the frozen uninstrumented controls. Config/PID
identities intentionally differ. Sequential CPU timings are descriptive, not a
randomized overhead measurement or a production deadline recommendation.

Controls01 is retained but excluded: the first auditor read identity before
rejecting symlink descendants. Inventory now runs before any JSON read, covered
by regression. Controls02 binds the corrected source; no semantic model retry.
The initial test-collection name collision was also corrected before acceptance.

## Evidence and limits

Raw: `results/phase5_exit_milestones_cpu_controls02` (19 files). Read-only audits
`results/phase5_exit_milestones_cpu_audit01.json` and `..._audit02.json` are
byte-identical. Per-case PID, config, generation/request hash, STOP/serve ordering,
partial milestones, outcome, schedule and raw/source inventory are checked.
[QA receipt](../../experiments/manifests/phase5_exit_milestones_cpu_qa01.json)
records the scoped regression commands, log hashes and frozen-source checks.
Final QA passes 666 focused tests (44.72s) and 149 integration tests (138.93s),
setup/Ruff/mypy454/knowledge/diff. This adds 53 observer/control regression tests.
The earlier 172/142/86/175 source-pin sets and prior teardown sources remain
unchanged. Full repository pytest is excluded because of sealed Test-authoring
fixtures. Git base `3cb2b54` plus exact working-tree hashes identify this CPU
study; the base alone does not contain the new observer or claim a native release.

Native cause is still unknown. Multiprocessing-exit return does not imply every
callback succeeded; Python thread counts omit native/CUDA threads. Completed
observer stages do not establish process exit or VRAM recovery. Never use missing
markers as success or describe a forced exit as graceful. No GPU, native weights,
network, held-out Test or private ground truth in this work.

## Next concrete gate

Wire the opt-in backend into a separately identified native diagnostic runner,
without replacing constrained GPU v1. Join milestones to the existing native
worker PID/role/task receipts, including partial/error paths. Rehearse exact
archive and expanded layouts plus interpreter hashes with synthetic workers;
only then freeze source and submit a bounded private Kaggle diagnostic. Do not
increase grace2s. Guard semantic quality, benign utility and Phase 5 formal freeze
remain independent open work; acceptance stays 4/7 (approximately 57%).
