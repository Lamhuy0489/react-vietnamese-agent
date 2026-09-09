# Paired worker IPC-origin diagnostic v1

## Scope and prior evidence

Continue Phase5 only. The completed pair cancellation GPU v1 remains immutable:
six workers reaped,18VRAM samples returned to baseline, but kernel shutdown warned
about3semaphores. No creation-site trace was present; neither its cause nor
persistent OS leakage can be inferred from that count. Do not rerun for better
model outputs, change grace periods or mark this as a quality evaluation.

One separate instrumented GPU identity: private/offline twoT4 kernel
`huylmhuhu/react-vn-pair-ipc-v1`, title `ReAct VN Pair IPC v1`, timeout5400s.
Same private Dataset11942593/version1, Qwen7B Kaggle model version1, pinned guard
snapshot, source archives/wheels, exact Docker digest as
[cancellation contract](phase5_pair_cancel_gpu_v1_contract.md).
No new Dataset or local model downloads. This is a causal diagnostic candidate,
not a replacement for old cancellation evidence or a semantic retry.

## Instrumentation, not a cleanup fix

Add only `ipc_trace_v1.py` and `run_phase5_pair_ipc_worker.py` to the prior13file
overlay. Frozen ModelPair/WarmGuard, factories, generation settings, three busy
cases, deadlines180/120, terminate0.5/kill1s and all model-memory caps unchanged.
Use the same zero-generation CUDA busy workload with resident model weights.

In owner before native imports and before Event creation, and in each worker
before calling its lazy model factory, wrap Python resource_tracker register/
unregister entry points. Each successful call forwards exactly once and appends
a fsynced per-process JSONL event. Record PID, role, sequential event number,
resource type, SHA256 of resource name, and at most24stack frame metadata records
(module, basename, function, line number). Never source lines, frame locals,
environment variables, prompt/model text, secret values or hidden reasoning.
Record Python version/tracker source hash at install, selected imported dependency
source hashes/versions at factory readiness. Worker imports before factory entry
are outside the child trace boundary and must remain a stated limitation.

Instrumentation stays active during normal multiprocessing finalizers. After
the completed suite has dropped its pairs, run one owner gc.collect checkpoint;
record its count but do not interpret it as deterministic across executions.
This added checkpoint is explicitly different from the historical run. It does
not release live child resources or fix graceful exit. Do not manually invoke
unregister, sem_unlink, finalizer callbacks, change library locks, suppress
resource warnings or alter the tracker cache. Hook logging errors invalidate
the diagnostic; preserve partials rather than silently continue as uninstrumented.

## Acceptance and interpretation

CPU: exact byte-bound archive/expanded/PAX wrapper rehearsals must import from
isolated installed source, exercise8tools/21Dummy/completed and missing-only
resume, execute all3stub trials, then check90parent REGISTER/90UNREGISTER and
no unmatched parent entries. Six stub factory traces have no registrations.
A deliberately SIGTERM-killed standalone synthetic child-owned semaphore is a
positive control: one unmatched registration and tracker warning. Its dedicated
tracker retains responsibility for cleanup; no manual cleanup bypass.

Before submit: full setup/Ruff/mypy/pytest/knowledge QA, source and exactpreflight
receipt pushed to GitHub, current quota/private Dataset version rechecked.
One submission only; no automatic retry. Read-only audits run after process exit,
when finalizer events are complete. Download logs even if kernelERROR. Freeze
all raw hashes, verify source/metadata, unchanged cancellation resource gates,
Dummy checkpoints and owner/worker trace PIDs against lifecycle records.

Do not require zero unmatched registrations as a diagnostic success criterion:
the purpose is to identify them. Require trace identities, ordered sequences,
paired per-process register/unregister accounting, and actual worker reap evidence.
Report observed unmatched registrations by role and call site, together with
shutdown warning counts. If they cannot be reconciled, report an unresolved gap.
Matching counts alone are not a proof that all resources were observed.
The ledger cannot observe cached pre-instrumentation aliases, C-level entry
points, resource tracker internals or final OS unlink outcome. Even an empty
ledger is not an IPC-clean certificate. A later lifecycle fix requires a separate
version/protocol and validation. Fsync instrumentation perturbs latency: never
pool this run with the earlier uninstrumented timing benchmark.

## Primary-source basis

- Python Software Foundation, Python3.12 multiprocessing docs (accessed
  2026-09-09): the POSIX spawn resource tracker cleans remaining named resources
  after the process family exits; signal-killed processes may leave tracked
  resources. [Documentation](https://docs.python.org/3.12/library/multiprocessing.html#contexts-and-start-methods).
- CPython3.12.0 source: SemLock registers named resources and arranges finalizer
  unlink/unregister; tracker warns before attempting remaining cleanup.
  [synchronize.py](https://github.com/python/cpython/blob/v3.12.0/Lib/multiprocessing/synchronize.py),
  [resource_tracker.py](https://github.com/python/cpython/blob/v3.12.0/Lib/multiprocessing/resource_tracker.py).
  These are mechanism references, not a claim about the Kaggle patch version.
- tqdm4.67.1 source creates a multiprocessing RLock in its default write lock.
  [std.py](https://github.com/tqdm/tqdm/blob/v4.67.1/tqdm/std.py).
  This is one candidate source, not attribution of the three historical warnings;
  installed Kaggle version and actual stacks must be measured.

No Test payload/private GT access; frozen seals only. No Phase5 acceptance or
guard/backbone selection. Next gates remain context-stress, runtime integration,
grouped Dev decision and remaining A4/final policy scope.
