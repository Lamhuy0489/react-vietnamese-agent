# Guard cancellation / VRAM recovery probe v1

Technical Phase 5 preflight only. Preserve the first guard GPU responses and its
failed graceful-cleanup audit. No classification prompt, response generation,
benchmark task, guard quality tuning or agent model is involved in this probe.
Use the pinned Qwen1.5B snapshot and frozen GuardHFBackend/WarmGuardBackend.

Three fresh sequential workers, fixed order:

1. `resident_close`: load the real HF backend, acknowledge residency through
   the existing transport without invoking model.generate, then close normally.
2. `busy_timeout`: load/acknowledge, then deliberately loop small CUDA matrix
   operations with the model retained until the existing 120-second request
   deadline cancels the process.
3. `ignore_term_timeout`: same deliberate CUDA load, but the child installs
   SIGTERM-ignore before the busy loop; exercise terminate-to-kill escalation.

Keep production deadline/graces 120s/0.5s/1s unchanged. Synthetic CPU tests may
use a separately recorded shorter deadline; they cannot certify CUDA behavior.
Never restart a failed trial. Each worker records busy-loop entry before waiting
for cancellation. All requests are fixed transport commands, not model prompts.
Require first ACK success, a live resident process, then expected timeout status
and reaping. For ignore-term case require KILL/-9. Normal close may be graceful
or terminated: record separately, do not relabel forced cleanup as graceful.

A persistent parent CUDA observer initializes device1 with an actual tensor op,
then releases its tensor/cache. Its CUDA context remains stable for the entire
probe, unlike the earlier parent-without-CUDA run. Record that observer baseline
and every trial's before/resident/post-close global free/total memory. Only device1
is used, on an allocation of two T4. Model remains single-device FP16/5GiB cap.
Require at least 2GiB less free memory while resident to avoid empty-worker proof.

Recovery uses six fixed post-close samples one second apart, no early stopping.
The last three must be within 256MiB of the trial baseline, and each new baseline
within 256MiB of the initial observer baseline. This is a declared engineering
tolerance, not exact zero leak or a global peak metric. Report signed residuals.
No further trial after unreaped worker, failed recovery or other failed gate;
persist the failure and mark remaining trials skipped. No retries for success.

Receipt binds source/config/snapshot, observer, all attempts/lifecycle and memory
samples. Distinguish CPU stub transport validity, real GPU resource recovery,
normal graceful closure and guard quality. Successful cancellation does not fix
the historical SAFE-on-B diagnostic miss or establish agent+guard coexistence.

Packaging must reuse the immutable private Dataset v1 and inject only new named
source files as a separately hash-bound kernel overlay, refusing overwrite of
the frozen source. Recheck source inventories before and after overlay, both
archive/actual-expanded mounts, eight tools/fault, 21Dummy/missing-only resume
and the complete CPU cancellation protocol offline. Commit/push source and
preflight before the private GPU run. No Test/GT/credentials/project memory.
