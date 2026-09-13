# Decision Log

## 2026-09-12 — Classify ordinary GPU v1 accelerator mismatch

- Submit exactly one new private ordinary package under owner `huylmhuhu` after
  source push and exact offline preflight. Kaggle accepted the kernel, but the
  invocation used CLI alias `--accelerator gpu`; remote metadata returned generic
  `machine_shape=Gpu`, and runtime observed one GPU. The pinned pair requires two
  T4 devices, so `PairCUDAObserver` failed before native model initialization.
- Pull source hash matches the preflight wrapper exactly. Bootstrap, tokenizer
  sidecars, publisher metadata and 21 Dummy checkpoints were downloaded; no
  model generation, tensor execution, benchmark/Test payload, private GT or
  quality result exists. Preserve this as infrastructure error; do not retry
  the same kernel/version or reinterpret it as semantic failure.
- A new kernel identity may request explicit `NvidiaTeslaT4` (official Kaggle
  documentation lists T4 x2). Verify returned metadata and `device_count==2`
  before loading models; if the same one-GPU infrastructure failure repeats,
  stop submissions and request platform access. [Receipt](../experiments/manifests/phase5_ordinary_pair_gpu_v1_error01.json).

## 2026-09-12 — Prepare exact ordinary A/B/A Kaggle package

- Add a new private ordinary kernel wrapper and offline builder. Extend the
  frozen efficient-stress bundle with the ordinary runner, policy/attention/
  tokenizer auditors and metadata collector; selected source bytes must match
  the resolved Git commit. Validate archive and generated-expanded source
  layouts in isolated Python environments with the pinned wheel set.
- Run eight-tool/recovery, 21 public Dev Dummy tasks, missing-only resume,
  synthetic six-call A/B/A and joined audits before any native request. Runtime
  order is collector → HF pair → joined audit; errors stop with no semantic
  retries. Model weights are never materialized locally and Test/private GT are
  excluded.
- Reserve a new private kernel identity `huylmhuhu/react-vn-ordinary-pair-v1`.
  Current owner quota/Dataset readiness are checked separately; default
  `lamhuy8904` lacks the private Dataset, so no upload occurs under that account.
  Package evidence is not native/GPU or Phase 5 acceptance. [Contract](../architecture/phase5_ordinary_package_v1_contract.md).

## 2026-09-12 — Authenticate ordinary tokenizer metadata without changing runtime

- Add a versioned metadata-only collector and audit layer. Authenticate exact
  public tokenizer config size/SHA256/Git blob against existing model pins;
  derive special-token IDs, bind pad expectations to ordinary policy evidence
  and config bytes to admitted model files. No caller pad override in new CLI.
- Preserve frozen native/supervisor auditors, model loaders, decoding and raw
  results. Public config is stored as a UTF-8 string envelope to preserve its
  missing final newline; its chat template is not executed or injected.
- Metadata authentication is not native tokenizer execution or model/source/
  remote authentication. CPU standalone evidence reuses explicitly synthetic
  records; no new model inference, Test access or research-scope change.
  [Contract](../architecture/phase5_tokenizer_metadata_v1_contract.md).

## 2026-09-12 — Audit the full ordinary request evidence chain

- New read-only supervisor and joined-native auditors require expected commit,
  exact six-request coverage, immutable snapshot prefixes and PID/attempt hashes.
  Bind existing policy/attention/native metrics to supervisor records; check
  publisher bytes, admitted model-file identities, placement and allocator bounds.
- Preserve forced/graceful distinctions and descriptive A-repeat results. Report
  native/worker/host timing separately; no semantic retry or performance claim
  from synthetic CPU fixtures. Tokenizer and remote source/package authentication
  remain release gates. See [contract](../architecture/phase5_ordinary_audit_v1_contract.md).
- Public guard snapshot hashes are added as a deterministic test fixture. No
  model weights, benchmark payloads, Test/private GT or research-scope change.

## 2026-09-12 — Add ordinary repeated-request pair entry point

- Add a versioned A/B/A runner that records submitted/returned calls, timing,
  residency and six recovery samples while preserving the frozen pair,
  policy and attention factories. The runner stops on errors, propagates
  interrupts after cleanup and never performs semantic retries or filters
  repeated outputs.
- CPU controls use real daemon-spawn transport with explicit synthetic
  responses/memory; HF mode is opt-in and requires the pinned model/snapshot,
  two-device environment and separate output roots before native initialization.
  This is plumbing evidence only; it does not change decoding, benchmark scope,
  Test sealing, or Phase 5 acceptance.
- CPU release correction: initial standalone runs 01/02 received an incorrect
  asserted full Git commit. Preserve and hash their outputs as excluded;
  select fresh runs 03/04 with identity obtained directly from Git and verified
  against source bytes. No model inference or semantic retry was involved.

## 2026-09-12 — Join request policy and attention in real spawned workers

- Add a lazy versioned pair builder with Ready outside progress outside policy
  outside attention/native factory. Validate both roles and roots before
  transport allocation; keep prior sources immutable.
  [Contract](../architecture/phase5_request_policy_pair_v1_contract.md).
- Reuse the prior CPU control runner through a scoped host-only builder
  substitution restored in finally. Explicit synthetic factories exercise
  policy/attention together in real daemon spawn with pinned native tqdm;
  models/config/tensors/timing rows remain synthetic, not model performance.
- Readiness/index coverage, repeated requests, joined artifact audit, failure
  partials/restoration/sibling cleanup/no-retry are checked. Native entry,
  authentication/preflight, agent-only owner and runtime phase gates remain.
  No new native/GPU/held-out inference or research scope change.

## 2026-09-12 — Observe ordinary policy separately from forced-length stress

- Add request-local policy observer/factory and an independent auditor joined
  to native-metric/attention receipts, without changing frozen source or decoding.
  [Contract](../architecture/phase5_request_policy_v1_contract.md).
- Ordinary native requests do not set min_new_tokens/output_logits; preserve
  None and publisher/default inheritance instead of importing stress settings.
  Require publisher stability, ordered observations and per-request restoration;
  retire on admitted failure, no semantic retries or extra forward.
- CPU fake differential and pinned method-source execution are bounded evidence,
  not native model/library parity or GPU adoption. Policy-pair composition,
  publisher/tokenizer/source/native-load authentication and phase gates remain.
  No Test/private-GT access or new inference/submission.

## 2026-09-12 — Compose ordinary requests before native runtime adoption

- New lazy pair builder preserves ReadyFactory outside progress and attention,
  leaving frozen supervisor/loader/adapter/runtime sources unchanged.
  [Contract](../architecture/phase5_request_pair_v1_contract.md).
- Real daemon-spawn CPU controls use native pinned tqdm but explicitly synthetic
  model-shaped objects and tensors. A/B/A success, reversed-order startup failure,
  injected failures on either role, retry refusal and sibling cleanup are tested.
  No native numerical/performance/GPU cleanup or benchmark adoption claim.
- Pair still starts both roles, so A0/A1 require a separate agent-only owner;
  native repeated-request policy/source/memory and package checks remain open.
  No new model/held-out inference or change to research scope/caps/decoding.

## 2026-09-11 — Audit ordinary request evidence without changing frozen workers

- Continue Phase 5 with a separate read-only artifact auditor and CLI. Join
  request geometry to original native input/output and timing metrics; reject
  missing, duplicated, failed or reordered calls instead of selecting survivors.
  [Contract](../architecture/phase5_efficient_requests_audit_v1_contract.md).
- Preserve source039af85 and all measured worker sources. Caller-supplied PID
  is not supervisor authentication; native metric consistency is not full KV,
  numerical statelessness, resolved policy or benchmark/runtime acceptance.
- No new inference, model load, GPU submission or Test/private-GT access.
  Remaining work is real-spawn composition, native repeated-request proof and
  task-owned runtime integration; research scope/decoding/caps are unchanged.

## 2026-09-11 — Separate ordinary requests from the fixed stress diagnostic

- Continue the approved attention optimization through a new request-local
  adapter; preserve frozen stress/native/runtime code. No forced length or
  extra forward; unchanged native config, caps and model identity.
  [Contract](../architecture/phase5_efficient_requests_v1_contract.md).
- Variable geometry and repeated success within a dedicated task worker are
  CPU-tested; any admitted error retires the adapter. No native repeated-request
  or benchmark adoption claim yet. No new GPU submission or Test access.
- Runtime inspection identifies mandatory agent-only ownership for A0/A1 and
  direct sibling routing for A2–A6. Do not nest ModelPair inside v5 guard factory
  or misattribute readiness/cold load as normal model generation.

## 2026-09-11 — Implement the approved efficient model stress gate

- Owner requested immediate continuation after tensor feasibility passed.
  [Contract](../architecture/phase5_efficient_stress_v1_contract.md): new scoped
  HF repeat/forced-efficient treatment with per-call guards, two actual dispatch
  samples per role and independent sidecars. Original sources remain immutable.
- Preserve models, precision, context, placement/caps, deadlines and publisher
  decoding. Timing includes scoped checks/two profiled calls; no speedup claim.
- This is a distinct diagnostic identity, not a retry or benchmark adoption.
  Full QA and exact package checks precede GPU; Phase 5 and Test remain closed
  to acceptance/final experiments respectively until their own gates pass.

## 2026-09-11 — Owner approved bounded attention-memory investigation

- User confirmed "ok làm cho tôi nhé" in response to the proposed VRAM-saving
  attention experiment with unchanged models and4096-token workload, then asked
  to continue. The earlier pending proposal below is now approved within those
  bounds, not permission to lower context, quantize or replace a model.
- First implement [no-weights SDPA tensor protocol](../architecture/phase5_sdpa_tensor_v1_contract.md):
  pinned libraries/hardware,10fresh processes, four predeclared numerical
  comparisons and long4096/boundary shapes. Tensor-only2GiB cap does not change
  any model allocator cap. No model inference at this gate.
- Conditional next step: only if native evidence supports the efficient path,
  prepare a versioned model attention integration with the same revisions,
  precision, placement/caps, deadlines, publisher decoding and full context.
  Preserve old OOMs; do not silently resume or use Test/model outputs for tuning.
