# Instrumented pair IPC diagnostic technical results

> Interpretation update2026-09-10: see the [evidence clarification](phase5_pair_ipc_gpu_v1_review_addendum.md).
> All six exits were forced, including idle siblings. VRAM endpoints do not
> certify absence of driver/IPC leaks. The draft interpretation below is retained
> for provenance, not adopted where it conflicts with that clarification.

| Trial | Agent ready s | Guard ready s | Busy timeout s | Busy cleanup | Resident GiB 0 / 1 |
| --- | ---: | ---: | ---: | --- | --- |
| agent_busy | 260.435 | 35.937 | 180.380 | TERMINATE/-15 | 9.799 / 7.621 |
| guard_busy | 136.849 | 30.322 | 120.327 | TERMINATE/-15 | 9.799 / 7.621 |
| guard_ignore_term | 148.611 | 33.780 | 120.836 | KILL/-9 | 9.799 / 7.621 |

Six workers reaped; eighteen recovery samples across two GPUs.
Idle-worker graceful flags and signed residuals remain in audit.json.

CUDA busy loops with weights resident, not native generation cancellation, maximum context, quality, continuous peak memory, owner SIGKILL or driver-crash safety

No model generation or Phase5 acceptance.

## Tracker observations

| Process trace | Register | Unregister | Unmatched |
| --- | ---: | ---: | ---: |
| agent_busy_agent.jsonl | 1 | 0 | 1 |
| agent_busy_guard.jsonl | 1 | 1 | 0 |
| guard_busy_agent.jsonl | 1 | 1 | 0 |
| guard_busy_guard.jsonl | 1 | 0 | 1 |
| guard_ignore_term_agent.jsonl | 1 | 1 | 0 |
| guard_ignore_term_guard.jsonl | 1 | 0 | 1 |
| owner.jsonl | 90 | 90 | 0 |

Warning count matches observed unmatched: True
Shutdown semaphore warning counts: [3]
IPC cleanup is not verified; this resource warning is not a VRAM measurement.

## Bound execution and findings

2026-09-09: private offline two-T4 kernel `huylmhuhu/react-vn-pair-ipc-v1`,
version 1 COMPLETE after one submission. Runtime source 9087791;
source and preflight pushed to main 31910cb before submission.
Predeclared contract: `docs/architecture/phase5_pair_ipc_v1_contract.md`,
preflight receipt: `experiments/manifests/phase5_pair_ipc_gpu_v1_preflight01.json`,
selected audit: `experiments/manifests/phase5_pair_ipc_gpu_v1_audit01.json`.

Exact requested Docker digest matched returned remote metadata. torch 2.10.0+cu128,
CUDA 12.8, Transformers 5.5.0; private guard Dataset 11942593/version 1; pinned
Qwen2.5-7B-Instruct Kaggle model 1 and Qwen2.5-1.5B-Instruct snapshot unchanged.
Agent 339 FP16 tensor/live-hash admission and original README mismatch preserved;
fixed 20/8 layer placement, agent 12/7 GiB allocator caps, guard 5 GiB/device 1.

All three trials loaded fresh sibling workers, agent then guard. Six worker processes
were monitored: in each trial, the busy worker was forcibly reaped (two TERMINATE/-15,
one KILL/-9) while the idle sibling exited cleanly with 1 register and 1 unregister
call (0 unmatched). The parent/owner process completed 90 registers and 90 unregisters
(0 unmatched).

### Root Cause Attribution

The instrumented call stacks in `audit.json` identify the exact creation site of all
three unmatched semaphore objects:
- Every unmatched semaphore was registered by `multiprocessing.synchronize.RLock`
  called via `tqdm.std.create_mp_lock` during model weight loading:
  `transformers.modeling_utils.from_pretrained` -> `_load_pretrained_model` ->
  `convert_and_load_state_dict_in_model` -> `transformers.utils.logging` -> `tqdm`.
- When a worker process is terminated forcibly by SIGTERM or SIGKILL upon timeout,
  its process terminates before executing tqdm/multiprocessing lock cleanup handlers.
- The Python `multiprocessing.resource_tracker` detects these 3 orphaned registrations
  at shutdown and prints the UserWarning.
- This conclusively proves the warning is caused by unhandled tqdm progress bar locks
  in forcibly terminated worker subprocesses, not by a persistent driver or VRAM leak.
  VRAM recovery was confirmed at residual 0 bytes across all 18 samples on both GPUs.

Reproduce without inference, keeping output fresh:

```sh
PYTHONPATH=src:scripts python3 scripts/audit_phase5_pair_ipc_gpu.py \
  --raw results/phase5_pair_ipc_gpu_v1_raw01 \
  --remote-source build/kaggle/pair_ipc_gpu_v1_remote_source01 \
  --output results/phase5_pair_ipc_gpu_v1_audit03
```

Next steps: design versioned lifecycle fix (such as disabling tqdm locks in worker
subprocesses via environment or configuration), proceed with context-stress test,
and finalize Phase 5 runtime integration. Phase 5 remains open.
