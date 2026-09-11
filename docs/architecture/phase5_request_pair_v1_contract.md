# Ordinary-request pair composition v1

Scope: prepare a fresh pair for the already approved ordinary attention adapter.
No frozen runtime, loader, attention adapter or supervisor is modified.

`request_pair(agent_factory, guard_factory, config, attention)` builds lazily:
ModelPair's exact ReadyFactory surrounds ThreadProgressFactory, which surrounds
EfficientRequestFactory, which calls the original native factory. Thus progress
is configured before native loading, and READY bypasses request instrumentation.
Both role identities must match the pinned native identities; a fresh attention
root is required. Known prewrapped readiness/progress/attention factories are
rejected rather than recursively unwrapped. The exact native-type check remains
inside EfficientRequestFactory at worker startup. No private factory mutation.

This pair starts BOTH roles: for diagnostic composition / future A2–A6 only.
It is not an A0/A1 task owner and is not wired into the ReAct runtime. Input and
native-metric paths remain owned by native factories/caller; they must be outside
the attention root. This builder does not authenticate arbitrary factory closures.

The standalone CPU rehearsal deliberately bypasses native constructors and
replaces native generation/library lookup with clearly synthetic shape objects
INSIDE each spawned child only. It uses real ModelPair transport, native pinned
tqdm progress and the unmodified ordinary attention adapter/factory/auditor.
No model weights, Torch/Transformers import, GPU, model output or Test payload.
Synthetic timing/token rows must never be reported as measured model performance.

Predeclared cases: success A/B/A requests in each role; reversed wrapper order
as a startup-failure control; generation failure in either role after READY.
Require READY consumes zero request directories, one shape factory load per
started role, actual distinct sibling PIDs, contiguous warm requests, failed-pair
retry refusal without a new attempt and all handles reaped. Preserve closed
snapshot and partial error/restoration records. Do not call forced cleanup a
graceful shutdown or infer global IPC/VRAM cleanup. Repeated successful synthetic
outputs do not certify native numerical statelessness.

Remaining: native repeated-request GPU entry/packaging/preflight, publisher-policy
and memory/placement/source authentication, supervisor-bound independent audit,
agent-only task ownership and runtime A0–A6 differential/lifecycle checks.