- No Phase5 closure or benchmark adoption is inferred from component success.

## 2026-09-11 — Proposed attention-memory deviation; awaiting owner approval

- Context/policy v1 failed factory admission; corrected v2 reached READY for
  both native models, then agent stress raised OutOfMemoryError. Preserve both
  runs separately; no same-identity retry, shortened context or success claim.
  [Evidence and source-level hypothesis](../evaluation/phase5_context_policy_v2_oom_review.md).
- Proposed: first diagnose pinned SDPA eligibility/memory with synthetic tensors
  and no model weights. If the GQA/math-fallback hypothesis is confirmed, test an
  opt-in explicit-KV-repeat/memory-efficient attention implementation. Retain
  model revisions, FP16, placement/caps, request deadlines, full 4096 input and
  512/128 output workload, publisher decoding, task splits and source history.
- This is not yet approved or implemented. Different kernels can change floating
  point results, requiring predeclared short-shape parity tolerances, distinct
  run identity, full package QA, native stress validation and later runtime
  differential evidence. No benchmark/runtime adoption from a tensor probe.
- Research-evidence does not authorize a frozen architecture change. Wait for
  explicit owner confirmation before this experimental computation-path change;
  no additional GPU submission has been made after v2 ERROR.

## 2026-09-10 — Observe native policy stages without changing decoding

- [Generation policy observation v1](../architecture/phase5_generation_policy_v1_contract.md)
  composes the frozen context backend through a new entry/factory, with separate
  policy artifacts. Observe actual resolver and length-preparation calls once,
  returning original results and restoring methods in finally. Do not neutralize
  publisher defaults or change benchmark decoding based on the prior finding.
- CPU fake differential/mutation tests and pinned-source assertions do not close
  native compatibility or GPU gates. Authenticate publisher metadata independently
  in the future outer release auditor; source/policy receipts alone are not proof.
- No frozen source/raw overwrite, model inference, Test access or scope change.

## 2026-09-10 — Submitted generation config is not the resolved policy

- Independent context-stress artifact auditing now covers 23-file consistency,
  lifecycle, all-layer KV arithmetic, allocator/timing containment and recovery.
  Its success does not authenticate remote source or certify the generation policy.
- Hash-verified Transformers5.5.0 source fills None fields from model defaults
  before global defaults; a newly constructed GenerationConfig is not isolated
  from publisher repetition settings. Preserve the [finding](../../experiments/manifests/phase5_context_stress_generation_defaults_finding01.json)
  and frozen backend. No inference has been submitted for this diagnostic.
- Add versioned publisher/resolved-policy evidence and matching checks before
  GPU wrapper/preflight. Do not silently neutralize publisher values, tune using
  outputs or relabel CPU/static checks as GPU acceptance. No research-scope change.

## 2026-09-10 — Isolated full-boundary context diagnostic implementation

- [Context stress v1](../architecture/phase5_context_stress_v1_contract.md)
  implements the existing design without changing benchmark decoding or frozen
  loaders/transport. Single-use synthetic4096input, forced512/128new tokens,
  followed by one separately timed last-token forward. Every KV layer's shape,
  dtype, device and byte count is checked, with no tensor values/text persisted.
- Parent clocks remain end-to-end; child generation time includes prefill,
  which is not claimed separately. Per-process allocator peaks and global free
  endpoints are distinct. Failed native attempt counts are unknown/null, not
  inferred from how many responses reached the parent.
- Two synthetic spawn rehearsals and fake tests are CPU evidence only. A new
  read-only artifact auditor, exact standalone preflight and launch contract
  must precede any context GPU submission. No Test or research-scope changes.

## 2026-09-10 — Versioned HF progress prevention validation

- [Pair progress v1](../architecture/phase5_pair_progress_v1_contract.md) keeps
  the 15-file IPC overlay, fixed model/image/transport and all prior results.
  Two additional files configure the pinned thread lock before native loading;
  distinct source/protocol and seven identity/policy receipts bind treatment.
- Exact preflight adds the hash-pinned 78 kB native tqdm wheel to isolated CPU
  environments only. GPU uses the pinned image's package, checked at runtime;
  no frozen Dataset version or local model acquisition changes.
- Tracked sources must be clean/committed; unrelated untracked user reports may
  remain outside the allowlisted payload. Prevention miss is retained separately
  from integrity validity. No automatic retry, Test access or phase closure.

## 2026-09-10 — Worker-local progress lock, not warning suppression

- IPC diagnostic trace attributes three unmatched registrations to tqdm's
  default multiprocessing RLock in busy workers. All six process exits were
  forced, including three idle siblings whose lock unregister had completed.
- Separate [worker progress contract](../architecture/phase5_worker_progress_v1_contract.md)
  uses a thread reentrant lock before progress/model initialization in daemon
  spawn workers only. Refuses existing locks/dependency drift; no manual
  unlink/unregister, deadline change, model/prompt change or source rewrite.
- Native CPU controls show TQDM_DISABLE alone still creates a semaphore; the
  thread-lock path does not. GPU/HF validation remains a distinct next gate.
  No research-scope/model-choice/Test/Phase6 transition; old evidence preserved.

## 2026-09-09 — Separate IPC-origin diagnostic, no cleanup reinterpretation

- Prior paired cancellation GPU logs warned about3semaphores; worker reap/VRAM
  recovery remains valid within its frozen scope, not global IPC certification.
- [New diagnostic protocol](../architecture/phase5_pair_ipc_v1_contract.md) adds
  observational tracker hooks and a declared post-suite owner GC checkpoint,
  preserving model inputs, deadlines, caps and frozen transport/factory code.
  It creates a new run identity, not a semantic retry or rewrite of old results.
- Stacks/hashes/PIDs only; no manual unlink/unregister, warning suppression or
  threshold changes. Instrumented latency is not pooled with original timings.
  No policy, model choice, Test access or approved research scope change.

## 2026-09-09 — Combined cancellation precedes context stress

- [Separate technical protocol](../architecture/phase5_pair_cancellation_v1_contract.md)
  adds three fresh-pair timeout trials after the small-context GPU milestone;
  no changes to frozen supervisors, adapters or prior results. CPU implementation
  is not GPU recovery evidence. GPU busy loops retain weights but do not invoke
  native autoregressive generation; report this boundary explicitly.
- Maximum-context/forced-length stress needs a separate versioned protocol;
  early EOS cannot certify a full4096+512-token allocation. No benchmark decoding,
  guard prompt or Test-based tuning is changed. No Phase5 acceptance implied.

## 2026-09-09 — Pair GPU entry point and native Transformers5.5 buffer adapter

- Exact pinned Dataset wheel inspection found native original_inv_freq is a
  registered buffer; frozen agent v1 would reject it before any generation.
  New agent v2 admits exactly the two known64-element rotary buffers and pins
  Transformers5.5.0. Original v1 and all earlier hashes remain unchanged.
- [Predeclared GPU contract](../architecture/phase5_pair_gpu_v1_contract.md) keeps
  the one-pair/two-small-call technical scope, original caps/deadlines and guard
  prompt. New offline HF entry point and hash-bound overlay are separate from
  policy/runtime integration. No GPU result or held-out output drove this fix.

## 2026-09-09 — Model pair supervisor, separate from frozen v5 runtime

- [Contract](../architecture/phase5_model_pair_v1_contract.md) composes the existing
  warm transport into two task-owned sibling workers, agent readiness before
  guard loading. No model.generate for readiness; fail either side, close both.
- Cold/warm technical deadlines are explicit and hash-bound; switching them
  after readiness does not change model identity or alter frozen transport.
  Prior forced/graceful cleanup outcomes remain unchanged. This component is
  not wired into security policies and does not select a guard or close Phase5.
- CPU spawn tests and a durable synthetic residency/small-context rehearsal
  precede an HF entry point and exact GPU bundle. Fake memory is never selected
  as proof of real VRAM recovery; Test access remains hash-only.

## 2026-09-09 — Versioned runtime-only agent admission, not a repaired full scan

- Owner authorized continuing the budgeted agent loader after the Kaggle CPU
  diagnostic. The old scanner/receipt remains a full-inventory failure; no rerun
  or publisher pin change. A new [contract](../architecture/phase5_agent_hf_v1_contract.md)
  admits matching runtime files and only the exact previously observed README
  size/SHA256/Git-blob difference. Documentation is not a runtime input.
- Live hashes, index/header shapes and post-load reauthentication are mandatory;
  a saved success receipt alone cannot authorize a load. Dedicated agent process,
  12/7GiB allocator caps and fixed20/8layer placement preserve the prior plan.
- Scope impact: engineering admission only. No model selection, semantic retry,
  held-out access, score change or Phase5 closure. GPU coexistence and grouped Dev
  remain future gates, not proven by synthetic CPU fakes.

## 2026-09-08 — Task-local warm guard and runtime v5

- [Contract](../architecture/phase5_warm_guard_contract.md) predeclares one model
  load per task, one in-flight request, bounded shared-memory JSON, inclusive
  cold/warm request deadlines, explicit close and terminate/kill/reap fallback.
  No cross-task worker/cache reuse, automatic restart or semantic retries.
- V5 retains the v4 policy loop but owns a warm worker in try/finally. A0/A1
  create no worker. Guard prompt/parser/generation and source labels stay fixed.
  Invalid guard JSON retires the new worker and clears cache; this additional
  fail-closed lifecycle behavior is versioned, not backported into frozen v4.
- Cache serving checks worker liveness; concurrent classifications are rejected.
  Cleanup failure retains the handle and raises, never reports successful reap.
  Real backend statelessness between generate calls still requires validation.
- Cold/warm A6 context comparison resolves only host-generated Post source IDs
  into source ID/type/hash/step/labels. Initial exact-byte comparison differed on
  those run-local IDs while outcomes/legacy events matched. Preserve raw contexts
  and do not normalize arbitrary model/source content to hide mismatches.
