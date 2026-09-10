# Context/policy stress release v1

Separate diagnostic, not Phase5 closure, model selection or benchmark decoding.
Extends the [stress design](phase5_context_stress_v1_design.md) and
[policy observation](phase5_generation_policy_v1_contract.md); frozen modules
and raw runs remain unchanged. No Test/private GT, local model loads or weights
acquisition. Public publisher generation JSON is permitted metadata only.

## Publisher authority and combined audit

Two generation_config.json byte copies are bound to pre-existing immutable
upstream inventories, using size, Git blob SHA1 including the blob header and
SHA256. Qwen7B revisiona09a354 has repetition_penalty1.05; Qwen1.5B revision989aa798
has1.1. Neither value is tuned or neutralized. Both use explicit do_sample=false
in the diagnostic. Publisher's version4.37.0 is preserved in the raw JSON;
the observer's serialization label is pinned native5.5.0. Missing fields are
native constructor None, then native publisher/global resolution applies.

`context_policy_audit_v1` authenticates these inputs independently of the five
self-reported policy receipts. It reconstructs the complete agent admitted-file
content digest, binds the guard generation file to its snapshot, reuses the
23-file native-stress audit, then checks10policy files against role/PID, model,
prepared config and publisher identity. Distinct non-nested roots and exact
inventories are required. This component does not itself authenticate Kaggle.

The outer release auditor additionally binds frozen bundle, source overlay,
remote code/private pinned T4 metadata, bootstrap identity, Dummy21/84events,
the full80-file output inventory and completion log. All inputs remain immutable.
Shutdown semaphore warnings are retained separately from VRAM/reap evidence.

## Worker and exact preflight

New dispatcher `run_phase5_policy_stress_v2.py` delegates HF mode to the frozen
policy stress entry without changing requests, factories or limits. It validates
fresh/separate roots and committed identity before dispatch, and restores argv
on every exit. No retries or model fallback. Stub mode uses the existing fresh
synthetic pair transport plus the four-case stub policy harness; it explicitly
does not produce or claim native23+10records. No model inputs are accepted in stub.

Standalone wrapper has32additive allowlisted files over the immutable bootstrap
and source archive. Existing25native-CPU files remain byte-identical. The GPU
worker materializes guard weights from the existing private frozen Dataset and
reads the pinned Qwen7B Model mount. Local preflight hashes the existing archives
but materializes source only, never guard weights. Archive/expanded/PAX rehearsals
run8tools,21Dummy/resume/missing-only20retained checkpoints, six native tqdm-policy
workers per layout, exact dispatcher stub and authenticated publisher metadata.
Prior accepted native-library compatibility receipt is required by hash.

## Predeclared launch identity and measurements

- Kernel: `huylmhuhu/react-vn-context-policy-v1`, new private/offline version1.
- Dataset: `huylmhuhu/react-vn-guard15-probe-data-v1`, private version1.
- Agent mount: `qwen-lm/qwen2.5/transformers/7b-instruct/1`.
- Image: existing pinned digest37c64f7d; Torch2.10.0+cu128/Transformers5.5.0;
  acceleratorNvidiaTeslaT4, no TPU, Internet or model download.
- One fresh pair; agent then guard with both resident; two native generations
  and two separately timed final-token forwards. Input4096 each; output512/128;
  inspect cache4607/4223 before final forward and4608/4224 after it.
- Keep cold1200/120s, request180/120s, allocator caps12/7GiB agent and5GiB guard,
  original finally-cleanup and six1s recovery samples/last-three±256MiB.
- Kernel wall ceiling3600s covers bootstrap/byte authentication as well as work;
  it does not extend either worker request deadline. Timeout/OOM remains a result.
- Time tokenizer, aggregate generation including prefill, final forward, backend
  and host calls separately. Do not infer decode-only speed or compare different
  role workloads as a model ranking. No generated text/token arrays retained.

Before push: fullQA, clean exact preflight, source/receipts on GitHub, current
account/private mounts/version/quota confirmed. Only one submission; preserve
logs/partials before any failure decision. Model quality/Dev tuning, runtime
integration, A4 scope, general final entitlements and Phase5 freeze remain open.
