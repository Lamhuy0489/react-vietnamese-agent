# Next gate: versioned efficient-attention model stress

Status 2026-09-11: design only, not implemented or submitted. Owner approval is
recorded in the [decision log](../project/decision_log.md); the conditional
[native tensor feasibility gate](../evaluation/phase5_sdpa_tensor_gpu_v1_report.md)
has now passed. No further context/model/cap change is authorized.

## Immutable boundaries

Keep all frozen context/policy/tensor source and old outputs byte-for-byte.
Add versioned entry, integration, auditor, wrapper and builder files. Reuse
authenticated native loaders without relaxing their exact-type checks.
Retain Qwen2.5-7B-Instruct agent and Qwen2.5-1.5B-Instruct guard revisions,
FP16, 20/8-layer placement, 12/7 GiB agent and 5 GiB guard caps, existing request
and worker deadlines. No quantization, context reduction or publisher decoding
change. The tensor-only 2 GiB cap does not apply to model workers.

Stress remains 4096 synthetic input tokens, 512/128 forced output tokens, then
one last-token forward for complete 4608/4224 KV inspection. Preserve all-layer
cache shapes/dtypes/device/bytes, actual resolved policy hooks, timings and
recovery evidence. No benchmark/Test payloads or model-generated text in memory.

## Composition to validate before implementation freeze

Keep ReadyFactory outermost so readiness never consumes the single-use stress
backend. Progress-lock prevention must still wrap native loader construction.
Proposed chain: ReadyFactory -> ThreadProgressFactory -> new efficient-stress
factory -> existing PolicyStressFactory -> existing ContextStressFactory ->
unchanged native loader. Validate both roles before mutating host factories.

The new backend should wrap the existing policy backend, not replace its config
or generation implementation. Explore a single-owner, single-use worker-local
scope around its one generate call (which also contains the final forward):

- Authenticate the installed pinned HF SDPA source and original helper identity.
- Temporarily select HF's existing `repeat_kv` branch by disabling native GQA
  eligibility only within this dedicated worker, combined with forced
  EFFICIENT_ATTENTION. No silent fallback or model config mutation.
- Restore the helper and backend-selection state in finally on success and
  exceptions; refuse nested, foreign-PID or concurrent use. This is process-wide
  state, so do not install it in a shared/threaded production backend.
- Prove this composition matches the tested tensor candidate, including scaling,
  masks, causal flags, head ratios and prefill/decode behavior. The tensor probe
  only covered no-mask inputs; native model mask behavior needs explicit checks.
- Record separate entry/error/restoration/completion sidecars, actual invocation
  counts and treatment identity without Q/K/V values or hidden reasoning.
  Decide before launch how actual backend dispatch is evidenced without adding
  unbounded per-token profiling or contaminating latency claims.

This composition is a candidate implementation route, not already-validated
code. If native helper binding, masks or backend semantics do not match, fail
before GPU and document a bounded alternative rather than patching frozen files.

## Acceptance and launch sequence

1. CPU fake differential and mutation tests for scaling/masks/GQA/repeat,
   ownership, single use, restoration on errors and no silent fallback. A real
   spawn rehearsal must exercise ReadyFactory ordering and not load weights.
2. Static pinned-wheel checks of the selected native composition; independent
   auditor binds treatment sidecars to policy/stress stages and source identity.
3. Full setup/Ruff/mypy/pytest/knowledge QA. Clean committed source and exact
   archive plus expanded/PAX preflight must include the new actual dispatcher,
   all eight tools, Dummy/resume and native progress/factory checks.
4. Push source/QA to GitHub, verify private Dataset/model pins and quota, then
   one newly named private/offline GPU version. Never resubmit context v1/v2 or
   tensor v1 to obtain better outcomes. No account cycling.
5. Preserve all failure/success outputs. Audit independently twice. Only native
   full-boundary success permits subsequent runtime integration and grouped Dev
   differential evidence; tensor or model-stress success alone does not close
   Phase 5 or authorize benchmark adoption.

Current source checkout has unrelated user changes in plan/phase6–9. Preserve
them; do not commit/restore them to obtain a clean package. A separate clean
worktree was used for the tensor preflight and may be used for the next source
commit after checking that all packaged files are tracked and immutable.