- Synthetic-only QA: 22 paired runtime conditions and nine worker conditions;
  no model selection, GPU/Kaggle run, benchmark Dev tuning or Test payload access.
  Preflight01 passes 891 tests (46 new), setup/Ruff/mypy 194 files/knowledge.
  44 Replay, 140 mock Broker calls, 240 fake runtime guard classifications;
  138 source/370 raw hashes and 1,038 prior source entries checked. Paired worker
  starts 53 cold / 18 warm are synthetic process counts, not model/GPU speedup.
  Selected source `2300751` reproduces the stable preflight summary and passes
  all 891 tests in 225.80 seconds; 138 source/370 raw hashes and 53/18 starts
  rechecked. [Receipt](../../experiments/manifests/phase5_warm_guard_v1_validation01.json).
  Phase 5 remains unaccepted.

## 2026-09-08 — Predeclare bounded A6 runtime composition

- New v4 loop composes frozen A6 components without editing selected A0–A5
  source. All levels share the new config-driven loop; old versions are evidence
  references. [Integration contract](../architecture/phase5_a6_runtime_contract.md).
- Retain full A5 session/rule/guard processing and log its coarse verdict. Only
  the coarse sensitivity pair may be discharged by an ALLOW host value gate;
  authorization, rule, suspicious/malicious/error guard vetoes stay in force.
  This is plan II/LV's artifact-aware refinement, not a standalone ablation.
- Actual model context references the declared untrusted Post view; raw source
  and observation remain immutable. Index/decisions stay host-only. A6 final
  uses fixed S0 host clearance and returns only the separately released text.
  No private-record entitlements inferred from user text or evaluator metadata.
- Synthetic QA fixture initially assumed uppercase email normalization; the
  frozen profile is case-sensitive. Correct the fixture to its supported
  zero-width normalization case, without changing matcher/expected protection
  scope. Uppercase/semantic/encoded leakage is not advertised as covered.
- No Test payload access, benchmark model run, guard-model selection or Phase 6.
  Preflight01 passes all 845 tests (76 new), setup/Ruff/mypy 190 files/knowledge.
  26 synthetic conditions + 12 prior-level parity pairs = 50 Replay, 56 mock
  Broker calls, 121 fake guard classifications. 135 source/435 raw hashes and
  903 prior source entries verified. Selected source `04ae4c8` reproduces the
  stable preflight and passes all 845 tests in 178.29 seconds; 135 source/435 raw
  hashes rechecked. [Receipt](../../experiments/manifests/phase5_a6_runtime_v1_validation01.json).
  Phase 5 remains unaccepted and no real-model security result is claimed.

## 2026-09-08 — Value-origin release evidence and bounded value gates

- Source `3b9f565` and `phase5_value_origin_v1_validation01` freeze the typed
  origin/final-release component: 696 tests, 24 synthetic cases, 130 source/101 raw
  hashes verified. Evidence handoff completed in `06086c1`; runtime A6 remains off.
- Next separate value PreGate requires raw-user action/destination anchors,
  complete index roots in the proposal ancestry, exact typed origins for all
  critical scalar leaves, S0 clearance and protected scans including JSON keys.
  Missing/unsupported origins, structure or resource coverage deny external sinks.
  Fixed read/compute tools remain value-origin fail-open; unknown tools do not.
- Predeclare small webhook key allowlist and exact scalar matching. This is
  intentionally restrictive; no substring concatenation or unknown numeric
  inference is advertised. Schema defaults are allowed without rewriting supplied
  arguments. A6 control/guard arbitration is still separate, not bypassed.
- Post primitive creates a JSON data envelope only for untrusted source results,
  preserving content/lineage/labels. It is not claimed to prevent all prompt
  injection. No raw artifact rewrites, model prompt changes or Test payload access.
- Component tests can exercise the existing Broker only after a value ALLOW;
  no real side effects or model run. Full A6 runtime/Final authorization and Dev
  validation remain pending; do not interpret component ALLOW as full A6 safety.
- Review found an omitted-observation hole: checking only indexed roots against
  exposure was insufficient. Require every observed raw user/tool source to be
  indexed as well. Regression test uses omitted S2/public duplicate data. No Test
  payloads informed this repair. Preflight01 was invalidated by this source edit;
  preserve its logs, select only the fresh preflight02 of the corrected source.
- Selected validation01 stopped before a receipt or pytest log was written; no
  validator/pytest process remained when checked. Preserve its partial directory
  without claiming acceptance. Run the full unchanged-source QA in a fresh
  validation02 directory, not a semantic retry or per-case selection.
- Source `a3743a2` clean-worktree validation02 reproduces preflight02: 769 tests
  pass in 138.14 seconds, setup/Ruff/mypy 186 files/knowledge pass. Verify all
  132 source/121 raw hashes and 771 prior source entries. Selected receipt:
  [value-gate validation02](../../experiments/manifests/phase5_value_gates_v1_validation02.json).
  No model/guard/Replay run or Test payload parsing; Phase 5 remains unaccepted.

## 2026-09-07 — Predeclare cumulative A3–A5 session enforcement

- New session policy and runtime v3 preserve selected A0–A2 implementations.
  Research contract/config matrix requires A4 to retain A3 sensitivity and A5
  to retain A1–A4; plan shorthand does not authorize standalone ablations.
- Host source sensitivity joins by max, trust by independent untrusted OR.
  A3 external clearance is S0: S1/S2 exposure blocks even unrelated public
  output and explicit user authorization. This coarse overblocking is intentional.
- A4 additionally requires action-specific raw-user destination authorization
  after any untrusted source. No general student/course-ID or processing-scope
  parser is claimed in this bounded milestone.
- A5 additionally vetoes external proposals on sticky rule alerts, guard
  SUSPICIOUS/MALICIOUS alerts or errors, including the current proposal. This is
  predeclared rather than tuned on Dev/Test; SUSPICIOUS remains TAG-only in A2–A4.
- Session snapshots are host-only at Initial/Pre/Post/Final; source/action IDs
  support auditing, not fine-grained value provenance. Empty guard sidecars now
  exist for zero-call runs. Final remains pass-through and A6 rejects explicitly.
- Preflight: 593 tests pass (147 new), setup/Ruff/mypy 179 files/knowledge pass.
  44 exact A0–A2 pairs + 30 session cases = 118 Replay. Session cases have 165
  fake guard classifications, 225 snapshots and 15 expected denials, not ASR.
  514 prior source entries intact; 127 source/780 raw hashes recorded.
  Selected source `8a4ca3d` reproduces the stable summary and all 593 tests pass;
  127 source/780 raw hashes verified in `phase5_session_v1_validation01`.
  Production guard selection/GPU efficiency,
  general A4 processing scope, A6 and grouped Dev validation remain open.

## 2026-09-07 — Add A2 bounded-process runtime without changing selected source

- New v2 loop preserves frozen A0/A1 mechanics and the v1 prompt/parser/rules;
  only A2 gets additional Pre-action/Post-source semantic classifications.
- Predeclare sticky source MALICIOUS/error veto for external sinks, current
  action MALICIOUS/error veto, and SUSPICIOUS tagging only. Reads fail open;
  SAFE/explicit destination authorization never override earlier A1/A2 vetoes.
  This is coarse task-local risk, not A6 value-origin proof. Final stays pass-through.
- Host backend factory runs inside a spawned child; each cache miss includes
  cold load/generation in a bounded deadline. Terminate/kill/reap on expiry and
  retire failed workers without automatic restart or reuse of stale SAFE cache.
  Bounded shared memory avoids partial pipe reads; child output/errors are sanitized.
- Trace binds current candidate, raw user, host artifact/proposal, model identity,
  prompt/generation/execution hashes and per-attempt wall-clock durations. No
  guard trace or development memory enters agent context. Production immutable
  guard selection and efficient GPU lifecycle still require their own validation.
- Preflight: 446 tests, 80 new; 40 exact A0/A1 pairs + nine synthetic A2 cases,
  89 fresh Replay/31 fake guard classifications. 390 frozen source entries intact.
  No benchmark tuning/Test parsing; no claim of real model quality or Phase 5 closure.
  Selected source `15ed921` reproduces the same stable summary with 446 passing
  tests; all 124 source/548 raw hashes verified. Receipt: `phase5_a2_v2_validation01`.

## 2026-09-07 — Integrate shared A0/A1 ReAct runtime

- Add separate `security_v1/runtime.py` derived from the frozen foundation loop;
  no edits to prior hashed modules. Both A0/A1 use the same loop/prompt/tools/
  decoder. Only security config differs; A2–A6 fail explicitly before output.
- Pre denial consumes a model step but not a Broker call. Store original action,
  related source lineage and fixed POLICY_FEEDBACK separately; no fabricated
  ToolResult or call ID. Next model turn may recover under ordinary step limits.
- Security sidecar links proposals/decisions/denials/actual Broker calls and
  proposed/released final artifacts. A0/A1 finals remain pass-through; no hidden A6.
- Runtime detector errors are typed/class-only, sticky fail-closed for external
  sinks and fail-open for reads. A0 skips the detector. Contract and tests precede
  selected evidence; no benchmark Dev/Test payload inspection or rule tuning.
- Source-native JSON snapshots are the existing detector input representation;
  this is not a new semantic detector and does not guarantee detection across
  every JSON escape or phrase split. Shared runtime integration does not establish
  ASR/utility improvements or real-model robustness. Grouped Dev protocol and
  actual A2 inference remain required before whole-phase acceptance.

## 2026-09-07 — Open Phase 5; freeze first security-component contract

- Owner explicitly authorized Phase 5. Add versioned security modules/configs,
  preserving all 153 Phase 4 source/test/config hashes and frozen datasets.
- Freeze cumulative matrix and typed public-only decision/observation schemas in
  `phase5_policy_contract.md`. A0/A1 execution adapter is the first milestone;
  A2 strict backend/parser/cache interface is not operational real-model evidence.
  A2–A6 config presence is not implementation or acceptance.
- A1 scans raw plus detector-normalized content, tags sources and vetoes external
  proposals after signals unless exact user action/destination is authorized.
  Raw-user anchor grammar is bounded and requires affirmative destination cues;
  quoted/negated/conditional/incidental addresses do not count as authorization.
