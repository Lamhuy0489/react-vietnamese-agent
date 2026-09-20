# Post-serve teardown CPU probe v1

2026-09-17. Separate lifecycle diagnostic after constrained GPU v1, not a retry
of its semantic outcomes. Frozen ShutdownBackend v2, its transport, native
factories, model/prompt/policy and the 2s graceful budget remain unchanged.

## Fixed experiment

Six synthetic factories, three repetitions in fixed order (18 fresh spawned
workers). Each worker returns two identical public responses before close:

| Case | Injected CPU-only teardown | Expected exit evidence |
|---|---|---|
| fast | finalizer without delay | serve returned, finalizer completed, GRACEFUL |
| bounded | finalizer delay 0.25s | serve returned, finalizer completed, GRACEFUL |
| finalizer_block | finalizer delay 5s | serve returned, finalizer entered only, TERMINATE |
| finalizer_ignore_term | same delay, ignore SIGTERM | serve returned, finalizer entered only, KILL |
| destructor_block | destructor delay 5s | STOP observed, serve not returned, TERMINATE |
| thread_block | non-daemon background thread delay 5s | serve/finalizer completed, thread unfinished, TERMINATE |

Register process-exit finalizers with `multiprocessing.util.Finalize(None, ...)`
and an explicit priority; no backend close method or production exit shortcut.
The synthetic non-daemon thread is started and acknowledged before the first
response. Never call `os._exit(0)` to manufacture success. Terminate/kill budgets
are 0.2s/1s for the CPU controls; these do not change native cancellation budgets.

Record worker PID, two transport attempts, config identity, unchanged response
hashes, destructor/finalizer/thread timestamps, STOP/serve timestamps and actual
exit/reap events. These are observable timings, not model reasoning. Preserve all
attempts; noisy or failed expected conditions invalidate a control, not authorize
automatic retries. Run outputs must be fresh and read-only audit outputs separate.

## Provenance and acceptance

Bind the fixed plan, exact working-tree source hashes, labeled Git base, Python
implementation/version and spawn method. Source/Git base before the final grouped
commit is not a native release commit. Include a strict read-only auditor for
complete schedule, unique case IDs/attempt sequences, per-worker PID binding,
event ordering, case/config identity,
expected control outcomes, raw hashes and synthetic-only flags. Audit twice.

CPU controls can show that different shutdown mechanisms reproduce similar
STOP/serve-return observations. They cannot identify the actual GPU teardown
cause, prove CUDA cleanup or choose a larger production deadline. Next native
step requires separate opt-in milestone instrumentation and a frozen diagnostic
protocol/package; no resubmission of constrained GPU v1. No Test/private GT,
model weights, GPU, external network or mock-tool changes in this CPU study.
