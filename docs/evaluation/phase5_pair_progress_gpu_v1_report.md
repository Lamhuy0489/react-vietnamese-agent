# Worker-local progress prevention GPU diagnostic results

| Trial | Agent ready s | Guard ready s | Busy timeout s | Busy cleanup | Resident GiB 0 / 1 |
| --- | ---: | ---: | ---: | --- | --- |
| agent_busy | 218.045 | 30.567 | 180.374 | TERMINATE/-15 | 9.799 / 7.621 |
| guard_busy | 136.324 | 30.323 | 120.324 | TERMINATE/-15 | 9.799 / 7.621 |
| guard_ignore_term | 139.425 | 31.045 | 120.818 | KILL/-9 | 9.799 / 7.621 |
Prevention gate pass: True

Six workers reaped; eighteen recovery samples across two GPUs.
Idle-worker graceful flags and signed residuals remain in audit.json.

CUDA busy loops with weights resident, not native generation cancellation, maximum context, quality, continuous peak memory, owner SIGKILL or driver-crash safety

No model generation or Phase5 acceptance.

## Tracker observations

| Process trace | Register | Unregister | Unmatched |
| --- | ---: | ---: | ---: |
| agent_busy_agent.jsonl | 0 | 0 | 0 |
| agent_busy_guard.jsonl | 0 | 0 | 0 |
| guard_busy_agent.jsonl | 0 | 0 | 0 |
| guard_busy_guard.jsonl | 0 | 0 | 0 |
| guard_ignore_term_agent.jsonl | 0 | 0 | 0 |
| guard_ignore_term_guard.jsonl | 0 | 0 | 0 |
| owner.jsonl | 90 | 90 | 0 |

Warning count matches observed unmatched: True
Matching counts do not establish complete instrumentation or OS unlink success.
Instrumented timings cannot be pooled with earlier uninstrumented measurements.

Shutdown semaphore warning counts: []
IPC cleanup is not verified; this resource warning is not a VRAM measurement.

## Selected evidence and bounded conclusion

Kernel `huylmhuhu/react-vn-pair-progress-v1`, version 1 COMPLETE, one submission.
Runtime source `a1a90b31c312b09c62c03af1b7f3bcc66166b0ee`; source/preflight/QA
pushed in `f8ab56dc76f3ef172a25517ed59ce9eae70f75fc` before submission.
[Exact preflight](../../experiments/manifests/phase5_pair_progress_gpu_v1_preflight01.json),
[pre-submit QA](../../experiments/manifests/phase5_pair_progress_gpu_v1_pre_submit_qa01.json),
[selected audit](../../experiments/manifests/phase5_pair_progress_gpu_v1_audit01.json).
Private/offline two-T4, pinned image and model mounts, remote wrapper hash verified.
106 raw files unchanged; independent audits01/02 and generated reports byte-identical.
Six native policy receipts bind worker PID and tqdm4.67.3/std.py identity before
HF loading. Owner identity also binds each lifecycle snapshot. Dummy21/84events
checks transport/checkpoints only, not model task success.

All six workers loaded pinned real models; zero model generation calls. Five
TERMINATE/-15 and one KILL/-9 exits: **zero graceful exits**, including idle
siblings. All eighteen recovery samples show signed residual0bytes on both GPUs.
Six child ledgers have zero registrations; owner90/90; zero unmatched entries
and no shutdown semaphore warning in the retained completed log. This satisfies
the predeclared creation-path prevention gate, not an exhaustive IPC/OS cleanup
certificate. No manual unregister/unlink, warning suppression or retry.

Historical IPC v1 observed three unmatched busy-worker tqdm locks and warned3;
its raw evidence is unchanged. Do not pool readiness timings across runs or
claim a causal speedup from differing cold-load/cache conditions. This diagnostic
does not measure native generation cancellation, maximum context, model quality,
continuous global peak, owner SIGKILL or driver crash safety.

Phase5 remains open: maximum-context native runner/GPU validation, runtime
integration, A4 processing scope, general final entitlements and grouped Dev
model/guard decision plus freeze. No local model load or held-out Test payload.