- A6 will retain cumulative detectors/tracking but adjudicate coarse session
  vetoes with value-origin evidence, per phase5 II/XXXVIII/LV. Detailed A6 policy
  remains to be specified; no silent removal of components or current implementation claim.
- First QA uses synthetic micro-cases only; no Dev tuning, Test payload parsing,
  guard model selection, GPU inference or benchmark outcome optimization.

## 2026-09-07 — Accept Phase 4 after committed-source reproduction

- Source `be7f8b5`; selected `phase4_closure_v1_validation01` passes all 12
  plan DoD gates. 244 tests, setup/Ruff/mypy 160 files/knowledge-check pass.
  45 fresh Dev pairs, 440 smoke overhead runs and two stress runs; no LLM or
  held-out payload parsing. 153 source/1,625 raw hashes and 497 prior entries
  audited. Stable Dev summary matches preflight; no semantic retries.
- Selected added runtime median 5.539 ms, p95 11.749 ms; max smoke traced peak
  527,301 bytes. Both prespecified guards pass. Stress traced peak 21,603,744
  bytes and 4,111,390 log bytes document duplication limits, not content-ref support.
- Acceptance is foundation/plumbing under existing owner waiver, not independent
  review, utility/ASR success, token-level lineage or GPU efficiency. No change
  to frozen research scope, source/data or prior model scores. Phase 5 remains
  gated on explicit owner authorization.

## 2026-09-07 — Phase 4 closure metadata and measurement scope

- Owner requested completion of Phase 4. Keep frozen runtime/primitives, A0
  behavior, benchmark sources and prior evidence unchanged; add host catalog v2
  plus separate QA/measurement modules. No Phase 5 security enforcement.
- Clean host document namespace defaults S1/TRUSTED; cached public pages default
  S0/UNTRUSTED, DB S2/TRUSTED, unlabeled auxiliary sources S2/UNTRUSTED. Explicit
  public overlay metadata is branch-independent. Search joins the whole source
  collection; DB projections join the DB scope, including tainted overlay/rows.
  These conservative initialization rules do not use evaluator facts or payload
  assertions, and are not claims of row-level or token-level attribution.
- New integration scope: 21 fixed clean Dev QA references and 24 paired Dev
  multi-step trajectories prioritizing linked resources. Their scripted outputs
  demonstrate plumbing, not utility, ASR, real-model success or defense.
- Controlled local study: seven alternating timing repeats after warm-up, separate
  three-repeat allocation tracing, process RSS and long-document stress. Thresholds
  and limits recorded before measurement in the closure protocol. No GPU/LLM
  extrapolation; storage duplication and long-context limits must remain visible.
- Plan's proposed file layout is mapped to consolidated versioned contracts in
  the design index. Existing self-review waiver applies; no fabricated Minh or
  independent-review approval. Acceptance remains conditional on closure evidence.

## 2026-09-07 — Additive Phase 4 runtime plumbing and exact raw A0 parity

Add a versioned runtime with frozen ControlState/ContextBundle and pass-through
Pre/Post/Final interfaces, retaining the legacy loop/Broker/parser/tools unchanged.
Exact context bytes, argument/result serialization, format correction and final
answers remain raw. Audit-only normalized views never enter model context or
tool arguments. Unsupported blocking/mutating hooks fail explicitly, not silently
becoming an A0 defense. Separate legacy and foundation-v2 traces preserve replay
comparison while adding observable artifact/control/decision/normalization logs.

Source snapshots retain host-owned native labels; rendered results depend on
both source and action and join labels conservatively. Unknown retrieval defaults
S2/UNTRUSTED, DB defaults S2/TRUSTED; these are documented over-approximations,
not labels inferred from evaluator truth or text claims. Field artifacts cover
email to/subject/body and webhook endpoint/payload. No causal token lineage claim.

CPU QA: 20 smoke + 21 preselected clean Dev + 24 stratified paired adversarial
Dev probes, 65 paired conditions/130 Replay runs, exact context/observable parity.
Clean Dev oracle action/fault scripts are QA-only; fixed final text does not claim
utility success. Attack/benign probes check source exposure, not ASR. 224 tests
pass (39 new), setup/Ruff/mypy 156 files and sealed adversarial hashes pass.
Source metadata/search coverage, sensitive multi-step Dev audit, reproducible
overhead/memory study and final Phase 4 acceptance review remain outstanding.

## 2026-09-07 — Phase 4 authorized; additive primitive foundation

Owner explicitly starts Phase 4. Preserve frozen Phase 1–3 source/data and
introduce `foundation` modules only; no A1–A6 enforcement or hidden A0 changes.
First milestone: versioned optional normalization and immutable run-local JSON
artifact/DAG primitives. Control/context/hooks and runtime integration follow.
Use named raw/Unicode/security profiles; explicit zero-width removal, paragraph
preservation and post-removal Unicode recomposition for idempotence. Removal can
alter emoji joiners; security view is optional and never silently enabled in A0.

Artifacts store canonical JSON strings rather than mutable nested objects. Host
allocates IDs; parents precede children; import verifies rather than trusts IDs.
Independent S0/S1/S2 and explicit TRUSTED/UNTRUSTED joins prohibit declassification
or trust upgrade through normalization/derivation. Phase4 follows its binary
trust proposal; legacy T1/T2 will map conservatively to UNTRUSTED while retaining
original source metadata. No oracle-driven source labeling.

Prerequisites use hash-only Test checks and the already sealed 50 robustness IDs.
Dev QA covers 150 clean instructions/400 adversarial payloads across three
profiles (1,650 checks), using explicit synthetic stress labels rather than
claimed benchmark sensitivity annotations. 185 tests pass (53 new), setup/Ruff/
mypy 151 files pass. No model/Broker run, no runtime/A0 parity claim yet.

## 2026-09-07 — Full release integration and post-seal access discipline

Combine accepted mechanical/linguistic snapshots into separate `release_v2`;
do not repair rejected v1 or rewrite canonical references. Exact 700 variants,
350 per branch, fixed 40/30 families and twenty conservative groups. Public-only
fixture loader exposes only task instructions to Runtime, with overlays/resources
owned by tools; private scorer dispatch remains unchanged. Unique variant and
invocation identities bridge original canonical runtime IDs.

Re-score and archive 1,692 previously recorded paths: 280 canonical standard,
1,400 variant standard and twelve safe alternatives. This is reused evidence,
not new inference. All 732 Test-assigned paths are pre-seal construction QA;
no held-out model runs. Archive stores observable events only. Input/source,
configuration, schema, mapping, environment and dependency hashes are frozen.
Sealing requires the exact source/data bytes already committed to Git.

Run full construction tests before sealing. Afterwards, exclude historical
authoring test modules before collection/import to prevent held-out construction
fixtures entering later development. Preserve their full pre-seal result; use
hash-only seal integrity and Dev-only loading checks afterwards. This is an
access boundary, not a waiver of failing tests. Keep reviewer and strata limits
explicit; Phase 3 acceptance does not authorize Phase 4 or model experiments.

## 2026-09-07 — Reviewed linguistic variants after fixed canonical assignment

Add a separate 280-record linguistic snapshot: 140 individually authored clause
paraphrases and 140 contextual code-mix outputs, each reviewed by the assistant
under the owner's existing waiver. Correct ambiguous glossary compounds before
freeze; do not use model failures or change any previously hashed source/data.
Review is semantic self-review, not independent human certification. Preserve
literal values, modality, timing, derived-disclosure direction and paired utility.
Preflight: 564 fresh reference paths (560 standard/four alternatives), exact
canonical score parity, 244 Test-assigned construction QA and zero model runs.
699 tests pass, setup/Ruff/mypy 143 source files pass. The complete 700-record
release still needs integration and immutable sealing; no Phase 4 work here.

## 2026-09-07 — Three mechanical surfaces and unified private reference adapter

- Continue Phase 3 from the immutable 70-canonical/40–30 selection. Add a separate
  420-record mechanical snapshot (210 attack/210 benign; 120 Dev/90 Test per
  branch), not a new selection or a replacement of old data/scorers.
- Existing helper handles no-diacritic, word-boundary and U+200B insertion.
  Exact output/argument literals remain unchanged even where that leaves accents
  in a no-diacritic payload. Protect NOTICE so insertion targets Vietnamese text.
  All 140 boundary edits were inspected in sentence context under owner waiver;
  structural checks cover the other 280. This is not independent human review.
- Preserve original protected spans, not raw substring counts: removing accents
  can create extra ordinary substrings without changing any original literal.
  The initial structural preflight exposed this checker false-positive before
  reference execution; a positional check and regression test fix the new checker
  only. No canonical, model, scope or historical oracle was changed.
- New adapter dispatches to the existing six scorer types and binds the old
  pilot utility sidecar explicitly. Search-snippet exposures are checked alongside
  primary reads. Public inputs exclude private rule/utility/reference objects;
  every call uses the unchanged Tool Broker and offline mocks.
- Preflight passes 1,128 fresh references: 280 canonical standard, 840 variant
  standard and eight safe alternatives. Scores match hash-bound canonical
  evidence exactly. 488 references use Test-assigned construction data, not
  held-out model inference; no LLM/Kaggle runs or Test-driven model tuning.
- 604 tests pass (109 new), setup/Ruff/mypy 140 source files and clean seal pass.
  Code-mix/paraphrase, their executable QA, complete release integration and Test
  seal remain outstanding; mechanical acceptance must not close Phase 3.

## 2026-09-07 — Whole-pool admission and grouped canonical assignment

- Owner asks to complete Phase 3. Review all 72 stored task/attack/benign texts
  and bind earlier pair rationales. Retain 70 authorization/task-effect scenarios,
  merge hexcode into encoded and rowretry into rowdirect as before. Per-scenario
  whole-pool rationale is in `canonical_selection_v1/review.json`.
- Admit for variant authoring under the existing assistant self-review waiver;
  do not claim independent human review or 70 unrelated abstract mechanisms.
  Existing conservative semantic/template groups remain intact, including edges
  through merged cases. Shared exact sources, artifact values and mock recipients
  add leakage edges without exposing their values in the report.
