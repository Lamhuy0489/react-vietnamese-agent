# Native generation policy observation v1

This is a versioned instrumentation layer around the frozen context-stress
backend, not a change to benchmark decoding or publisher defaults. The prior
[finding](../../experiments/manifests/phase5_context_stress_generation_defaults_finding01.json)
remains valid: a fresh submitted config does not describe the resolved policy.

## Composition and boundaries

`PolicyStressFactory` composes the authenticated `ContextStressFactory` and a
single-use `PolicyStressBackend`. The new HF entry wraps that factory in the
existing `ThreadProgressFactory`. Model identities, placement, generation request,
timeouts and the frozen 23-file context probe are unchanged. Policy receipts are
written to a separate, non-nested directory; existing paths are rejected before
model loading. The CLI is not yet packaged or GPU-validated.

Within one owning worker, temporary instance-level hooks observe calls to the
original bound `_prepare_generation_config` and `_prepare_generated_length`.
Each hook delegates exactly once and returns the original result. There is no
second resolver invocation, sampling, policy neutralization or model generation.
Existing instance hooks are rejected, and installed hooks are removed in finally.
Failure consumes the backend; no retry. The inner backend retains its existing
single-use/context/cache/error handling.

## Evidence

Each role emits five complete-run receipts with PID/model identity:

1. `entered`: loaded publisher config and native global defaults.
2. `resolved`: submitted config, actual resolved config and model-kwargs names.
3. `length`: config before/after the actual native length preparation, input4096.
4. `restored`: restoration status and exact hook call counts.
5. `completed`: configuration hashes, one generation, no policy change.

Failure retains partials plus an error-class-only receipt and restoration record
when instrumentation has begun. Errors before hook installation may leave only
an empty policy directory. Never infer model execution from receipt presence.

Only69 known serialized fields are copied. Native private special-token tensors
are ignored without copying, traversing or serializing them. Unexpected fields,
non-JSON objects, nonfinite numbers and extra generation overrides fail closed.
No input/output token values, hidden states, model text or tensor objects enter
policy files. `transformers_version` follows native serialization semantics.

The independent auditor checks exact five-file inventory, identities, precedence
submitted-non-None > publisher-non-None > pinned global defaults, length4608/4224,
hashes, one call per hook and restoration. Caller must separately authenticate
publisher metadata and the submitted receipt. Auditor success is not remote
source authentication or phase acceptance. It describes these observed stages,
not every later modification inside generation, logit processing or cache setup.

## Verification and release gates

CPU fake-model tests cover both roles, preserve publisher repetition1.1 while
explicit do_sample=False wins, compare token/cache summaries with uninstrumented
controls, skip private tensor copies, reject corrupt artifacts and restore after
exceptions/interruption. Static wheel checks authenticate Transformers5.5.0 and
compare native global defaults/precedence to the independent auditor.

Neither fake execution nor AST checks prove the hooks work in the installed
native runtime. Before GPU release: exact packaged native-library compatibility
rehearsal, authenticated publisher/config mapping in the outer release auditor,
source push, standalone archive/expanded/PAX 8tools/21Dummy/resume and separate
native thread-progress checks, then current private inputs/quota and one distinct
GPU run identity. Preserve failures, do not silently alter decoding/deadlines.
