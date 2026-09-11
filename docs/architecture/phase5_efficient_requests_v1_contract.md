# Request-local efficient attention v1 — CPU component

Status: experimental adapter; not integrated into the ReAct runtime or validated
with native multi-request GPU inference. Continues the approved attention work
after [full-context stress](../evaluation/phase5_efficient_stress_gpu_v1_report.md).
All old sources/receipts remain immutable. No benchmark or Test access.

## Interface and boundaries

`EfficientRequestFactory(native_factory, role, output)` requires the exact frozen
AgentHFBackendV2 / GuardHFBackend and authenticated identities; guard config
remains unchanged. Factory construction is lazy. The resulting LLMBackend
delegates the original messages and GenerationConfig unchanged to that loader's
generate method; it neither forces length nor adds a last-token forward.
Agent remains greedy512/seed42; guard greedy128/seed42. No new model loads,
quantization, caps, placement, prompt or publisher-generation modifications.

Successful requests may repeat in one dedicated task-owned worker. Each call
gets its own geometry state and evidence directory `request_000001`, etc.
Any admitted request failure or interruption permanently retires the adapter;
the supervisor still owns process termination/reaping. Foreign PID/concurrent
entry is refused before touching the active request. No automatic retries.
This does not alone enforce one-task ownership: the later runtime must create
and close the worker per task, never reuse it across tasks.

Within each request, require pinned native library/source and unmodified HF/Torch
bindings; disable native GQA through HF's original repeat_kv branch and force
EFFICIENT_ATTENTION. Delegate to the original builtin once per call, passing
the mask object, dropout, scale and causal flag unchanged. Restore bindings and
backend-selection flags in finally; release the scope lock even on evidence
write failures. Dedicated worker only: these library bindings are process-global,
not safe to install in an arbitrary shared/threaded application process.

No profiler, warmup, extra generation or full-boundary forward is added. Every
observed call checks efficient-only flags, helper ordering, head_dim128/FP16,
28 query heads agent/12 guard, repeated K/V heads and frozen per-layer placement.
First forward: 1–4096 input tokens with equal Q/K lengths; subsequent forwards:
one query with K growing by exactly one. Every forward must finish all28layers.
Maximum forward groups512/128, matching ordinary cached native generation.
Explicit masks, if present, must be full `[1,1,query,key]`, bool/FP16 and on the
query device. Unsupported shape/mask fails; no math fallback is selected.

Three stage JSON records per completed request: entered, restored, completed.
Errors after entering preserve error/restored stages when storage permits;
failures before native admission may have no stage records. Records contain
PID/model/request index, library hash, flags and integer geometry/counts only.
They contain no prompt, output text, token/tensor values or hidden reasoning.
Storage failure and forced termination may leave partial records, never success.

Forward counts and key geometry are not independently measured emitted token
counts or inspected full KV-cache objects. Receipts explicitly set
`output_tokens_verified=false` and `full_boundary_cache_verified=false`.
Efficient-only guards are not individually profiled dispatch evidence; the
earlier tensor/model stress operator traces remain separate historical evidence.

## CPU verification and remaining acceptance

Tests cover short/long variable sequences for both roles, mask/no-mask, lower
and upper input/output bounds, repeated A/B/A requests with new geometry,
ordered heads/devices/keys, identity/config rejection, nested/foreign entry,
exception/storage-error restoration, retirement and exact factory admission.
Hash-authenticated Transformers5.5 SDPA source executes against fake Tensor
objects for multiple varying requests; no native numerical/statelessness claim.

Before model/runtime adoption: independent request-artifact auditing joined to
native input/output metrics, real-spawn composition with ReadyFactory outermost
and thread-only progress before loading, repeated-request native GPU evidence,
then versioned runtime differential/isolation/lifecycle checks and grouped Dev.
Do not overwrite the fixed stress backend or plug it into ordinary requests.

## Runtime integration constraints identified during inspection

- Runtime v5 owns a WarmGuardBackend internally and emits its attempts/lifecycle
  metadata. Passing ModelPair through its guard factory would spawn a nested
  supervisor instead of routing to the already resident sibling. Do not do this.
- ModelPair.start currently starts both roles unconditionally; A0/A1 v5 forbids
  guard instantiation. A future explicit agent-only task owner/role selection is
  required; do not load a guard for A0/A1 merely to reuse the existing start path.
- Cold readiness attempts must not be attributed to a guard classification or
  normal agent generation. Record load/start once, per-request warm time and
  task total including cleanup separately. Never drop cold time from reporting.
- Cache liveness/invalid guard output must retire the relevant pair and clear
  guard cache; all terminal/exception paths must attempt sibling cleanup. Keep
  failure visibility if cleanup is incomplete rather than claiming success.
- Preserve Broker, Pre/Post/Final decisions and existing replay context parity,
  including the narrowly defined run-local source-ID renaming for A6 envelopes.
  This adapter does not implement any of those policy/runtime changes itself.
