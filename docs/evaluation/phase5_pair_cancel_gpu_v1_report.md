# Pair cancellation GPU technical results

| Trial | Agent ready s | Guard ready s | Busy timeout s | Busy cleanup | Resident GiB 0 / 1 |
| --- | ---: | ---: | ---: | --- | --- |
| agent_busy | 258.432 | 30.655 | 180.383 | TERMINATE/-15 | 9.799 / 7.621 |
| guard_busy | 148.124 | 31.868 | 120.337 | TERMINATE/-15 | 9.799 / 7.621 |
| guard_ignore_term | 147.689 | 32.741 | 120.823 | KILL/-9 | 9.799 / 7.621 |

Six workers reaped; eighteen recovery samples across two GPUs.
Idle-worker graceful flags and signed residuals remain in audit.json.

CUDA busy loops with weights resident, not native generation cancellation, maximum context, quality, continuous peak memory, owner SIGKILL or driver-crash safety

No model generation or Phase5 acceptance.

Shutdown semaphore warning counts: [3]
IPC cleanup is not verified; this resource warning is not a VRAM measurement.

## Bound execution and review

2026-09-09: private offline two-T4 kernel `huylmhuhu/react-vn-pair-cancel-v1`,
version1 COMPLETE after one submission. Runtime overlay sourcee01b4e7;
source/preflight pushed to mainf6474a7 before submission. [Predeclared contract](../architecture/phase5_pair_cancel_gpu_v1_contract.md),
[exact preflight](../../experiments/manifests/phase5_pair_cancel_gpu_v1_preflight01.json),
[selected audit](../../experiments/manifests/phase5_pair_cancel_gpu_v1_audit01.json).

Exact requested Docker digest matched returned remote metadata. torch2.10.0+cu128,
CUDA12.8, Transformers5.5.0; private guard Dataset11942593/version1; pinned
Qwen2.5-7B-Instruct Kaggle model1 and Qwen2.5-1.5B-Instruct snapshot unchanged.
Agent339FP16tensor/live-hash admission and original README mismatch preserved;
fixed20/8layer placement, agent12/7GiB allocator caps, guard5GiB/device1.

All three trials loaded fresh sibling workers, agent then guard. Timings above
include process startup, live model hashing and loading; subsequent trial load
speed is not an independent cold-cache benchmark. All six HF metrics files
contain exactly one load record, no generation records. Busy diagnostic performs
small CUDA matrix operations while retaining model weights; host command never
becomes a model prompt. No Test, private GT, quality score or semantic retry.

All six workers required forced termination: five TERMINATE/-15, one KILL/-9.
No idle sibling exited gracefully. All18post-cleanup samples measured signed
residual0bytes on both devices relative to each trial's stable observer baseline.
This meets the fixed last-three ±256MiB gate; it is not proof of unlimited
stress resilience or zero leaks across every resource type.

The kernel log reports3leaked semaphore objects at interpreter shutdown. It
does not identify their creation site or prove persistent leakage after tracker
cleanup. Keep this warning unchanged; IPC cleanup is unverified. Do not remove
tracker registrations manually or loosen termination graces to hide it. A
separate bounded diagnostic is needed before claiming completely clean shutdown.

91raw files retained in `results/phase5_pair_cancel_gpu_v1_raw01`; remote source
and metadata in `build/kaggle/pair_cancel_gpu_v1_remote_source01`. Whole-tree hashes,
13overlay source hashes, model/request/generation/deadline identities, markerPID/
CUDA device map, six lifecycle reaps and18recovery samples verified.21Dummy
terminal checkpoints/84events verified; both independent audit invocations
produced byte-identical JSON and generated table. This is automated validation
and assistant self-review, not independent human review.

Reproduce without inference, keeping output fresh:

```sh
.venv/bin/python scripts/audit_phase5_pair_cancel_gpu.py \
  --raw results/phase5_pair_cancel_gpu_v1_raw01 \
  --remote-source build/kaggle/pair_cancel_gpu_v1_remote_source01 \
  --output results/phase5_pair_cancel_gpu_v1_audit03
```

Next: investigate shutdown semaphore origin, predeclare maximum-context/forced-
length stress, then versioned pair runtime integration and grouped Dev guard
decision/remaining A4/final scope. Phase5 remains open. No new account required.
