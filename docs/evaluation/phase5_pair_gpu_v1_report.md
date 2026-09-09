# First combined agent–guard GPU probe — 2026-09-09

Technical small-context residency/calls/recovery scope passed on the first
submission. Phase 5 is **not accepted**. This is not a model-quality experiment.
[Review receipt](../../experiments/manifests/phase5_pair_gpu_v1_review01.json),
[predeclared contract](../architecture/phase5_pair_gpu_v1_contract.md),
[exact preflight](../../experiments/manifests/phase5_pair_gpu_v1_preflight02.json).

## Execution identity

Private kernel `huylmhuhu/react-vn-pair-gpu-v1`, version1, COMPLETE; one submission,
no retry. Source b76c040, source/preflight pushed to main6596802 before submission.
Offline, two Tesla T4; guard Dataset11942593 private/version1, manifest unchanged.
Qwen2.5-7B-Instruct pinned Kaggle model version1, fixed20/8layer map and12/7GiB
allocator caps; Qwen2.5-1.5B-Instruct guard pinned snapshot on device1/cap5GiB.
Models FP16/SDPA/no quantization. No model weights downloaded to the local machine.

Actual runtime torch2.10.0+cu128/CUDA12.8/Transformers5.5.0. Returned Docker image:
`gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461`.
This digest was learned from this run, not known or asserted before submission.
Remote wrapper hash matches exact preflight. Kaggle returns framework display
label `Transformers`; requested `transformers` refers to the same pinned model1.
Version-qualified source pull returned403; unqualified pull succeeded, hash
verified, no additional version submitted. Both download attempts retained.

## Measurements

| Observation | Agent 7B | Guard 1.5B |
|---|---:|---:|
| HF load including live hash checks | 264.082 s | 32.692 s |
| Host cold readiness including worker startup | 264.423 s | 33.033 s |
| Warm host call | 1.906 s | 1.788 s |
| Native generate duration | 1.835 s | 1.761 s |
| Input / generated tokens | 43 / 8 | 147 / 31 |
| Generated tokens / generate second | 4.359 | 17.599 |

One different small synthetic prompt per role, batch1, greedy/seed42; agent
max512 output tokens, guard max128. These are single-call diagnostic timings,
not matched workload throughput, confidence intervals, TTFT or model ranking.
Cold times include expensive authentication, not just reading weights into GPU.
No response text, hidden reasoning, benchmark score or guard SAFE correctness
is certified by this protocol. Both transport calls returned OK.

At simultaneous readiness, global memory use above observer baseline was
9.798828GiB on device0 and7.621094GiB on device1, exceeding predeclared8/6GiB
residency thresholds. Agent/guard per-process metrics stayed within fixed caps.
These global point samples are not continuous combined peak measurements and
do not establish fit at4096input+512output tokens.

Both workers were reaped using TERMINATE/-15, with lifecycle durations0.885s
and0.840s. **Neither shutdown was graceful.** Six recovery samples, approximately
one second apart, all had signed residual0bytes on both devices relative to
the stable parent-observer baseline. This meets the predeclared last-three
±256MiB gate, not a universal zero-leak or crash-safety claim.

## Evidence and limitations

62 immutable downloaded raw files retained under
`results/phase5_pair_gpu_v1_raw01`; remote source/metadata under
`build/kaggle/pair_gpu_v1_remote_source02`. Every raw hash is in the review receipt.
Eight tools/fault preflight passed on Kaggle;21Dummy terminal checkpoints and
84trace events audited. Two read-only inspections byte-identical:
`results/phase5_pair_gpu_v1_inspection01.json` and `inspection02.json`.

Reproduce envelope, Dummy, raw hash and recovery inspection without model load:

```sh
.venv/bin/python scripts/inspect_phase5_pair_gpu.py \
  --raw results/phase5_pair_gpu_v1_raw01 \
  --remote-source build/kaggle/pair_gpu_v1_remote_source02 \
  --output results/phase5_pair_gpu_v1_inspection03.json
```

The inspector explicitly does not certify execution acceptance. Technical
self-review additionally checked bound model/request/generation identities,
cold/warm deadlines, two distinct worker PIDs, allocator caps and cleanup.
This is assistant self-review under the owner's waiver, not independent review.

Remaining Phase5 work: declare and test maximum-context/combined-cancellation
scope, integrate task-owned pair with runtime v5 without modifying frozen v5,
then grouped Dev guard/model decision and remaining A4/final entitlement scope.
The historical guard quality miss remains unchanged. No held-out Test payload
or private ground truth entered any model, inspector or tuning decision.