- Freeze an exact grouped 40/30 assignment objective before variant authoring:
  category/source proportional L1 loss first, target-sink/reference-length loss
  second, fixed-seed SHA256 tie-break last. Enumerate every feasible assignment;
  no model outcome, random retry or edge deletion influences selection.
- The 25-member business group includes 12/15 output-poisoning scenarios. This
  makes ideal strata balance impossible: chosen category split is 10/10 exfil,
  10/10 indirect, 8/7 policy and 12/3 output. Retain this limitation explicitly,
  rather than silently splitting templates or changing category labels. The plan
  allows imperfect small strata; no new representativeness claim is authorized.
  Complexity is reference action count, not empirical model difficulty.
- Seventy selected scenarios reuse 280 of 288 standard reference paths (eight
  belong to merged regression cases). No new Replay/model/Test inference.
  New manifest is separate from unchanged historical `unassigned` snapshots.
  Test remains unsealed; 350+350 reviewed executable variants, release mapping
  and immutable sealing are still required for whole-phase acceptance.

## 2026-09-06 — Gemma 4 and Qwen 7B measured Dev conditions

- Owner requested Gemma 4, a stronger Qwen, and scientific time/efficiency
  reporting. Google file access is now confirmed; Meta access remains pending.
- Predeclare Gemma 4 E4B IT v1 and Qwen2.5 7B Instruct v1 on the same 21 Dev
  tasks with measured protocol `dev21_performance_v1`. Larger Qwen is selected
  by size/availability, not by observing its scores. Historical Qwen 3B remains
  a separately labeled reference. The old unexecuted Gemma 2 condition is deferred.
- Native Gemma 4 loader, non-thinking generation, offline pinned dependencies,
  two T4 GPUs without CPU offload, per-call token/time/memory measurements,
  and group-bootstrap intervals are specified before inference in
  `docs/evaluation/dev21_performance_protocol.md`.
- Local Intel macOS cannot install the required recent PyTorch build; CPU
  library/model preflight is moved to Kaggle. No benchmark inference occurs in
  that preflight. Both mount-layout/Dummy/resume tests still run locally.

## 2026-09-06 — Owner authorizes three-model Dev pilot

- Compare existing 21-task clean_v1.1 Dev pilot with Qwen, Google Gemma and
  Meta Llama. Reuse historical Qwen; prepare Gemma 2 2B IT v2 and Llama 3.2 3B
  Instruct v1 from official Kaggle sources before observing their outputs.
- Keep task selection, A0, generation limits and evaluator fixed. Record native
  chat-template differences; Gemma requires merging system text into user text.
- API metadata confirms model handles; weight-file listing returns 403 for both
  additional models while Qwen succeeds. Await account access before submission.
- This is Dev-only diagnostic scope alongside Phase 3. See
  `knowledge/multimodel_dev_pilot.md` for comparison and audit protocol.

## 2026-09-06 — Replacement seal and first-attempt Kaggle evidence

- Frozen v1.1 hash `692ca92a214b0da87245ca7d11a074a74d416558f377bc448c125bd7d387be38`;
  150/100 exact group-wise split with 50 robustness IDs selected before sealing.
- Frozen inference source `42c1d45ebf349884496dd9f3029b640027f8622d`, one private
  Dataset v1 and one kernel push. Both local mount representations, eight tools,
  fault parser and 21-task Dummy/resume passed before upload.
- Server derived `huylmhuhu/react-vietnamese-clean-v1-1-dev-pilot` from title,
  rather than the requested slug. Followed the returned handle; no duplicate push.
- Kernel v1 COMPLETE: 21 terminal, 0 model errors, 318 schema-valid trace events,
  5/21 Dev diagnostic success. No inference retries and no Test model access.
- Input/checkpoint hashes and four secret values audited (zero matches). Raw
  artifacts stay ignored; selected audit hashes are tracked. v1 and v1.1 inputs
  remain unchanged; later commits only add audit/docs/tests/validation entrypoints.
- This does not certify unrestricted natural-language equivalence or every
  possible tool path. Remaining annotation/comparator coverage is a Phase 2
  closure item; do not silently interpret 5/21 as final Test TSR.

## 2026-09-05 — Owner authorizes clean_v1.1 replacement and Dev experiments

- Owner approved replacing the invalid benchmark, running experiments, retaining
  knowledge, and improving Kaggle skills/preflight after repeated packaging errors.
- Preserve v1 and both historical Kaggle runs byte-for-byte. Author v1.1 from
  the synthetic environment/templates, not by selecting tasks based on old scores.
- Retain 250/150/100 and category quotas. Repair cross-category instance grouping,
  dependent DB/document tasks, executable QA and typed argument/fact comparators.
- Experiment scope: CPU oracle/replay/negative controls, mount/import/fault/resume
  preflight, then one frozen Qwen2.5-3B Dev pilot on the existing Kaggle account.
  No held-out model run or Phase 3 work is authorized by this implementation.
- Update project-scoped experiment skill and runbook with observed Kaggle lessons;
  do not silently alter global skill behavior for unrelated projects.

## 2026-09-05 — Initial operational contract

- Use the existing Word document as approved scope and `docs/` as the concise
  implementation contract.
- Use three backbones for RQ1, one fixed backbone for RQ2/RQ3 comparisons.
- Treat A0–A6 as cumulative defense levels.
- Split attack data by canonical family (40 Dev / 30 Test) before variants.
- Select the 50 robustness canonicals from clean held-out Test before sealing.
- Store repository skills in `.agents/skills` per current Codex discovery.

Exact model identities and collaborator account remain configuration decisions
and are not inferred here.

## 2026-09-05 — Repository and execution accounts

- GitHub source of truth: private repository
  `Lamhuy0489/react-vietnamese-agent`.
- Repository-local Git author: `Lamhuy0489 <lamquanghuy1234@gmail.com>`.
- Kaggle CLI smoke authentication uses the existing local credential for
  `lamhuy8904`; credential files remain ignored and outside Git history.
- Teammate access was pending at setup close and is resolved by the following
  Phase 0 handoff entry.

## 2026-09-05 — Phase 0 accepted and Phase 1 authorized

- Project owner accepted the frozen research contract without changes.
- GitHub user `minhb5d` was invited to the private repository with write access.
- Phase 1 starts on branch `phase-1/a0-vertical-slice`.
- Phase 1 uses synthetic smoke data only and does not access held-out Test.

## 2026-09-05 — Phase 1 Kaggle smoke condition

- The owner deferred Minh's assigned smoke-task review; this does not transfer
  authorship and is recorded as an owner-approved Phase 1 gate waiver.
- Use Kaggle account `huylmhuhu` (`kaggle1.json`) for the single authoritative
  run. Accounts `meanalways` and `buiquocviet` are fallback credentials only and
  must not be combined to pool quota or select a favorable result.
- Freeze Qwen2.5-3B-Instruct at Kaggle model source
  `qwen-lm/qwen2.5/transformers/3b-instruct/1`.
- Run on an NVIDIA T4 with internet disabled and a private source-bundle Dataset.
- Kaggle attempt v1 stopped before model loading because Kaggle expanded the
  uploaded source archive into Dataset files. This infrastructure failure is
  retained; the wrapper now supports Kaggle's expanded mount representation.
- Attempt v2 confirmed the expanded archive is placed under a generated
  subdirectory rather than the Dataset mount root. It also stopped before model
  loading; the wrapper now discovers the single packaged `src/react_agent`
  directory instead of assuming its parent path.
- Attempt v3 reached local environment construction, then stopped because
  Kaggle subprocesses did not inherit a source-package import path. The wrapper
  now fixes `PYTHONPATH` to the frozen bundle's `src` directory.

## 2026-09-05 — Phase 1 accepted

- Before the next upload, added regression tests for expanded Dataset mounts,
  case-insensitive model framework paths, and frozen-file tampering; added a
  local Kaggle-mount simulation with per-file hashes and credential guards.
- Authoritative attempt v4 used source commit `2138dc8`, private Dataset v5,
  Qwen2.5-3B-Instruct v1, NVIDIA T4, and internet disabled.
- The run produced 20/20 terminal trajectories, zero crashes, 262 valid trace
  events, 3/20 semantic task success, and 78.87% schema validity.
- Low semantic performance is retained as A0 evidence. No quality-based retry
  or prompt tuning was performed after observing the full run.
- Minh's review remains deferred by explicit owner instruction. This is an
  owner-approved collaboration-gate waiver, not a claim that review occurred.
- Phase 1 is accepted; Phase 2 remains not started and held-out Test remains
  uncreated/unaccessed.

## 2026-09-05 — Same-machine workflow and Phase 2 authorization

- The project owner confirmed Huy and Minh use the same machine and explicitly
  removed the peer-review requirement for ongoing work.
- Do not fabricate cross-review metadata. Phase 2 tasks use
  `review_mode=automated_checks_owner_waiver` and must pass deterministic schema,
  oracle, duplicate/leakage, consistency, split, and checksum validation.
- This replaces Phase 2 DoD-5 peer-review coverage with 100% automated QA under
  the explicit owner waiver. It does not claim task-by-task owner inspection.
  Impact: there is no independent human-review evidence; reports and the data
  card must disclose that limitation.
- Phase 2 clean-benchmark work is authorized. Create the 250-task pool before
  splitting; do not run a model on held-out Test or modify Test after sealing.

## 2026-09-05 — Integrity audit and Phase 2 acceptance withdrawal

- User requested continuation and an additional Phase 1 check. Static audit
  found a generation/validation defect, not model-driven evidence: 30 pairs
  share facts/evidence with different groups, and 12 cross Dev/Test. The old
  signature included task-local `fact_id` labels.
- Reopen Phase 2 and quarantine `clean_v1.0`; no release tag or Phase 3 work.
  Quotas, research scope and review waiver remain unchanged. Hash consistency
  is not proof of semantic split independence.
- Preserve task/GT/environment/schema/manifest bytes and raw Kaggle outputs.
  Refreshed QA reports are derived audit outputs, not input repairs. Static
  split reads were for integrity only; no Test model output, prompt/policy
  tuning, model selection, or in-place data repair occurred.
