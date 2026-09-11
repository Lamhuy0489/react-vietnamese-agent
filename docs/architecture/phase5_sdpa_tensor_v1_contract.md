# SDPA tensor diagnostic v1 — approved continuation

Owner approved the proposed attention-memory work on 2026-09-11 ("ok làm cho tôi
nhé"), then requested continuation. This protocol is the no-weights feasibility
gate preceding any model attention change. Preserve the two failed context runs.

## Fixed scope and measurements

Pinned Kaggle image/Torch2.10.0+cu128/Transformers5.5.0; two Tesla T4, compute
capability7.5. Authenticate the installed HF SDPA member by its existing wheel
hash. No model mount, HF model construction, weights materialization or
benchmark payloads. Synthetic Q/K/V only, FP16, batch1, head_dim128, seed42.

Agent geometry has28query/4KVheads on device0; guard12/2heads on device1.
Each role has five cases in separate sequential processes (10 children total):

1. Short prefill128: unchanged HF SDPA versus explicit KV repeat + forced
   EFFICIENT_ATTENTION, identical inputs, default scaling, no mask/dropout.
2. Short decode: query1/key257, both implementations, non-causal full history.
3. Long prefill4096, unchanged HF SDPA; OOM is an observed outcome, not a retry.
4. Long prefill4096, explicit KV repeat + forced efficient backend.
5. Boundary decode: query1/key4608agent or4224guard, repeated efficient backend.

Four short comparisons use predeclared per-element abs(diff)<=0.005+0.01*abs(ref).
Record max absolute error, maximum tolerance excess and pass/fail, not just a
boolean. These are tensor checks, not end-to-end model-output parity or tuning.
No tolerance changes based on the result. Candidate path may not fall back to
math/Flash. Unsupported dispatch is ERROR; candidate OOM/error/parity failure
makes candidate_valid=false without destroying otherwise valid failure evidence.

Each child has a2GiB tensor-only process allocator cap and90second process limit.
This is an explicit headroom probe, NOT a replacement for the model's frozen
12/7GiB agent and5GiB guard caps, and NOT an exact reproduction of its allocator
state. Inputs are regenerated/hash-compared between long modes. Short parity
keeps both outputs for comparison; its peaks cannot serve as isolated mode speed
or memory rankings. CPU profiler captures actual dispatched ATen operator names;
wall timing includes instrumentation/synchronization, not uninstrumented latency.
Record native GQA eligibility, device identity, global endpoints and allocator
peaks even on caught OOM. Never persist tensor values or model-generated text.

## Package, acceptance and launch

28-file additive overlay preserves the25-file native CPU package. Archive and
expanded/PAX isolated preflights run eight tools,21Dummy tasks/resume/missing-only
20retained checkpoints, native progress controls and the actual new dispatcher
in stub mode. Stub output explicitly has no native/candidate-acceptance claim.
Full QA and source/receipts must be on GitHub before submission.

New private/offline kernel `huylmhuhu/react-vn-sdpa-tensor-v1`, version1,
NvidiaTeslaT4, timeout1800seconds; existing private Datasetversion1 for frozen
source/dependencies, model_sources empty. Do not extract its guard archive.
One push only. Download all raw outputs to a fresh directory; independently bind
remote source, pinned metadata, bootstrap, Dummy and all12tensor files.

An audited tensor COMPLETE may contain baseline OOM. Report it faithfully and
separately from candidate_valid. Numerical/long candidate success is permission
to prepare the already owner-approved versioned model optimization, not evidence
that full Qwen generation or Phase5 has passed. Keep full4096+512/128 stress,
models, decoding, placement, caps and deadlines unchanged in that next gate.
Actual failure-time kernel in context v2 was not observed: tensor results cannot
retroactively establish conclusive attribution for that old run.
