# Phase 5: runtime-input admission and budgeted agent adapter v1

This is a new engineering contract, not a change to the full-inventory scanner,
its failed README result, frozen runtime, prompts, data, or historical scores.
Only synthetic CPU fixtures are used during implementation. No held-out payloads,
private ground truth, local model download or GPU submission in this milestone.

## Runtime input admission

Authenticate live mount bytes against the exact committed publisher inventory
SHA256 `9023d04a65f44a4e4beef29efba9f1ca088e2af1990cc82e586f457d4c5c43b3`.
The machine-readable constant in the implementation must match the actual file;
the verified identity is recorded in the receipt. All eleven runtime files must
match. Optional documentation must match if present, except the observed README:
6005 bytes, SHA256 `0981c06fb21db45eca831ebafa68861b654587566a8e3071aece79cf60329b71`,
Git blob `19613c71726c705978eb7fed4ce46c8625418a5b`.
No other mismatch is admitted. Preserve full_inventory_match=false when this
exception occurs. Documentation is never read into prompts or used as model code.
No copies or filtered weight directories are made; native local-only Qwen2 loads
the verified mount. Reject unknown files, links and directories as in scanner v1.

Check native Qwen7B geometry plus the exact 339 named parameter shapes, index-to-
shard mapping and safetensors header offsets before importing torch. Headers
are bounded to 2 MiB each; reject duplicate JSON keys, unknown tensors/dtypes,
shape mismatch, gaps, overlaps, incomplete coverage or byte-size inconsistency.
BF16/F16 serialized weights only; runtime parameters must all be FP16. Headers
do not prove numeric quality or absence of NaN. Rehash after loading and require
the same complete content identity. Trusted read-only mounts are required: this
is not an adversarial concurrent-writer defense or a cryptographic GPU attestation.

The raw publisher config stays under the frozen strict geometry validator.
After loading only, native config None defaults for rope_scaling/auto_map/
quantization_config are treated as absent; active values remain rejected.
Native layer_types, if present, must be all28 full_attention. This boundary
accounts for native [Qwen2Config defaults](https://github.com/huggingface/transformers/blob/v4.57.1/src/transformers/models/qwen2/configuration_qwen2.py),
not a relaxation of snapshot authentication or extended-context admission.

## Adapter

Dedicated agent process only. Load agent first, then the existing separate guard
process; do not instantiate guard in the agent allocator. Require exactly two
T4 devices and planner admission before loading. Set PyTorch process allocator
fractions to the planner's 12/7 GiB ceilings before tokenizer/model load; pass
the explicit 20/8-layer device map and matching max_memory to native Qwen2.
No auto placement, quantization, CPU/disk offload, remote code or network fallback.
Check exact loaded parameter names/shapes/dtypes and every parameter/buffer
placement. Dynamic rotary buffer alone may be FP32. Allocation/reservation
observations must remain within caps. This bounds the caching allocator, not
all CUDA/driver allocations or global memory; it does not prove combined fit.

Fresh greedy generation config and dynamic KV cache per request, seed42,
batch one, full rendered input1–4096 tokens, output limit512. Reject rather
than truncate, never reuse caller message objects, never request/store hidden
reasoning. Concurrency, model errors, invalid context and metrics failure fail
closed without automatic retry. Retire a failed backend; the future process owner
must terminate/reap it. Synchronous adapter alone has no hard timeout or proven
GPU recovery and must not be used as a deadline controller.

Record content/plan/generation identity, load/tokenize/generate/call time, input/
output counts, per-device allocated/reserved/peak/global-free measurements and
library versions. Logs exclude prompt/response/exception text. Generation peaks
are sampled allocator counters, not device-global peaks. No speed/quality claim
from CPU fakes. Native dependency versions and actual tensor-operation smoke,
isolated archive/expanded runtime preflight, GPU lifecycle/context protocol and
run identity must be frozen before any combined GPU submission.

## API evidence (checked 2026-09-09)

Allocator fraction limits the caching allocator relative to visible total memory,
not every allocation: [PyTorch 2.8 documentation](https://docs.pytorch.org/docs/2.8/generated/torch.cuda.memory.set_per_process_memory_fraction.html).
Explicit device_map, local_files_only, dtype and max_memory are loader options:
[Transformers 4.57.1 documentation](https://huggingface.co/docs/transformers/v4.57.1/main_classes/model).
Header offsets are relative to the data buffer, duplicate keys and holes are
invalid: [safetensors format](https://github.com/safetensors/safetensors/blob/main/README.md#format).