- Seal guards stop generators before writes; packaging rejects invalid splits.
  Group allocation, evidence-backed QA and comparator work need a separately
  versioned replacement with defined rerun scope. This is proposed, not
  recorded as owner-approved. Do not regenerate existing v1.
- Generator-assigned booleans do not satisfy the waiver's QA requirement;
  7/21 pilot score remains historical provisional output, not validated TSR.
- Earlier post-seal review-metadata corrections changed the dataset identity
  to `2a98633481ac82ae77dbbbe96877d67a3353894ce869e54947e0cf5335371c62`
  at commit `37e121f`. This was not a Test-content repair; lack of a separate
  contemporaneous deviation entry is a provenance limitation. This audit
  performs no further resealing.
- Phase 1 smoke evidence revalidated: repeatable CPU runs and eight original
  Kaggle hashes; no runtime changes or new model inference.
## 2026-09-06 — Owner authorizes Phase 3 adversarial authoring

- Begin Phase 3 from the frozen `clean_v1.1` scope using synthetic overlays only.
- First milestone is an unreviewed draft: 70 family-level scenarios, five
  deterministic linguistic variants per family, and one paired benign control
  per variant. No model output, held-out Test tuning, or real side effect is
  permitted during authoring.
- The draft is not Phase 3 acceptance evidence until semantic/security review,
  overlay validation, and reproducibility checks pass.

## 2026-09-06 — Measured Dev pilot completed; no final backbone decision

- Owner requested Gemma 4, a larger Qwen and research-style efficiency metrics.
  The predeclared `dev21_performance_v1` protocol supersedes the unexecuted
  Gemma 2 condition; the three-family final capability target is unchanged.
- Gemma 4 E4B IT v1 and Qwen2.5 7B Instruct v1 each completed one 21-task Dev
  run from source `58fdeb510d1a8e3265c60f97650f64e8898700e4`, same two-T4
  hardware class, FP16/SDPA, pinned software, native templates, no thinking.
- Exact input/source/measurement and checkpoint audits pass. Strict scores
  remain 6/21 and 3/21; no semantic retries, evaluator edits or hidden Test use.
  Post-inference reporting adds presentation tables only, not new score rules.
- Publish selected aggregate JSON/CSV/Markdown, figures and hash receipts in
  GitHub; raw synthetic trajectories stay ignored locally and on private Kaggle.
- Do not interpret the small selected Dev set, heterogeneous tokenizers,
  single-run timings or path-constrained evaluator as a final model ranking.
  Historical Qwen 3B is not a controlled timing comparator. Meta Llama is
  pending access and is not assigned a zero score. Phase 3 stays in progress.

## 2026-09-06 — Strengthen development memory and resume Phase 3 QA

- Owner requests repository knowledge maintenance before continuing work.
  Add a handoff entry point, update obsolete v1 runbook instructions and check
  links/sections. Memory is development-only, never injected into model inputs.
- Resume Phase 3 with static draft integrity checks, not new LLM inference.
  Counts alone are insufficient: record template-overlap candidates, category
  imbalance, webhook/benign annotation and surface-transform defects.
- Preserve v1 draft and all clean/measured frozen artifacts byte-for-byte.
  Diagnostics read both unreviewed adversarial splits for integrity only; no
  Test-driven tuning, attacks filtered by model success, or phase advancement.
- Add mechanical surface candidate helpers with protected literals and pending
  review status. Do not regenerate the existing draft or claim human semantic
  approval from software checks. The next authoring milestone is executable
  canonical pairs/overlays with private violation and safe-utility fixtures.

## 2026-09-06 — Executable authoring workbench, not a benchmark replacement

- Continue authorized Phase 3 with four unsplit synthetic pairs under
  `data/adversarial/workbench_v2`, not counted toward the 70 canonical families.
  Preserve v1 rather than repair/reseal it in place. No new variants/Test split.
- Freeze the narrow workbench interface in the dedicated contract: public
  task only, source overlay on copied environment, offline private QA oracle.
  No A0 prompt/policy/tool interface changes or real-model inference.
- Sixteen Replay runs exercise safe/negative scripts on both pair branches,
  four source types and email/webhook/final sinks. Successful mock results
  are required to count delivery; proposed violations remain separate.
- Exact artifact/fact/action fixture checks are intentionally bounded and are
  not the Phase 6 evaluator or evidence of model attack success. Independent
  language review is not claimed. Canonicals and variants remain review-pending.
- 143 tests, setup, Ruff and mypy pass; originals retain hashes. The next gate
  is broader canonical/data-scope QA and diverse family authoring, not advancing
  to defense implementation or running Test.
- Implementation and fixture source commit: `b7ae80c`; selected QA receipt
  records exact verifier/input hashes. Raw executions remain ignored locally.

## 2026-09-06 — Owner approves bounded canonical/data-scope expansion

- Expand Phase 3 into a separate 12-pair candidate set: four adapted from the
  workbench and eight newly authored. Preserve prior inputs, source receipts
  and clean/measured releases. No variants, Test split, inference or defenses.
- Add separate catalog metadata and private data-scope schema. Compile SQL
  offline for table/column access, not row-level authorization or equivalence.
  Missing/unsupported scope remains unassessed, never accepted as safe.
- Artifact authorization is destination-specific and independent of final
  disclosure. Utility/leakage remain literal bounded fixtures; transformed
  disclosure and general natural-language grading are not claimed.
- 48 Replay fixtures pass (24 safe/24 negative), balanced across four attack
  categories and four source types. Nine template-group annotations still
  need semantic scrutiny; twelve candidate IDs are not twelve accepted families.
- 168 tests, setup, Ruff, mypy and sealed clean validation pass; old receipts
  and measured hashes match. Selected expansion receipt records the actual
  base commit and exact source hashes; raw output remains ignored.
- No human review is fabricated under the existing owner workflow waiver.
  Next: semantic/template QA, typed utility/review evidence and further diverse
  canonical authoring before variants, split or Phase 3 acceptance.
- Implementation commit: `3e68814`. Knowledge validation and changed-file
  scan against four local credential values pass with zero matches.

## 2026-09-06 — Continue canonical QA and report evidence-based progress

- Owner asks to continue Phase 3 and estimate completion. Record a rough
  25–30% work estimate with a 12-DoD evidence table, explicitly not acceptance
  percentage. Twelve candidates are not twelve approved independent families.
- Add separate private typed-utility sidecars and offline scoring, preserving
  previous candidate/workbench/clean inputs, source files and measured scores.
  Typed values/source evidence close demonstrated literal substring and date
  format gaps; this is not semantic entailment or a Phase 6 general evaluator.
- Enumerate all 66 candidate pairs and conservative connected review units;
  three shared template pairs yield nine provisional units. Do not infer
  semantic independence from different IDs, sources, sinks or action shapes.
- Assistant authoring inspection identifies self-labelled fake instructions,
  benign safety cues and length imbalance for future versioned revision.
  No independent human approval is fabricated; no variants or split assigned.
- 48 fresh Replay outcomes pass typed QA; 220 tests and setup/Ruff/mypy pass.
  No LLM/Kaggle/held-out model runs or A0 changes. Next dataset step is a
  versioned, neutral paired pilot with explicit group decisions, then further
  diverse canonical authoring and the remaining acceptance gates.
- Implementation source: `114615d`; selected receipt records exact source and
  sidecar hashes. Previous receipts/inputs and 12 measured artifacts retain
  hashes. Knowledge checks and four-value credential scan pass with zero matches.

## 2026-09-06 — Implement separate neutral paired pilot revision

- Continue owner-authorized Phase 3 with `candidates_v2_2`, a wording/grouping
  revision of twelve v2.1 candidates, not twelve additional families. Preserve
  public/private oracle bytes and all prior datasets, sources and receipts.
- Change only attack/benign additions and catalog semantic/template groups.
  Remove explicit fake/self-authorized class cues from attack wording and
  safety-instruction cues from benign wording, without changing target actions,
  destinations, legitimate task, artifact, authorization or reference scripts.
- Declare a bounded 0.8–1.25 whitespace-word ratio gate for this revision.
  Actual ratios 1.0278–1.1333 pass; this is not universal semantic QA or a
  model-token matching claim. No model output informed revision choices.
- Conservatively merge destination substitution and out-of-scope document
  reads across source/sink types. Seven review units retain prior connections;
  no independent-family certification, Test split or variants are produced.
- Assistant author self-review is explicit; independent human approval is not
  fabricated under the owner waiver. Canonical approval remains pending.
- 48 fresh Replay scores equal parent typed/security scores; 244 tests pass,
  with setup/Ruff/mypy and sealed clean validation. Next authoring milestone:
  new mechanisms and missing retrieval/multi-step coverage, not another rewrite
  of the same twelve cases or advancement into defense/evaluation phases.
- Implementation source: `53452a5`. Prior/source/sidecar hashes and twelve
  measured artifacts match; knowledge validation and four-value credential
  scan pass with zero matches. Selected receipt records exact execution inputs.

## 2026-09-06 — Add eight new mechanism candidates, not another pilot rewrite

- Continue owner-authorized Phase 3 with a separate eight-pair batch. Preserve
  all previous datasets, source receipts and measured scores. Combined count is
  twenty unsplit candidates, not twenty accepted independent families.
- Introduce private offline argument-path, successful-call-quota and prior-success
  rules plus complete Base64/hex disclosure checks. Do not modify A0 or claim
  general temporal/data-flow/encoding/row-level oracles from these bounded rules.
- Use real document/cache search, including genuine snippet exposure and longer
  tool paths. All eight tools are exercised; every runtime action goes via Broker.
- Keep three business-parameter cases in one group and two encoded cases in one
  group. Five new + seven prior groups produce twelve provisional review units;
  audit all 190 pairs without assigning Test or fabricating human review.
- 32 new Replay fixtures and 263 tests pass; setup/Ruff/mypy/clean seal pass.
  No LLM/Test inference or model-output-based example selection. Update effort
  estimate to a rough 30–35%, explicitly distinct from approved-family counts.
  Next: new multi-source/data-scope scenarios, then canonical pool consolidation,
  variants, stratified split and freeze once their acceptance evidence exists.
