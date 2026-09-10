# IPC v1 evidence clarification — 2026-09-10

This addendum preserves the uncommitted report supplied during the handoff and
corrects its overbroad interpretation without editing its bytes. It is the
current bounded interpretation; raw inference artifacts and selected audit
remain unchanged.

Fresh read-only audits03/04 reproduced the selected audit byte-for-byte:99raw
files,6reaped workers,18recovery samples with signed residual0bytes on bothT4s.
All six exits were forced:5TERMINATE/-15,1KILL/-9, **zero graceful exits**.
The three idle siblings did issue UNREGISTER for their tqdm locks, but that is
not equivalent to a clean process exit. Worker lifecycle records are authoritative.

The3unmatched registrations in this instrumented run each have a creation stack
through tqdm.std.create_mp_lock and multiprocessing.context.RLock during HF
loading; the other3worker locks and90owner transport registrations have paired
UNREGISTER calls. The shutdown warning count3matches the unmatched count.
This supports attribution of the observed entries, not observation of the
tracker's final OS unlink or an exhaustive proof of no driver/IPC leaks.
No claim of "no CUDA driver leak" follows from endpoint VRAM measurements.
It also cannot retroactively attach stacks to the earlier uninstrumented run.

TQDM_DISABLE=1 is not a verified repair: pinned4.67.3 creates the default lock in
__new__ before display options are handled. A separate
[thread-only worker lock](../architecture/phase5_worker_progress_v1_contract.md)
is implemented for CPU validation, not yet wired into GPU/runtime. No manual
resource unregister/unlink or warning suppression is used.

No guard prompt tuning from the four-call diagnostic, no Phase6/7 or held-out
Test transition. The active Phase5 gates include context stress, versioned runtime
integration, A4 processing-scope anchors, private-record final entitlements and
grouped Dev validation/model decision/freeze. Test pass count is not phase progress.
