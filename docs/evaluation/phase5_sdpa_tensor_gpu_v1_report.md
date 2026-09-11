# SDPA tensor GPU v1 — audited feasibility result

2026-09-11. One submission of private/offline
`huylmhuhu/react-vn-sdpa-tensor-v1`, version 1, completed. Worker source
`5aabea015c1fa30c56dd908b51e382a59e092567`; source and pre-submit QA were on
GitHub at `50a6092` before the push. This is a no-weights component experiment,
not full model inference or Phase 5 acceptance.

## Authenticated evidence

- [Predeclared protocol](../architecture/phase5_sdpa_tensor_v1_contract.md),
  [exact preflight](../../experiments/manifests/phase5_sdpa_tensor_gpu_v1_preflight01.json)
  and [pre-submit QA](../../experiments/manifests/phase5_sdpa_tensor_gpu_v1_pre_submit_qa01.json).
- [Selected independent audit](../../experiments/manifests/phase5_sdpa_tensor_gpu_v1_audit01.json):
  valid, source_authenticated and candidate_valid are true; phase5_accepted is false.
  Two local audits are byte-identical, SHA-256
  `278c3f0759e71c5d6291e03303ed859487ecebcc5fb8deb77b17e6894494e772`.
- All 59 raw files and two remote files authenticated, including 12 tensor
  artifacts, bootstrap, log and 21 Dummy tasks / 84 observable events.
  Dummy checks transport/checkpoints, not semantic task success.
- Ten fresh native child PIDs, fourteen attention invocations, zero model loads
  and zero model.generate calls. No model mounts or guard weights extracted.
  Torch 2.10.0+cu128 / CUDA 12.8 / Transformers 5.5.0, two Tesla T4; pinned HF
  integration hash verified. No local native tensor or model execution.

## Numerical and memory results

All four short comparisons passed the frozen per-element criterion
`abs(candidate-reference) <= 0.005 + 0.01*abs(reference)`.

| Geometry | Maximum absolute error | Maximum tolerance excess | Result |
| --- | ---: | ---: | --- |
| Agent prefill 128 | 0.001953125 | -0.0048159072 | Pass |
| Agent decode 1/257 | 0.000244140625 | -0.0049672434 | Pass |
| Guard prefill 128 | 0.0009765625 | -0.0048194886 | Pass |
| Guard decode 1/257 | 0.000244140625 | -0.0049672434 | Pass |

Long modes used identical hash-matched Q/K/V in separate fresh processes.
All modes below used the predeclared **2 GiB tensor-only allocator cap**.
MiB means 1,048,576 bytes. Peaks include tensors/allocator activity in that
process; they are not the full model's VRAM requirement.

| Geometry / path | Status | Peak allocated MiB | Peak reserved MiB | Instrumented seconds |
| --- | --- | ---: | ---: | ---: |
| Agent 4096 / native | OOM | 396.000 | 446 | 4.333821 |
| Agent 4096 / repeated efficient | OK | 120.000 | 132 | 4.193053 |
| Guard 4096 / native | OK | 1920.172 | 1978 | 4.360918 |
| Guard 4096 / repeated efficient | OK | 52.000 | 56 | 4.200026 |
| Agent decode 1/4608 / repeated efficient | OK | 73.014 | 86 | 4.243528 |
| Guard decode 1/4224 / repeated efficient | OK | 28.881 | 36 | 4.130938 |

The agent native OOM peak is **only successfully allocated memory before the
failed allocation**; it does not quantify the memory required to complete.
No agent reduction ratio is inferred. Guard's two successful long modes show
lower allocated peak for the candidate in this isolated experiment.

The profiler observed `aten::_scaled_dot_product_attention_math` on every native
path, including the agent OOM, and
`aten::_scaled_dot_product_efficient_attention` on all eight candidate paths.
Native GQA was enabled; native flash/efficient/cuDNN eligibility was false on
all ten input geometries. Candidate dispatch had no math/Flash fallback.
This supports the hypothesized mechanism for this tensor experiment, but does
not retrospectively prove which operator caused the older context-v2 OOM.

Timings include CPU profiler startup, dispatch initialization and synchronization.
Short native runs always preceded candidates within their process; no warm-up
or repeated trial was performed. **Do not publish these as speedups, isolated
kernel latency, throughput or multi-model benchmark results.** Raw timings for
all fourteen invocations remain in the selected audit. The worker completion
marker appeared at log elapsed 169.037 seconds; this is not model latency.

Profiler cycle warnings and notebook-export SyntaxWarnings remain in the raw
log. Each measurement has one profiler context/cycle and captured operator
names; no warning was suppressed or used to exclude a measurement. No semaphore
warning was observed; this does not establish exhaustive IPC cleanup.

## Scope and next gate

The tensor feasibility gate passed. No model attention has yet changed. Short
random-tensor parity does not establish full-length numerical parity, model
answer equivalence, KV-cache correctness, quality or security acceptance.

Next: [versioned model-attention integration plan](../architecture/phase5_efficient_stress_v1_design.md),
retaining the approved models, FP16, placement, model allocator caps, deadlines,
publisher decoding and exact 4096 + 512/128 context stress. This requires new
code/tests, independent sidecar auditing and exact package preflight before a
new GPU submission. No retry of either old OOM identity.

Raw directory: `results/phase5_sdpa_tensor_gpu_v1_raw01`; remote source:
`build/kaggle/sdpa_tensor_gpu_v1_remote_source01`; repeat audits:
`results/phase5_sdpa_tensor_gpu_v1_audit01.json` and `..._audit02.json`.
Keep these immutable and untracked. No Test payload or private ground truth
was accessed; Test seals were checked by hash only.