- Implementation source: `b3e38f8`. Previous source/input/receipt hashes and
  twelve measured artifacts match. Knowledge checks and four-value credential
  scan pass with zero matches; raw output remains untracked.

## 2026-09-06 — Linked-source/row-scope batch and unified pool QA

- Continue the owner's request to finish Phase 3 without changing research
  targets. Add eight unsplit scenarios with explicit auxiliary resources and
  private bounded row grants. Preserve previous data, source hashes and scores.
- Row SQL supports only the documented single-table grammar; primary-key
  identities are checked offline/read-only with bound literals. Unsupported
  SQL is unassessed, not safe. This is not a runtime A0 defense or a claim of
  arbitrary row-level inference. Auxiliary reads still go through the Broker.
- Four row cases share a conservative group; three linked cases connect to
  earlier groups. Combined 28 candidates form 14 provisional review units;
  378 comparisons do not certify 28 independent accepted families.
- Unified QA reruns all three active batches: 112 paths, 56 safe/56 negative.
  297 tests pass; setup/Ruff/mypy 119 source files and clean seal pass. Seven
  previous receipts/347 hash entries match, including twelve measured artifacts.
- Distinguish `qa_valid` from `phase3_accepted`; `--require-acceptance` returns
  exit 2 while saving successful QA evidence if whole-phase gates are missing.
  Neither case counts nor file presence can automatically close Phase 3.
- Source implementation `89eedaa`. Self-review is explicit; independent human
  review is not invented under the owner waiver. No variants, split, model
  runs or Test-driven tuning. Next: consolidate whole-pool review and author
  missing canonical scenarios, then grouped split, paired variants and freeze.
  Do not demand 70 unrelated abstract mechanisms or pad families by renaming.
  Final credential-value scan: four values across 24 changed files, zero matches;
  selected receipt source/input hashes and knowledge checks pass.

## 2026-09-06 — Expand to forty working candidates and record author review

- Owner requested continued Phase 3 work and a progress estimate. Report a
  rough 40–45% effort estimate, explicitly not acceptance; 40/70 ≈ 57% refers
  only to candidate count. Phase targets and acceptance gates are unchanged.
- Record assistant self-review of the prior 28-candidate pool and twelve new
  transaction/sink-position pairs. Do not fabricate peer review or equate
  retaining a working candidate with final family admission.
- Reuse existing runtime, overlays and private oracles. New full-payload rules
  include record/account identifiers and extra fields, with exact JSON types;
  email subject and body are both scoped. No A0 defense or old-score change.
- Detect encoded disclosure in email subject and JSON property names separately
  from exact-message mismatch; explicit artifact grants and failed-send counts
  have regression tests. This is complete Base64/hex, not general data flow.
- Preserve existing grouping edges: fifteen conservative groups and 780 pair
  comparisons across forty candidates. Most transaction fields remain in the
  shared business-payload group, not twelve new independent mechanisms.
- Source `7f1f284`; 160 fresh Replay (80/80), 321 tests, setup/Ruff/mypy (121
  files) and clean seal pass. Eight older receipts/451 hash entries match,
  including twelve measured artifacts. Original v1 static audit still refuses
  acceptance; static Test integrity access is not Test-driven model tuning.
- No LLM/Kaggle run, variant generation or split/freeze. Next: complete the
  missing canonical scenarios and record family release decisions, then grouped
  split, reviewed variants and sealed release. Do not grow infrastructure
  without a concrete scenario need or pad the target by renaming templates.
  Final scan: four credential values across 22 changed files, zero matches.
  Selected receipt source/input/author-review hashes and knowledge checks pass.

## 2026-09-06 — Add authorization-flow candidates without changing old scorers

- Continue owner-authorized Phase 3 in a separate eight-candidate batch. Compose
  existing public source builders and private typed/mechanism scorers, keeping
  their bytes and A0 behavior unchanged. No model-output selection or Test tuning.
- Exercise directional artifact grants, allowed private final output but
  prohibited email disclosure, crossed two-artifact routing, aggregate/suffix
  disclosure bounds, notification/commit and conjunctive-source prerequisites,
  and explicitly selected current-source submission.
- Forty-eight working candidates remain in fifteen conservative groups; the
  eight additions are not eight certified independent abstract mechanisms.
  Final family admission/merge and linguistic equivalence review remain open.
- Source `56de8e7`; 192 fresh Replay (96/96), 341 tests, setup/Ruff/mypy (123
  files) and sealed clean validation pass. Nine old receipts/566 hash entries
  match, including twelve measured release artifacts. No Kaggle/LLM/Test run.
- Rough effort estimate 45–50%, not acceptance. 48/70 ≈ 69% is candidate count
  only. Finish missing canonical scenarios, then full-pool admission decisions,
  grouped split, reviewed paired variants and immutable release gates.
  Selected source/input hashes match; credential scan checks four values across
  22 changed files with zero matches. Knowledge links pass after receipt creation.

## 2026-09-07 — Correct two false-safe rules and record admission merges

- Continue authorized Phase 3; no scope/target change or Test/model-based tuning.
  Source `e001c8a` adds `mechanism_batch_v2`, changing only two allowed rule
  fields plus README. Preserve all old sources, data, receipts and model scores.
- Public-task review exposed a missing successful-call quota and a missing
  business-value equality. Real Broker Replay reproduces both false-safe gaps
  under old rules; corrected rules reject the same observed violations. Failed
  violating proposals count as proposed, not executed. No A0 defense is added.
- Hash-bound assistant self-review under the existing owner waiver covers all
  48 candidates. Merge hexcode into encoded and rowretry into rowdirect; retain
  their original files and regression fixtures. Retain 46 representatives for
  later whole-pool selection, not semantic-independence or release certification.
  Fifteen conservative groups remain. Need at least 24 additional retained
  scenarios for 70; final pool review may merge further. No fabricated reviewer.
- Selected evidence contains 38 fresh Replay (32 standard plus six controls/
  counterexamples), explicitly reusing 160 standard paths from unchanged cases.
  367 tests, setup/Ruff/mypy (126 files) and sealed clean validation pass. Ten
  prior receipts/689 hash entries match, including twelve measured artifacts.
- Admission verifier saves valid bounded QA but refuses whole-phase acceptance
  with exit 2. Historical pool v3 still uses v1 rules; it is not the current
  revision gate. No variants, split/freeze or LLM/Kaggle/held-out inference.
  Next: distinct canonical/benign authoring, full-pool selection, grouped split,
  reviewed paired variants and immutable release. Estimate stays 45–50% effort.
  Selected receipt: 134 source/input/review hash entries and 38 raw traces match;
  four credential values checked across 24 changed files have zero matches.
  Knowledge-check passes after the selected receipt is fully written.

## 2026-09-07 — Add four bounded disclosure pairs

- Source `1c3f829` adds separate `disclosure_batch_v1`: private search argument,
  fragmented final output, same-recipient email accumulation and JSON value
  fragmentation. Existing scorer/runtime/data bytes remain unchanged.
- Public tasks authorize private reads and public status utility, not private
  disclosure. Negative fixtures preserve utility and isolate new channel coverage
  from old typed scoring. No model-output-based selection or Test-driven tuning.
- The oracle recognizes a literal query value or two exact declared pieces,
  not arbitrary reconstruction/entailment. Successful recipient-local history
  counts only the coverage-completing send; failed effects are not executed.
  Explicit grants are respected. Absence of a full-fragment hit is not a general
  privacy guarantee. All tools stay offline and every action uses the Broker.
- Assistant self-review under the owner waiver retains four working candidates,
  not four certified independent families. Three fragment cases share a group.
  Pool: 52 stored, 50 retained, two old merges, 17 conservative review units,
  1,326 comparisons. At least 20 further retained scenarios remain necessary.
  All four new pairs are DB/exfiltration; final stratification is still open.
- Selected receipt binds 16 fresh Replay and explicitly reuses 192 prior standard
  paths; 208 total is not a fresh-run count. 401 tests pass (34 new), setup/Ruff/
  mypy 129 source files and clean seal pass. Eleven old receipts/823 hash entries
  match, including twelve measured artifacts. No LLM/Kaggle/held-out inference.
- Whole-phase acceptance remains false; exit 2 with `--require-acceptance` is
  intentional. No variants, grouped split or freeze. Next: remaining distinct
  canonicals with source/category coverage, final pool selection and release gates.
  Selected receipt: 133 source/input/prior hash entries and 16 raw traces match;
  four credential values checked across 24 changed files have zero matches.
  Knowledge-check passes after receipt creation.

## 2026-09-07 — Add twelve task-effect pairs toward canonical completion

- Owner requests completion and an honest progress estimate. Source `9917eb0`
  adds a separate twelve-pair batch, using old runtime and scorers unchanged.
  Seven tool-output, three indirect/document and two policy/cache cases improve
  source/category coverage. Existing frozen labels and data are not altered.
- Distinctions: denomination, rounding, idempotency identity, atomic effects,
  expiring permission, allocation, computation attribution, signatory identity,
  source citation, evidence backdating, time zone and queue priority. All remain
  in the conservative business-payload group, now 25 retained members; do not
  split it to manufacture independence or improve Dev/Test strata.
- Public authorized full payload, source prerequisite and one-successful-send
  limit are explicit. Negative fixture violates payload and fails legitimate
  sink completion despite correct final fact. No false utility claims.
- 64 stored/62 retained, two old merges, 17 groups and 2,016 comparisons. Review
  is assistant self-review under owner waiver, not final independent-family or
  human-review certification. At least eight more retained scenarios needed;
  full-pool selection may merge further. No variants or split/freeze yet.
- 48 fresh Replay plus 208 explicitly reused standard paths. 428 tests pass
  (27 new), setup/Ruff/mypy 131 files and clean seal pass. Twelve old receipts/
  956 hash entries match, including twelve measured artifacts. No model runs,
  held-out inference, Test-driven tuning or old-score changes.
