# Efficient model context stress v1

2026-09-11. Implements the owner-approved next step after the authenticated
[tensor gate](../evaluation/phase5_sdpa_tensor_gpu_v1_report.md). This is an
additive diagnostic treatment, not benchmark/runtime adoption. Frozen source,
models, FP16, 20/8 agent placement, 12/7 GiB agent and 5 GiB guard caps, 180/120s
warm request deadlines, publisher decoding and 4096 + 512/128 workload remain.

## Execution and evidence

ReadyFactory remains outermost; ThreadProgressFactory applies before model
loading; new EfficientStressFactory wraps the original PolicyStressFactory and
ContextStressFactory with their unchanged native-loader type checks.
The new backend is one-request, PID-owned, non-concurrent and non-nested. It is
not suitable for a shared/threaded application process. Native imports are lazy.

The pinned Transformers SDPA member and native Torch binding are authenticated.
Within the dedicated worker only, temporarily override `use_gqa_in_sdpa` to
select HF's own `repeat_kv` branch. Preserve HF's mask/scale/causality code; force
only EFFICIENT_ATTENTION and wrap the original Torch SDPA callable once. Restore
both callables and backend flags in finally, including error/interruption paths.
Unsupported dtype/mask/shape/dispatch is a failure, never a math fallback.

Every call checks efficient-only backend flags, one preceding HF eligibility
call, repeated logical heads, exact FP16 shape, 128 head dimension, expected
layer/device order, dropout zero and Qwen scale `128**-0.5`. Explicit masks, if
present, must be full `[1,1,query,key]`, FP16/bool on the query device; mask values
are neither changed nor stored. Maskless prefill is causal; single-query decode
or explicitly masked attention is not `is_causal=True`.

There must be 28 attention calls per forward, ordered across all 28 layers:
14,364 agent calls (513 forwards), 3,612 guard calls (129 forwards). These include
the original stress backend's separate final-token forward, not an extra model
generation. Key lengths end at 4608/4224. Existing full-layer KV and resolved
publisher-policy auditing remains authoritative alongside new attention evidence.

Profile exactly two existing attention calls per role: first prefill layer and
first layer of the final boundary forward. Require the observed efficient ATen
operator, not math/Flash. All remaining calls have efficient-only flags and
geometry guards but are not individually profiled. No extra model forward or
warm-up is added. Timings include this instrumentation, hence are not benchmark
latency, speedups or uninstrumented multi-model performance rankings.

Separate per-role JSON sidecars: entered, dispatch_1, dispatch_2, restored and
completed (five on success). Failures preserve error and all reached stages;
forced termination can leave incomplete sidecars. No tensor/token values, model
answers, exception text or hidden reasoning. Independent auditor joins these to
worker PID/model identity, existing stress/policy records and remote source.
Completion of one diagnostic does not establish answer parity, quality, ASR,
graceful worker exit, exhaustive cleanup or Phase 5 acceptance.

## Package and launch

New private/offline kernel `huylmhuhu/react-vn-efficient-stress-v1`, one version1
submission, pinned same image/2T4/private Datasetv1/agent model mountv1 and
3600s kernel timeout. No account cycling. A 42-file overlay preserves every
previous 36-file context-v2 member. Exact source-only archive and expanded/PAX
preflights run eight tools, 21 Dummy/resume, 20 retained checkpoints, six native
progress controls per layout, the old factory failure control and the actual
new dispatcher with corrected efficient factory/readiness rehearsal.

CPU tests execute hash-authenticated HF SDPA source against synthetic Tensor
objects for both roles and masked/maskless full forward sequences. This verifies
composition, not native CUDA numerical behavior. The preceding tensor GPU gate
provides only the previously declared component numerical evidence.

Before push: full QA, clean committed packaged source, exact two-layout receipt,
GitHub source/QA, private readiness/pins/quota checks. Download to a fresh raw
directory; independently audit twice without changing inputs. Failed treatment
or infrastructure outcomes remain preserved and must be classified before any
new identity. No silent reruns, model/context/cap changes or Test access.
