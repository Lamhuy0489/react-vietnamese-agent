# Worker-local progress lock v1 — CPU implementation, not a GPU fix claim

The pair IPC v1 trace identified three unmatched registrations created by the
default tqdm multiprocessing RLock in force-killed busy workers. Their idle
siblings did unregister their locks but still exited via TERMINATE/-15; zero
graceful exits. Preserve99raw files, all warnings and their bounded interpretation.

## Minimal prevention, separate from frozen code

New opt-in `ThreadProgressFactory` configures tqdm before invoking the untouched
HF factory. Only a daemon spawn child with an owning parent is accepted. It must
not fork or spawn descendants; each model worker already writes to its own
captured/suppressed output. Its threads still synchronize through threading.RLock.
Use tqdm's public set_lock API; do not replace transport Event locks or manually
unregister/unlink resources. Refuse repeated/late initialization, existing locks,
active bars, native torch/Transformers already imported, or dependency drift.

Bind tqdm4.67.3 and std.py SHA256
`4a4db84b039de7d86935b6f450bf18dfff2e79198bdffe4eef6572d9729ab231`, measured in
the completed GPU trace and matched against the local native package.
Do not silently fall back to default multiprocess locks. No model, decoding,
prompt, policy, deadline, placement/cap or frozen worker change. Installation
only prevents this named creation path; it does not make forced termination
graceful or prove every IPC/CUDA resource clean.

`TQDM_DISABLE=1` alone is not this fix: tqdm4.67.3's __new__ calls get_lock before
__init__ applies display options. A new native CPU control confirms one registered
semaphore even with disable set before import. [Primary source](https://github.com/tqdm/tqdm/blob/v4.67.3/tqdm/std.py).

## Acceptance

Unit tests cover worker ownership/start method, early-init boundary, version/hash,
existing lock refusal, thread reentrancy and lazy/fail-closed factory ordering.
Optional native pytest control is explicitly skipped if pinned tqdm is absent;
do not count that skip as execution. Selected standalone native controls must run
with the verified installed package and report actual Python/source identities.

Four independent synthetic spawn children: default+SIGTERM, disabled+SIGTERM,
thread-lock+SIGTERM, thread-lock+SIGKILL. Parent waits for ready acknowledgment,
reaps every process, records exitcode and trace PID. Expected registrations are
1/1/0/0; two positive controls leave unmatched entries and the dedicated owner's
normal resource tracker emits the warning before attempting cleanup. Never
manually unregister/unlink the positive controls. No model or GPU operation.

Preserve raw logs/traces and per-file hashes, run twice without replacing prior
outputs, compare invariant outcomes (not PID/timing bytes). Full project QA and
knowledge-check before handoff. Prior GPU source and raw hashes stay unchanged.

## Next gate

This implementation is NOT installed in an existing kernel or runtime. Before
GPU validation, add a new versioned wrapper/entry point, thread-policy identity
receipt and trace coverage, exact archive/expanded/PAX8tools/21Dummy/resume
preflight, source/receipt push and current private mount/quota checks. Keep the
historical uninstrumented/instrumented results unchanged. No claim of native HF
or GPU verification until that separate run is complete and audited.

Context stress, runtime integration, A4 scope, final entitlements and grouped Dev
decision remain separate Phase5 gates. No Test/private GT, new model choice or
Phase6/7 transition authorized by this component.