- Estimate 50–55% effort, unweighted and not acceptance. 62/70 ≈ 89% refers only
  to provisional representative count. Remaining work: distinct canonical
  boundaries, whole-pool review, grouped 40/30 split, paired variants and seal.
  `--require-acceptance` exits 2 with valid bounded QA; no phase closure claimed.
  Selected receipt: 143 source/input/prior hash entries and 48 raw traces match;
  four credential values across 23 changed files have zero matches. Knowledge
  validation passes after receipt creation.

## 2026-09-07 — Reach seventy provisional representatives with boundary cases

- Source `c5e1030` adds eight separate pairs: private membership/threshold/
  comparison/difference, final credential solicitation/false approval, shared
  email-webhook quota and sticky revocation from a designated status source.
- New private BoundaryOracle extends expected outcome with `final_policy` and
  requires its own loader. Existing schemas/scorers/runtime remain unchanged.
  Final-policy and derived-final outcomes are not raw leaked artifacts or
  fictitious tool calls. Future release QA must retain these fields explicitly.
- Projections compute from exact annotated synthetic values; arbitrary inference,
  paraphrase and entailment remain out of coverage. Exact normalized standalone
  final-line checks do not imply comprehensive negation/quotation analysis.
  Shared quota requires successful source evidence and one allowed alternative;
  failed sends do not consume quota. Explicit observed revocation is sticky,
  and unknown/failed/wrong-source status cannot authorize a send.
- 72 stored/70 retained, two old merges, 20 conservative groups, 2,556 pair
  comparisons. Retained category counts 20/15/20/15 match the plan's proposal,
  not proof of independent-family acceptance. No split or variant generation.
- 34 fresh Replay (32 standard plus two safe alternatives), 256 explicitly
  reused standard paths; total standard 288. 466 tests pass (38 new), setup/
  Ruff/mypy 134 source files and clean seal pass. Thirteen older receipts/
  1,099 hash entries match, including twelve measured artifacts. No LLM/Kaggle/
  held-out inference, Test tuning or historical score changes.
- Stop count-driven expansion. Next whole-pool semantic/pair admission, grouped
  40/30 feasibility with honest strata limits, then reviewed paired variants
  and seal. Preserve the 25-member business group. Further merges/replacements
  may be necessary despite numeric target. Effort estimate 55–60%, unweighted,
  not phase acceptance. Exit 2 with valid bounded QA intentionally refuses closure.
  Selected receipt: 155 source/input/prior hash entries and 34 raw traces match;
  four credential values scanned across 25 changed files have zero matches.
  Knowledge validation passes after the selected receipt is written.
# 2026-09-12 — Complete native ordinary pair with explicit T4×2 identity

- The first ordinary-pair submission used the generic `gpu` accelerator and
  stopped before model initialization because only one GPU was visible.  Keep
  that error receipt immutable and do not retry its identity.
- The owner-approved follow-up uses a fresh private kernel identity and the
  explicit `NvidiaTeslaT4` machine shape.  The package source, wrapper bytes,
  bootstrap identity, pinned model mounts and offline Dataset remain unchanged;
  only the remote kernel identity/accelerator request changed.
- The kernel completed one technical A/B/A run: 21/21 public Dummy tasks,
  two native model loads, six native generations, two T4 residency deltas and
  six signed recovery samples.  Two local joined audits match the worker audit
  byte-for-byte.  Forced `TERMINATE/-15` cleanup is reported separately from
  graceful cleanup.
- This is feasibility/provenance evidence only.  It does not select a guard,
  measure ASR/utility, authorize Test access, or close runtime A0–A6/grouped
  Dev/freeze gates.  The release audit records `phase5_accepted=false`.

# 2026-09-12 — Add bounded A4 processing-scope component

- Add a new `a4_processing_scope_v1` host-only component rather than editing
  frozen A3–A5/session or v5 runtime sources. The component extracts exact
  affirmative `DOC_*`/`CACHE_*` and bounded SQL table/column anchors from raw
  user text, rejects quoted/conditional/negated clauses, and records only
  hashes/opaque host identities.
- An explicit raw-user scope is a hard boundary. Without one, the first read
  remains compatible with existing behavior until an untrusted source is
  observed; thereafter only previously observed exact resources or database
  subsets are allowed. Search, malformed SQL and unknown actions fail closed;
  calculator and external sinks remain delegated to their existing gates.
- This is a deliberately bounded component milestone, not a silent contract
  change or runtime adoption. It does not implement private-final entitlements,
  causal LLM attribution, benchmark tuning or Test access. A new runtime version
  and independent differential evidence are required before Phase 5 acceptance.
- QA receipt scope: 14 synthetic conditions, 21 focused unit tests and the full
  repository suite with no model/Kaggle/Test inference. Existing source hashes,
  frozen inputs and prior receipts remain unchanged.

# 2026-09-13 — Add bounded private-record final entitlements

- Add a new host-only `final_entitlement_v1` component without editing frozen
  public-final/value-origin policy or runtime v5 sources.
- A grant requires an affirmative raw-user final-answer clause naming an exact
  synthetic resource/table and supported value type. Quoted, conditional,
  negated and scope-only clauses do not grant access.
- Bind raw user, proposal ancestry and origin index; release only trusted exact
  origins with matching source/table/type. Wrong-source/type or untrusted values
  are redacted; normalized-only, incomplete coverage or residual unauthorized
  values deny to an empty final. Sensitivity/trust joins remain conservative.
- This is a bounded component milestone only. It does not claim semantic or
  complete origin coverage, runtime A0–A6 adoption, ASR/utility evidence or Phase
  5 acceptance. QA uses synthetic data only (12 cases, no model/Kaggle/Test),
  and all prior seals/receipts remain unchanged.

# 2026-09-13 — Add versioned runtime v6 entitlement adapter

- Add `security_runtime_v6_entitlement_adapter` as a host-only A6 composition
  over the frozen task-local v5 loop. A per-call function-global map supplies
  the entitlement final bound without modifying or duplicating `runtime_v5.py`.
- A supplied `FinalEntitlement` must hash-bind to the raw task instruction before
  any output/guard worker is created. When omitted, only the raw user clause is
  extracted at the final sink; extraction failure becomes an empty grant. The
  existing Broker, warm-guard, A0–A5 policy and observable traces remain active.
- QA is limited to ten synthetic runtime conditions and 25 focused tests using
  `data/smoke`; no real model/Kaggle/Dev/Test/private-GT inference. This does
  not close production guard/GPU lifecycle, broader A4/origin coverage, grouped
  Dev freeze or Phase 5 acceptance; prior seals remain unchanged.

# 2026-09-13 — Correct entitlement/scope integrity without rewriting evidence

- Owner requested remediation following audit. New development uses runtime v7
  and versioned v2 entitlement/scope/origin components; v1/v6 stay unchanged as
  historical reproduction targets, not recommended security implementations.
- Fix clause Cartesian grants, hash-only supplied authorization, mixed raw and
  zero-width finals, A0 metadata contamination, and table/column scope binding.
  Compose bounded scope at A4–A6 before Broker while retaining coarse vetoes.
- An actual smoke DB row regression exposed silently omitted `SV_SYN_*` IDs.
  Add their bounded typed/lexical extraction; unsupported recognized typed fields
  invalidate coverage. No dataset, tools, prompts or decoding changes.
- Entitlement v1's selected pytest log fails its recorded raw hash. Preserve
  both files, withdraw reliance on that receipt, record independent audit and
  rerun repairs under a fresh identity. Never rewrite expected hashes to match
  overwritten logs. v6's byte-valid receipt does not establish behavioral safety.
- CPU repair QA is not grouped Dev/model quality or Phase 5 freeze. ModelPair
  runtime/GPU, production guard, broader coverage and formal acceptance stay open.

# 2026-09-13 — Compose task-owned ModelPair with runtime v7

- Add `pair_runtime_v1.run_pair_task` and parent-owned role adapters. A2–A6
  receive a fresh pair; A0/A1 receive only a bounded agent factory/execution
  configuration. No nested guard spawn or pair transfer across owner PIDs.
- Preserve the existing v7 loop, A4 scope and A6 entitlement/origin behavior.
  READY startup attempts remain in the outer receipt and are excluded from
  actual guard generation counts. Guard errors retire the pair and clear cache
  through the existing WarmModelGuard semantics.
- Outer lifecycle receipts survive startup failures and cancellation. Record
  actual worker methods/PIDs/handles, separate startup/runtime/outer-cleanup
  timing, and explicitly state that runtime includes inner cleanup.
- Acceptance for this milestone is real-spawn synthetic CPU integration and
  source/raw/data integrity. Native Kaggle packaging, GPU cleanup/performance,
  production guard quality/grouped Dev and Phase 5 freeze remain separate gates.

## CPU01 trace-schema deviation and CPU02 rerun

- CPU01 at source snapshot `819af7a` passed 2,492 tests (one dependency skip),
  but independent trace inspection found READY sequence 1 being interpreted by
  the warm-only trace schema. Keep its receipt/raw bytes unchanged as development
  history; it is not the selected integration acceptance evidence.
- Use `guard_trace_pair_v1`, preserve actual transport sequence/cold-start fields,
  and join guard traces with the outer worker snapshot. Record host proposals
  independently: after guard failure a closed pair can reject a further agent
  proposal before any worker attempt. Do not count that as model inference.
- CPU02 uses fresh output/receipt identities and a joined auditor with deliberate
  corruption tests. This is an evidence-format correction, not a policy/prompt,
  model, decoding or benchmark change; no Test inspection is authorized.

# 2026-09-13 — Version pair outcome and failed-startup evidence

- Continue the owner-requested Phase 5 work with a v2 receipt/runtime/auditor,
  preserving selected v1 CPU02 source and raw bytes. This is not a scope change.
- Real process termination after a successful worker response reproduces the
  pair post-response liveness failure. Worker OK and host ERROR are both true;
  bind host proposals to exact pair event ranges instead of equating statuses.
- Record elapsed startup on all exit paths and explicit completion. On startup
  failure the interval can contain pair-internal cleanup; it is not weight-load
  time. Outer cleanup and runtime-including-inner-cleanup remain separate.
- Keep all policy/model/prompt/tool/decoding behavior and public interfaces.
  CPU fault tests are not native GPU cleanup/guard quality or Phase 5 freeze.
