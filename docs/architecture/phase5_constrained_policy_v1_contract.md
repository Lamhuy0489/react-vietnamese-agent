# Phase5 constrained worker composition and native CPU gate v1

2026-09-16. Continues the [isolated adapter contract](phase5_constrained_guard_v1_contract.md).
No baseline edits, held-out Test, private ground truth or semantic retry.

The candidate's earlier source-admission implementation is corrected: native
`generate` is decorated with `torch.no_grad`. Require its bound function to be
the exact SDK GenerationMixin method, then hash the unwrapped Transformers body
with `inspect.unwrap`. Hashing the wrapper's source would wrongly compare Torch
`_contextlib.py` to Transformers `generation/utils.py`. Prior synthetic QA did
not exercise this constructor; retain that evidence as historical, not native proof.

## Composition

Guard worker: readiness → response sidecar → constrained factory → progress
initialization → policy → attention → authenticated guard loader. At each request,
the constraint scope wraps the policy/attention call, never bypasses it with a
direct model call. All four request counters must agree; errors retire every
layer and remove constraint, policy and attention hooks. Agent factory,
independent host witness and shutdown2s remain unchanged. Cache behavior follows
the prior adapter contract inside one owning worker.

The new native-pair factory is lazy, spawn-picklable and opt-in. Inputs, snapshot,
root separation and factory topology are admitted before loading. This does not
yet connect the host security classifier/cache to constrained evidence, join the
new receipts into the benchmark release auditor or authorize GPU experiments.

## Fixed native CPU control schedule

Run four cases in order: `success01`, `success02`, `forced_bos`, `interrupt`.
Use actual pinned Transformers5.5.0/Torch2.10.0+cu128 GenerationMixin and the
authenticated Qwen tokenizer. Instantiate a fresh **random tiny Qwen2** for each
case: vocabulary151936, hidden8, intermediate16, one layer/head/KVhead, tied
embeddings, context4096, seed42. No pretrained weights are opened, loaded or
downloaded; no model-quality inference, GPU or benchmark task is involved.

The two success cases traverse the real native generation loop and existing
constraint scope; output must be a complete token-language document plus EOS.
Real forward calls must equal returned output tokens. Processor/config admission
must reject forced-BOS before any forward. A controlled first-forward interrupt
must propagate and remove request hooks; neither negative case may have a
completed receipt. Each failed case discards its model; no retries.

Verify installed logits/generation/Qwen source against the pinned offline wheel,
tokenizer hashes before/after, fixed language identity, stage counts and thread
restoration. Preserve receipts and timing, not raw generated text or reasoning.
Times describe tiny CPU controls, not the production1.5B guard's latency/quality.

The tiny CPU model does **not** execute the28-layer CUDA attention adapter.
Combined wrapper behavior is checked separately with explicit synthetic tensors;
neither evidence proves production CUDA execution or host runtime acceptance.

## Package and launch gate

Private CPU notebook only, offline, no model mounts, reuse pinned private
Datasetv1. New requested handle `huylmhuhu/react-vn-constrained-generate-cpu-v1`;
record the actual handle/version after submission, never rerun the old notebook.
Before upload: commit/push source, verify source closure and exact archive plus
expanded mount in fresh offline venvs. Execute eight tool schemas,21clean Dummy
tasks and missing-only resume; native launcher runs metadata-only locally and
must state that native libraries were not executed. All source and raw hashes
are retained. Terminal source/version/download audit is required before claiming
this native gate passed. Phase5 acceptance remains open.
