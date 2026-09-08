# Phase 5: dual-GPU placement admission v1

CPU-only engineering admission, not combined GPU fit, model selection or Phase5
acceptance. Preserve measured pilot, guard adapters, runtime, prompts and receipts.
No model loading, benchmark inputs, Test payloads or network calls in this module.

Candidate agent is the already piloted Qwen2.5 7B Instruct, FP16, batch one;
candidate guard is the pinned Qwen1.5B adapter on device1 with its unchanged
5GiB process allocator cap and 1GiB free headroom. Exact agent weight acquisition
and loader binding remain prerequisites to a real run; model shape or parameter
count alone does not authenticate weights or establish Kaggle/HF byte equivalence.

The proposed explicit agent map puts embeddings and layers0–19 on device0,
layers20–27, final norm, rotary module and lm_head on device1. Agent process
allocator ceilings are 12GiB/7GiB, not the old loader's 13GiB/device weight map.
Guard uses a separate process. Reserve an additional 1GiB global headroom per
device, separate from process caps. Before either model loads, require observed
free memory >= agent cap + guard cap where applicable + global headroom.
These checks do not reserve GPU memory, include every CUDA allocation or prevent
another process racing for it. A future adapter must enforce caps independently
in the agent process and verify every parameter/buffer's actual placement.

The planner supports only the specified dense Qwen2.5 7B geometry:28layers,
hidden3584, intermediate18944,28query/4KVheads, head128,vocab152064, untied
embeddings. Formula includes Q/K/V bias and both per-layer norms; expected count
7,615,616,512 matches the previously audited model_setup. No quantization,
offload, tensor parallelism, tied embeddings or alternate geometry is assumed.

Admission accounts separately for FP16 parameters, batch-one dynamic K/V cache
through input4096 + output512 tokens and a declared 1GiB workspace allowance on
each GPU. This allowance is an engineering hypothesis, not an activation or SDPA
upper bound; the estimate must never be labelled peak VRAM or proof of fit.
Reject over-budget candidates before loading. Count exact rendered input tokens,
reject empty/overlong input or changed output budget rather than truncate.
Agent greedy512/seed42 and guard128 remain distinct generation contracts.

Planner output binds shape, map, budgets, context and analytical assumptions in
a canonical SHA-256. Pure admission validates finite integer memory samples,
exact two-T4 identities, total/free constraints and cumulative process budgets.
Post-load validation rejects unknown, duplicate, missing, CPU/disk or misplaced
tensor paths. It checks placement coverage, not tensor content or shape integrity.
Pre-load geometry validation rejects mismatched heads/layers/dimensions, changed
bias or tying, remote-code maps, quantization and extended-context overrides.
Config validation is not publisher authentication or a check of actual tensors.

Next: acquire/bind exact agent snapshot, build a separate budget-enforcing HF
adapter, verify parameter/buffer inventory and context rejection with CPU fakes,
then declare combined-residency/context/cancellation trials. Package exact source,
run both isolated mount layouts, commit/push and check quota before GPU. Do not
reuse this CPU admission receipt as evidence those later gates have passed.
