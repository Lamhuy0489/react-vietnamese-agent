# Efficient stress GPU v1 — native full-context gate passed

2026-09-11. One private/offline Kaggle submission:
`huylmhuhu/react-vn-efficient-stress-v1`, version 1, COMPLETE.
Source `5267218578b1366f7c0ed5c9a0183f19b7fef585`;
pre-submit source/QA pushed at `a66514e`; submission tracking at `0c838e2`.

[Protocol](../architecture/phase5_efficient_stress_v1_contract.md),
[preflight](../../experiments/manifests/phase5_efficient_stress_gpu_v1_preflight01.json),
[QA](../../experiments/manifests/phase5_efficient_stress_gpu_v1_pre_submit_qa01.json),
[selected audit](../../experiments/manifests/phase5_efficient_stress_gpu_v1_audit01.json).

## Result

Both native models completed the full predeclared synthetic context workload
without OOM under unchanged FP16, model revisions, 20/8 agent placement,
12/7 GiB agent and 5 GiB guard allocator caps, and 180/120s warm deadlines.
Two model.generate calls and two separate last-token forwards were measured.
Both models remained resident during the sequential agent then guard requests.

The two independent audits are byte-identical, SHA-256
`f60467ea45e5e46b523cf365a98cfb3e56e266b27963b7b7a01acef7541b9d5f`.
All 90 raw files and two remote files authenticated, including the pinned
bootstrap, 42-file overlay, model/publisher inputs and 21 Dummy / 84 events.
Dummy success checks transport, not semantic task quality.

## Measurements

The following values are derived from the immutable completed/call/closed JSON
records, not edited model output. Generation includes prefill and the first
profiled attention call; final forward includes the second profiled call.

| Role | Input + new tokens | Model load s¹ | Generation s | Final forward s | Host request s | Full KV tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| agent | 4096 + 512 | 276.196 | 48.447 | 0.098 | 48.664 | 4608 |
| guard | 4096 + 128 | 31.365 | 6.085 | 0.044 | 6.221 | 4224 |

¹ Worker factory load interval includes authentication and loading; it is separate
from the measured warm request. One observation per role, not a statistical
comparison, isolated decode benchmark or model-speed ranking.

| Process / GPU | Peak allocated GiB | Peak reserved GiB | Frozen allocator cap GiB |
| --- | ---: | ---: | ---: |
| agent / 0 | 10.408 | 10.596 | 12 |
| agent / 1 | 5.077 | 5.246 | 7 |
| guard / 1 | 3.248 | 3.293 | 5 |

These are per-process allocator peaks during each stress request, not global
device peaks or a concurrent sum of peaks. GiB = 1,073,741,824 bytes.
The guard shares GPU1 with the resident agent. No caps were increased.

All 28 layers per model had the expected FP16 KV shape and placement. Agent
full KV bytes: GPU0 188743680, GPU1 75497472;
guard GPU1 121110528. Generation initially retained 4607/4223
tokens in cache; the separately measured last-token forwards completed 4608/4224.

## Attention and policy integrity

Agent had 14,364 completed attention calls and guard 3,612, matching all layers
and forwards. Every call passed efficient-only backend flag, repeated-head,
dtype, geometry, device, scaling and causal checks. All observed masks were
None in this run; native explicit-mask execution was not measured here.

Actual ATen efficient dispatch was observed at first prefill and first layer
of final-boundary forward for each role (four profiled calls total). The other
calls were guarded but not profiled individually. No extra forward/warmup or
math/Flash fallback was used by the treatment. Both helper/builtin bindings and
backend flags were restored. Publisher metadata and actual resolved generation
policy passed the unchanged independent auditor; repetition settings were not
neutralized or tuned.

## Cleanup and limits

Both workers were TERMINATE / exit -15 and reaped; zero graceful exits. Six
post-cleanup samples had signed residual zero bytes on both GPUs. No semaphore
warning was observed. This does not establish native-generation cancellation,
driver crash safety or exhaustive IPC cleanup.

The approved efficient treatment passed this full-context diagnostic where the
older context-v2 run had OOM. Keep both outcomes: this does not retrospectively
prove the old failure-time operator, full-model answer parity, semantic quality,
guard selection, ASR or benchmark performance. Tensor short-shape numerical
parity remains separate evidence. No generated text/token values were retained.

Raw: `results/phase5_efficient_stress_gpu_v1_raw01`;
remote: `build/kaggle/efficient_stress_gpu_v1_remote_source01`.
Audits01/02 are under results; selected copy above is byte-identical.
No local model/native tensor execution, Test payload or private GT access.
Test prerequisite checks were hash-only.

## Next work

The native full-context feasibility gate is now passed for this treatment only.
Phase 5 remains open: reusable production attention scope and ModelPair runtime
integration, A0–A6 isolation/parity/lifecycle tests, A4 processing-scope anchors,
general final entitlements, grouped Dev guard/model decision and differential
freeze. The current backend is single-use and accepts only fixed stress shapes;
do not plug it directly into normal ReAct requests or claim benchmark adoption.
