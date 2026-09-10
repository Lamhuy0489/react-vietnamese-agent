# Context/policy stress v2: readiness composition correction

The [v1 workload contract](phase5_context_policy_gpu_v1_contract.md) remains in
force except for the versioned entry, factory composition and preflight below.
This is an implementation correction, not a change to research scope, model
selection, generation settings, deadlines, placement, inputs or acceptance.

## Preserved failure and causal control

Kernel `huylmhuhu/react-vn-context-policy-v1`, version 1, failed during agent
startup. Preserve all 59 raw files and two remote files; the guard never started.
The agent loader returned, but the stress factory received a `ReadyBackend`
instead of the exact native backend it requires. The sanitized worker result
was `BACKEND_FAILURE`; no stress generation or readiness acknowledgement was
completed. Six sampled VRAM residuals were zero; one worker was terminated,
not gracefully shut down. This is not a successful context-stress experiment.

The submitted v1 topology was:
`ThreadProgressFactory(PolicyStressFactory(ReadyFactory(native_factory)))`.
The new topology is:
`ReadyFactory(ThreadProgressFactory(PolicyStressFactory(native_factory)))`.
The native exact-type check is unchanged. Host readiness is outside the
single-use stress backend, so its acknowledgement does not consume stress.
Both roles are validated before either factory is replaced. Frozen v1 source
and artifacts are never edited in place.

## Added preflight gate

`check_phase5_policy_factory.py` runs the original failure control and corrected
pair through actual daemon-spawn workers with pinned native tqdm. It deliberately
bypasses HF constructors, creating native-shaped placeholders only. Expected
statuses are `[BACKEND_FAILURE]` and `[OK, OK]`; all handles must be reaped and no
stress entry/completion may be recorded. No weights, model calls or GPU claims.
This closes the v1 rehearsal gap: the previous stub dispatcher did not exercise
the HF entry's factory composition. Native model generation still needs Kaggle.

Both archive and expanded/PAX isolated rehearsals must run this control in
addition to all v1 tools/Dummy/resume/progress/policy/publisher checks. The new
36-file overlay preserves all 32 v1 files and adds only the corrected factory,
fixed HF entry, v3 dispatcher and factory checker. The v2 outer auditor requires
both factory-control receipts and reuses the unchanged native/policy auditors.

## New launch identity

- Kernel `huylmhuhu/react-vn-context-policy-v2`, private/offline version 1.
- Wrapper `context_policy_kernel_v2.py`; bootstrap `context_policy_bootstrap_v2`.
- Preflight `context_policy_gpu_exact_preflight_v2`.
- Completion marker `CONTEXT_POLICY_GPU_V2_COMPLETE`.
- Same pinned Dataset, model mount, image and T4; same 3600-second ceiling.
- One submission after source commit, exact preflight, full QA, GitHub push and
  current access/quota checks. Failure is evidence, not permission for blind retry.

Phase 5 remains open until its remaining runtime, security-scope, entitlement,
grouped Dev decision and freeze gates pass. No Phase 6/7 or held-out Test access.
