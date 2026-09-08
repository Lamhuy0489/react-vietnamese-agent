# Agent/guard placement admission — 2026-09-09

Phase5 CPU-only preparation after successful cancellation/VRAM recovery.
[Contract](../docs/architecture/phase5_coexistence_placement_v1_contract.md).
New module `src/react_agent/llm/coexistence_placement_v1.py`; no torch/model loads,
network, Test payload/GT or changes to any frozen adapter/runtime.

Candidate Qwen7B agent: embeddings/layers0–19 device0, remaining8layers/final
norm/rotary/head device1. Process caps12GiB/7GiB; guard keeps5GiB/device1.
Separate global headroom1GiB/device => require13GiB live free on each before
either model loads. These are not memory reservations or fit guarantees.
FP16 weights9,697/4,488GiB; dynamicKV at4096+512tokens adds0,176/0,070GiB;
workspace allowance1GiB each => estimates10,873/5,558GiB. Actual activations,
allocator fragmentation, CUDA overhead and concurrent fit remain unmeasured.

Typed deterministic admission rejects missing/duplicate devices, insufficient
free bytes, invalid samples/budgets/context, misplaced/offloaded/unknown tensor
paths and missing module coverage. Plan digest binds map, geometry and estimates.
Does not authenticate weights or prove tensor shapes; adapter must bind those.

## Claim-to-evidence

- Qwen team, Qwen2.5-7B-Instruct configuration, accessed2026-09-09:
  [official config](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/raw/main/config.json).
  Direct metadata:28layers,hidden3584,intermediate18944,28query/4KVheads,
  vocab152064,untied embeddings,32768positional limit. Mutable main URL is only
  shape evidence, not a pinned acquisition receipt or Kaggle/HF byte equivalence.
- Local audited pilot setup:7,615,616,512parameters,FP16,twoT4 with
  15,636,037,632bytes/device. Script checks model_setup against
  [pilot audit](../experiments/manifests/measured_qwen7b_v1_audit.json), reads only
  setup metadata, not saved model responses or task traces.
- Analytical inference: parameter/KV formula under dense Qwen attention and
  batch-oneFP16 matches that parameter count. Workspace1GiB is a declared
  engineering allowance, not sourced as an upper bound. No quality/model choice.
- Direct historical evidence: guard cancellation recovered observed VRAM;
  [report](../docs/evaluation/phase5_guard_cancellation_v1_report.md). That run did
  not have agent resident and cannot validate the new combined map.

## Verification and next action

56 targeted CPU tests pass, including geometry mismatch, literal type coercion
and misleading GPU-name rejection. Preflight01/02 retained as development only;
contract/source evolved before freeze, so neither is selected evidence. A fresh
committed-source reproduction must bind the final geometry validator and tests.
The verifier
binds source/plan/metadata and preserves134frozen adapter hashes and Test seals.
Full quality checks are in progress; no new GPU submission.
Next: versioned sharded agent snapshot acquisition/authentication and budget-
enforcing HF loader. Then complete CPU fake/context tests and exact packaged
preflight before declaring/running combined GPU stress. Do not substitute the
old 13GiB/device loader or use these estimates as measured memory results.
