# Context/policy v2: failure evidence and memory hypothesis

2026-09-11. Question: did the readiness fix work, and what prevents the fixed
4096-token stress workload from completing under the frozen allocation?

## Direct experiment evidence

One private/offline T4 kernel, `huylmhuhu/react-vn-context-policy-v2`, version 1,
source `0a97953`, source/QA pushed at `a39a9e6` before submission. Status ERROR.
[Selected failure evidence](../../experiments/manifests/phase5_context_policy_gpu_v2_failure01.json)
binds all 69 raw files, two remote files, exact wrapper, 36 source overlays,
private pinned metadata, bootstrap, both HF loads and Dummy 21/84 events.

Both native workers reached READY: agent PID 41 and guard PID 68. The v1 factory
admission error did not recur. Agent load including hashes took 232.950 seconds;
guard 30.953 seconds (exact values in the receipt). The agent then raised
OutOfMemoryError 1.134 seconds after entering stress; its host attempt took
1.557 seconds. No generation-completion or full-cache-boundary artifact exists.
The guard completed readiness only, not a native stress generation.

The observed agent policy resolved against independently authenticated publisher
metadata: repetition penalty 1.05, sampling false, input 4096 and min/max total
length 4608. Both hooks ran once and were restored. This validates those partial
observations, not generation completion. Preserve the original summary's null
actual_model_generation_calls; do not silently replace it with zero.

Both workers were reaped by TERMINATE/-15, not gracefully. All six recovery
samples had signed residual zero on both GPUs. This is sampled recovery, not
proof of exhaustive driver/IPC cleanup. The success auditor correctly rejects
the partial policy inventory. No rerun or model fallback was performed.

## Source evidence, distinct from observations

- Hugging Face, Transformers 5.5.0 (2026), installed-wheel source
  `transformers/integrations/sdpa_attention.py`: on this non-XPU path, Torch >=2.5
  with no attention mask enables native GQA instead of explicitly repeating KV
  heads. Wheel SHA256 `821a9ff0961abbb29eb1eb686d78df1c85929fdf213a3fe49dc6bd94f9efa944`;
  member SHA256 `87f933d1a2d8508df572da5c0748c6b24c22ff2b625796949957dcd86cc57564`.
  This local source is the pinned bundle, not a statement about every HF version.
- PyTorch contributors, [SDPA documentation, version 2.10](https://docs.pytorch.org/docs/2.10/generated/torch.nn.functional.scaled_dot_product_attention.html),
  accessed 2026-09-11: GQA support is restricted; math SDPA uses float32
  intermediates for half inputs. Different attention implementations may differ
  numerically; a memory optimization cannot be assumed byte-identical.
- PyTorch contributors, [CUDA SDPA dispatch source, tag v2.10.0](https://github.com/pytorch/pytorch/blob/v2.10.0/aten/src/ATen/native/transformers/cuda/sdp_utils.cpp),
  accessed 2026-09-11: Flash and cuDNN hardware filters require SM80 or later;
  the efficient dense path rejects grouped-query head counts. Its hardware
  filter permits earlier architectures, subject to other input/build checks.
- NVIDIA, [CUDA GPU Compute Capability](https://developer.nvidia.com/cuda/gpus),
  accessed 2026-09-11: T4 is compute capability 7.5. Device name in the run was
  Tesla T4; the run did not separately record get_device_capability().

## Inference and missing evidence

Native GQA selecting math attention is a plausible explanation for this OOM on
T4. It is not directly demonstrated by this run: no selected SDPA kernel, actual
attention-mask argument, failing operator/device/allocation or failure-time
allocator snapshot was captured. Do not call it conclusive attribution.

Arithmetic illustrates the risk, not a measured peak: one float32 attention
matrix at batch 1, 28 query heads and 4096x4096 occupies 1.75 GiB. Agent weights
already allocate about 9.698 GiB on GPU0 against a 12 GiB process cap; overlapping
temporaries and reserved blocks matter. Endpoint global free memory does not
prove enough headroom under a process cap. No final KV cache was observed.

## Proposed next step, not implemented

Use a no-weights tensor diagnostic to record backend eligibility/selection and
memory under the pinned Kaggle image. If confirmed, evaluate an opt-in
explicit-KV-repeat/memory-efficient SDPA path, with short-shape numerical
comparisons before repeating the unchanged 4096+512/128 workload. Keep models,
precision, placement, caps, deadlines, publisher policy and held-out seals fixed;
do not silently shorten inputs or introduce quantization. Fused numeric changes
must be recorded and validated before runtime adoption.

This changes a frozen computation path: [proposal awaiting owner approval](../project/decision_log.md).
No new GPU submission, attention change or Phase 5 acceptance is authorized by
this evidence note alone. Remaining runtime integration, A4 processing scope,
general final entitlements and grouped Dev/freeze gates are still open.
