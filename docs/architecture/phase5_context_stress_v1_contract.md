# Context stress v1 — native adapter and CPU runner contract

This implements the previously declared [design](phase5_context_stress_v1_design.md)
in new files only. No old backend, dataset, prompt, runtime or GPU output changes.
Not packaged/submitted to Kaggle yet; CPU mocks and synthetic spawn do not certify
GPU maximum-context fit. Model weights are not loaded or downloaded locally.

## Composition and request boundary

New `ContextStressFactory` accepts only the exact authenticated agent-v2/guard-v1
backend classes, model identities and frozen guard config. The HF entry composes
the existing `hf_pair` lazy loaders with `ThreadProgressFactory` outside the stress
factory so native progress configuration precedes loading. Fixed placement/caps,
agent1200/guard120 cold and agent180/guard120 warm deadlines remain unchanged.

Each backend accepts one fixed diagnostic marker and default seed42/greedy
512-agent or128-guard transport config. Any request/error consumes that instance;
no retry, cache reuse or concurrent request. Marker is a host-side diagnostic
command only: not a benchmark prompt, tool capability or runtime policy change.
The model sees only the fixed synthetic token geometry from `context_geometry_v1`.

Generation uses fresh native config, dynamic cache, batch1, min_new_tokens equal
to max_new_tokens; EOS IDs copied unchanged. Return sequences/cache for immediate
local inspection, never hidden-state/attention/score outputs. No decoding or raw
token IDs in durable files/IPC; only hashes, counts and tensor metadata survive.

Pre-submit source audit found that Transformers5.5.0 fills the fresh config's
None fields from publisher settings, then global defaults. Thus prepared.json
is a **submitted configuration receipt**, not the fully resolved runtime policy.
Explicit greedy/length settings remain fixed; publisher repetition settings can
still apply. [Finding](../../experiments/manifests/phase5_context_stress_generation_defaults_finding01.json).
Before GPU, add versioned publisher/resolved-policy evidence and its auditor;
do not rewrite frozen backend v1 or silently change the benchmark decoding.

## Full-boundary cache observation

After generation, require exact input4096 plus output512/128 sequence shape and
unchanged input prefix. Inspect every layer's keys/values: batch/head/sequence/
head-dimension shape, FP16 dtype and expected device. Record metadata and summed
KV tensor bytes by device, not tensor values. Cache must span4607/4223positions.

Feed the last emitted token exactly once through the native model with existing
cache, complete all-ones attention mask, use_cache and logits_to_keep1. Inspect
all layers again at4608/4224positions; this is a separate forward, not another
sampled token. Log separate final-forward timing; do not silently equate token
count with cache residency. A failure preserves the earlier generation record.

Evidence from Hugging Face Transformers5.5.0, accessed2026-09-10, and hash-verified
local wheel SHA256 `821a9ff0961abbb29eb1eb686d78df1c85929fdf213a3fe49dc6bd94f9efa944`:
[generation source](https://github.com/huggingface/transformers/blob/v5.5.0/src/transformers/generation/utils.py)
prepares a cache bounded at max_length−1; [Qwen2 forward](https://github.com/huggingface/transformers/blob/v5.5.0/src/transformers/models/qwen2/modeling_qwen2.py)
accepts past_key_values and returns the updated cache; local cache_utils.py
DynamicLayer stores sequence length in tensor shape. These are source-level
facts motivating the checks, not empirical proof that the actual GPU run fits.

## Durable measurements and lifecycle

Per-worker exclusive fsynced files: entered, prepared, generated, completed;
on ordinary failure also error-class-only record, never exception text. PID,
role/model identities bind each stage. Progress before forced exit remains raw
partial evidence; completion is not inferred from folder presence.

Record tokenizer/construction time, synchronized aggregate generation time
(includes prefill, no separate prefill claim), synchronized final-token-forward
time and backend total. Parent measures end-to-end calls independently. Reset
and read per-process allocator peak counters; retain global free endpoints only,
not a claim about continuous global GPU peak. Observe generated/full KV metadata
while cache remains live; do not manually unlink/unregister or flush CUDA caches.

New `run_context_probe` calls agent then guard with both resident, validates ACK
and PID-bound completed-stage shapes/counts, closes in finally, and retains
six recovery samples at1s on GPU (zero delay in CPU stub). Last three within
±256MiB and all worker handles reaped remain required. Forced/graceful are
reported via unchanged supervisor lifecycle. Failed native attempt count is
unknown/null, not zero or merely completed ACK count. Stub claims zero native
calls and cannot pass the native evidence flag. A separate read-only GPU audit
must still verify all records/source/identities; the runner flag is not release
acceptance or IPC cleanup proof.

## Required next steps before GPU

CPU fake tests cover both roles, forced lengths, fresh config/cache boundary,
final token/mask routing, cache layers/shapes/dtypes/devices, error redaction,
single-use/concurrency, cap/position checks and native-loader admission.
Real spawn synthetic runner tests cover successful calls, failing observers,
request failure/interruption, missing native receipts and always-close behavior.
Full QA and two source-bound CPU rehearsals precede selected receipt.

The [independent artifact auditor](../../knowledge/context_stress_audit_v1.md)
now validates complete 23-file evidence with mutation/CLI tests. Static checks
against the hash-pinned Transformers5.5.0 wheel confirm constructor/serialization,
Qwen forward arguments and dynamic-cache storage. These do not execute native
libraries, reconstruct tokenizer IDs or authenticate a remote GPU release.
Still required: versioned allowlisted GPU wrapper and exact archive/expanded/PAX
8tools/21Dummy/resume preflight, outer source/bundle release audit, source/receipts
push and current private inputs/quota. Preserve the prior native progress-policy
rehearsal: the context stub alone does not configure native tqdm.
No context GPU launch is authorized by file presence alone. No Phase6/7/Test,
model-quality tuning, automatic retry or changes to benchmark decoding.
