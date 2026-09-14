# Phase Status

- Current stage: **Phase 5 in progress: native seven-level artifact audit passes; graceful lifecycle, guard-path/quality coverage and freeze remain open**
- Setup owner: Lâm Quang Huy
- Last updated: 2026-09-14

## Setup acceptance

- [x] Repository structure and operational docs created.
- [x] Python packaging, lint, typing, and test configuration created.
- [x] Credential paths excluded from Git.
- [x] Four repository-scoped Codex skills created.
- [x] Official Kaggle CLI skill installed and verified.
- [x] GitHub remote created and initial branch pushed.
- [x] Collaborator invitation sent to `minhb5d` with write access.
- [ ] `minhb5d` accepts the GitHub invitation and confirms clone access
  (deferred by the project owner; not a Phase 1 blocker).

## Phase 0 handoff

- [x] Research contract accepted by the project owner.
- [x] Four previously ambiguous design decisions frozen.
- [x] Phase 1 authorized on 2026-09-05.

Phase 1 may proceed on synthetic smoke data while collaborator acceptance is
pending. Held-out benchmark data must not be created or accessed in this phase.

## Phase 1 progress

- [x] Five shared contracts and A0 configuration frozen.
- [x] Backend-neutral runtime, strict parser, broker, logger, and eight tools.
- [x] Synthetic environment and 20 smoke tasks (10 Huy / 10 Minh).
- [x] Local Replay run: 20/20 success, 0 crash, 8/8 tool coverage.
- [x] Local Dummy run: 20/20 terminal states, 0 crash.
- [x] Unit/integration suite: 35 tests passing; package coverage 89%.
- [x] Minh cross-review deferred by explicit owner decision.
- [x] Real-model Kaggle run: 20/20 terminal, 0 crash, artifacts audited.
- [x] Trace audit: 262 schema-valid events and valid tool event ordering.
- [x] Credential-value artifact scan: 0 matches.
- [x] Frozen run manifest and artifact SHA-256 values recorded.

Phase 1 was **accepted on 2026-09-05**. The low A0 semantic score (3/20) is a
recorded limitation, not a completion blocker.

Follow-up audit reconfirmed the eight Phase 1 DoD gates on the smoke scope:
two independent Replay/Dummy CPU runs, normalized trace determinism, and all
eight frozen Kaggle artifact hashes. See `knowledge/integrity_audit_20260905.md`.
This is not a claim that every edge case has an individual regression test.

## Phase 2 progress

- [x] Phase 2 explicitly authorized on 2026-09-05.
- [x] 250 total / 150 Dev / 100 Test and category quotas retained.
- [x] Same-machine workflow recorded; review replaced by automated QA under the
  owner waiver without fabricated reviewer metadata.
- [x] Clean task/ground-truth/automated-QA schemas frozen.
- [x] Frozen synthetic environment built and validated.
- [ ] Pool acceptance: 250 schemas/oracle fixtures pass, but 30 same-instance
  pairs have different group IDs; review booleans are not independent QA evidence.
- [ ] Split acceptance: sealed hashes intact, but 12 semantic instances cross
  Dev/Test. Original v1 files are preserved, not repaired in place.
- [x] Dev-only Kaggle pilot completed without Test/private GT access.
- [ ] Phase 2 acceptance and release tag: blocked by benchmark-integrity defects.

The earlier Phase 2 acceptance claim is **withdrawn** after a static integrity
audit, not after a held-out model run. The Dev pilot remains historical execution
evidence (21 terminal, 0 crashes, 334 events); its 7/21 score is provisional
because argument comparators and typed fact semantics are incomplete.

Owner approved clean_v1.1 replacement and Dev experiments. Replacement progress:

- [x] Independent `data/clean/v1_1` with original v1 bytes preserved.
- [x] 250/250 executable QA, required arguments and all annotated alternative paths.
- [x] Cross-category group assignment: exact 150/100 quotas, no shared group or
  fact/evidence signature across splits; 50 robustness IDs selected before seal.
- [x] Typed numeric/date/set checks and SQL/calculator result equivalence with
  negative-control tests; no fabricated human review claims.
- [x] Public-only 21-task Dummy run and identity-safe checkpoint/resume tests.
- [x] Exact Git-bundle archive/expanded mount simulations, eight runtime tools,
  fault adapter, 21-task Dummy and missing-only resume in both layouts.
- [x] Kaggle v1 COMPLETE on first push: 21 terminal, 0 model errors, 318 valid
  trace events, 5/21 Dev diagnostic success; all checkpoint/input hashes audited.
- [x] Frozen evidence receipt, four credential-secret checks with zero matches.
- [x] Full Phase 2 closure: v1.1 acceptance recorded with the documented
  automated-QA owner waiver; no final Test experiment or Phase 3 start.

v1.1 dataset hash: `692ca92a214b0da87245ca7d11a074a74d416558f377bc448c125bd7d387be38`.
Do not move tasks or rewrite either frozen version. Language-quality review is
waived, not claimed to be proven by the structural tests. Low-level QA is not
equivalent to unrestricted language-quality review. Pilot evidence is in
`experiments/manifests/phase2_clean_v11_kaggle_v1.json`; audit hashes are in
`experiments/manifests/phase2_clean_v11_audit.json`.
The review waiver still applies; no peer review or new account is requested.

Phase 2 is accepted for the frozen synthetic benchmark under the owner waiver.
The pilot is Dev-only diagnostic evidence; held-out Test remains sealed and
must not be accessed without explicit scope. Phase 3 was subsequently authorized below.

## Phase 3 progress

**Accepted 2026-09-07 for adversarial_v2 under the owner self-review waiver.**
Source `c228a68`; [closure receipt](../../experiments/manifests/phase3_release_v2_closure.json)
and [acceptance summary](../benchmark/adversarial_release_v2_summary.md).
70 paired canonical scenarios, 350 attack/350 benign, five types, each branch
200 Dev/150 Test, 20 conservative groups. All 1,692 selected reference paths
re-scored/archived (280 canonical standard, 1,400 variant standard, 12 alternatives).
782 pre-seal tests pass; two seal-only tests skip. After seal: 132 tests pass,
650 construction tests excluded before import to protect frozen Test during
later development. Setup/Ruff/mypy 146 files, clean and adversarial seals pass.
Review is assistant self-review, not independent human review. Grouped output
strata remain 12/3; scenario count is not independent-mechanism certification.
Test seal binds data/environment/config/schema/mapping/source. No new model or
held-out inference; 732 Test-assigned reference paths were pre-seal construction.
Phase 4 was subsequently authorized below. The bullets preserve historical authoring stages.

- [x] Phase 3 explicitly authorized by the project owner on 2026-09-06.
- [x] Draft generator and deterministic integrity validator added.
- [x] Synthetic draft contains 70 families, 350 attack variants and 350
  matched benign controls (40 Dev families / 30 Test families).
- [ ] Semantic/security review and final freeze are pending; no model run or
  Test-driven tuning has occurred.
- [x] Strict identity/variant/pair validators, negative tests and a static draft
  audit are implemented; original v1 bytes preserved. The audit does **not**
  accept v1: template overlap, missing category strata, malformed webhook
  targets and surface/benign annotations require further authoring.
- [x] Offline mechanical surface helpers reject no-ops and preserve protected
  literals; candidates remain review-pending and have not regenerated v1.
- [x] Four separate unsplit workbench pairs pass 16 Replay fixtures with four
  reachable source types, safe utility, unauthorized email/webhook and final
  leakage checks. Public tasks/overlays/private oracles are separated; network
  interdiction and observable replay reproducibility tests pass (143 tests total).
- [x] Separate 12-pair unsplit candidate expansion (four adapted, eight new)
  passes 48 Replay fixtures, with offline SQL table/column scope and
  per-artifact destination/final grants. Balanced category/source counts,
  nine author-annotated template groups; 168 tests pass. See the
  [expansion receipt](../../experiments/manifests/phase3_candidates_v2_1_validation01.json).
- [x] Separate typed-utility/source-evidence sidecars retain 48 expected Replay
  outcomes. Pair/group audit examines all 66 combinations: nine provisional
  review units, not independent-family certification. Assistant authoring review
  notes identify wording/length/group issues; 220 tests pass. See
  [review QA receipt](../../experiments/manifests/phase3_candidate_review_v1_validation02.json).
- [x] v2.2 pilot revision preserves public/private oracle bytes and all reference
  objectives while revising attack/benign wording and conservative group labels.
  48 Replay scores match the parent; seven review units, length gates and
  mutation/network/reproducibility tests pass (244 tests total). See
  [revision receipt](../../experiments/manifests/phase3_canonical_revision_v22_validation01.json).
- [x] Separate eight-candidate mechanism batch passes 32 Replay fixtures for
  argument scope, call quota, prerequisites, query scope and complete Base64/hex
  disclosure. Genuine search exposure and multi-step paths use all eight tools.
  Combined pool: 20 candidates, 190 pair comparisons, 12 provisional review units;
  263 tests pass. See [batch receipt](../../experiments/manifests/phase3_mechanism_batch_v1_validation01.json).
- [x] Eight linked-source/row-scope candidates and unified active-pool QA pass:
  28 unsplit candidates, 112 fresh Replay paths (56 safe / 56 negative), 378
  pair comparisons and 14 provisional review units. Bounded row SQL remains
  offline; unsupported forms are unassessed, never implicitly safe. 297 tests
  pass; see [unified receipt](../../experiments/manifests/phase3_pool_v1_validation01.json).
- [x] Author self-review of the prior pool and twelve transaction/sink-position
  candidates added. Full pool: 40 unsplit candidates, 160 fresh Replay paths
  (80 safe / 80 negative), 780 comparisons and 15 conservative review units.
  321 tests pass; encoded subject/JSON-key leakage is tested independently of
  exact-message mismatch. See [v2 pool receipt](../../experiments/manifests/phase3_pool_v2_validation01.json).
- [x] Eight multi-step authorization-flow candidates compose existing scorers
  and source builders unchanged. Full pool: 48 unsplit candidates, 192 fresh
  Replay paths (96 safe / 96 negative), 1,128 comparisons and 15 conservative
  review units; 341 tests pass. Directional artifact/final grants and failed/late
  prerequisites are tested. See [v3 pool receipt](../../experiments/manifests/phase3_pool_v3_validation01.json).
- [x] Versioned mechanism-rule correction closes two demonstrated false-safe
  gaps without changing old data/scorers. 38 fresh Replay (32 standard plus
  six counterexample/control) and 160 reused standard paths pass bounded QA.
  Hash-bound assistant review retains 46 of 48 representatives and merges two;
  15 conservative groups remain. This is not final family admission. 367 tests
  pass; see [admission receipt](../../experiments/manifests/phase3_admission_v1_validation01.json).
- [x] Four query/fragment-disclosure pairs pass 16 fresh Replay paths and 34
  new tests (401 total). Reuse 192 hash-bound standard paths from prior evidence.
  Pool: 52 stored candidates, 50 retained representatives, two merges and 17
  conservative groups; not certified family independence or final admission.
  See [disclosure receipt](../../experiments/manifests/phase3_disclosure_v1_validation01.json).
- [x] Twelve task-effect pairs reuse frozen mechanism QA: 48 fresh Replay paths,
  208 reused standard paths, 428 tests pass (27 new). Pool: 64 stored candidates,
  62 retained representatives and 17 conservative groups. All twelve additions
  remain in the existing business group; final family admission is not certified.
  See [completion-authoring receipt](../../experiments/manifests/phase3_completion_v1_validation01.json).
- [x] Eight boundary pairs add bounded projection, final-policy, shared quota
  and designated-source revocation QA. 34 fresh Replay: 32 standard plus two
  safe alternatives; 256 standard paths reused. 466 tests pass (38 new).
  Pool: 72 stored/70 retained, two merges, 20 conservative groups; not final
  family admission. See [boundary receipt](../../experiments/manifests/phase3_boundary_v1_validation01.json).
- [x] Whole-pool canonical admission **for variant authoring**, under owner
  self-review waiver: 70 selected scenarios, two merged regression cases and
  exact 40 Dev/30 Test assignment preserving 20 conservative groups. All 17,429
  feasible assignments evaluated; category/source imbalance is explicitly
  reported (output-poisoning 12/3). 495 tests pass. Revalidate 288 prior reference
  records, 280 selected; no new Replay/model inference. See
  [selection manifest](../../experiments/manifests/phase3_canonical_selection_v1_validation01.json).
- [x] Full executable variant release, 350 attack/350 benign reviewed records,
  release mapping/integration and immutable Test seal accepted in adversarial_v2.
  Canonical authoring admission is not Phase 3 acceptance or certification of
  70 unrelated abstract mechanisms. See
  [Phase 3 handoff](../../knowledge/phase3_progress.md) and
  [audit receipt](../../experiments/manifests/phase3_draft_audit_20260906.json).
  New [workbench receipt](../../experiments/manifests/phase3_workbench_v2_validation_01.json)
  certifies fixture QA only; v1, clean inputs and measured releases are unchanged.

## Phase 4 progress

- [x] Owner explicitly authorized Phase 4 on 2026-09-07.
- [x] Prerequisites checked: clean/adversarial hashes intact; 50 robustness
  canonical IDs already sealed. New Dev validator does not parse Test payloads/GT.
- [x] Versioned raw/Unicode/security normalizer, raw preservation, operation
  hashes, descriptive features, explicit zero-width handling and idempotence.
- [x] Immutable JSON artifacts, run-isolated IDs, typed DAG links, ancestor
  queries, serialization and independent conservative sensitivity/trust joins.
- [x] 1,650 primitive checks on 150 clean Dev instructions/400 adversarial Dev
  payloads; 185 tests pass (53 new), setup/Ruff/mypy 151 source files pass.
- [x] ControlState, ContextBundle, pre/post/final pass-through hooks implemented.
- [x] Separate runtime: host source catalog, email/webhook field artifacts,
  context/model/final lineage, trace v2 and raw A0 exact-context/observable parity.
- [x] 65 paired CPU conditions: 20 smoke, 21 clean Dev reference-action scripts,
  24 attack/benign Dev source probes; 130 fresh Replay runs. No model/Test run.
  224 tests pass (39 new), setup/Ruff/mypy 156 files pass. Source `a65bc53`,
  [receipt](../../experiments/manifests/phase4_runtime_v1_validation01.json),
  [runtime contract](../architecture/phase4_runtime_contract.md). Clean/attack Dev
  final texts are plumbing probes, not utility/ASR measurements.
- [x] Host catalog v2: conservative search/DB collection labels, auxiliary sources;
  21 clean Dev + 24 deep paired Dev trajectories, 90 fresh Replay, all eight tools.
  152 deep source snapshots, 12 search envelopes, 120 sink fields checked.
- [x] Controlled overhead: 440 smoke Replay and two long-document stress runs;
  median added 5.539 ms, p95 11.749 ms; smoke traced peak 527,301 bytes. Guards pass.
- [x] 244 tests, setup/Ruff/mypy 160 files/knowledge-check pass; 153 source and
  1,625 raw hashes verified, 497 prior evidence hashes preserved. Dev stable
  summary matches preflight. Source `be7f8b5`,
  [closure receipt](../../experiments/manifests/phase4_closure_v1_validation01.json),
  [12-DoD report and limits](../architecture/phase4_report.md).

**Phase 4 accepted 2026-09-07 under owner self-review waiver.** No model inference
or security gate. Phase 5 needs explicit authorization. Replay does not measure
LLM utility/ASR. Collection/context lineage is conservative; log/content duplication
remains a measured long-context limitation, not a hidden claim of deduplication.
Frozen runtime/data/scorers unchanged; security normalization is not enabled in
A0. [Foundation contract](../architecture/phase4_foundation_contract.md).
Source `a4e9a87`; [Dev primitive receipt](../../experiments/manifests/phase4_primitives_v1_validation01.json)
matches its preflight stable summary; this earlier primitive receipt is historical.

## Phase 5 progress

- [x] Grouped package v3 independent CPU rehearsal (2026-09-14), source `0d86536`:
  complete 170-file worker, archive/generated-expanded fresh venvs, 128 package
  module origins each; eight tools/recovery, 21 clean Dummy and 112 grouped stub
  keys/resume per layout. 175 source/4,166 raw/16 kernel hashes independently match.
  [Receipt](../../experiments/manifests/phase5_grouped_package_v3_preflight01.json),
  [report](../evaluation/phase5_grouped_package_v3_report.md). Full repository QA
  passes 3,113 tests/one optional-tqdm skip (1,060.05s), setup/Ruff/mypy392/knowledge;
  555 source/seven raw/169 data hashes rechecked. No additional aggregate gate.
  [CPU QA receipt](../../experiments/manifests/phase5_grouped_package_v3_cpu01.json).
- [x] Grouped Dev CPU runner/checkpoint v1 (2026-09-14), source `354b75b`:
  all 112 variant+level keys across eight shards audited, immutable prefix resume,
  tampering/failure-retention controls. 27 focused tests; full 3,055 pass/1 optional
  native-tqdm skip (973.70s); setup/Ruff/mypy381/knowledge pass. 537 source/1,783 raw/
  169 data hashes rechecked. 106 tool results, 154 synthetic guard sidecars,
  192 GRACEFUL/reaped workers; no native/quality claim or additional aggregate gate.
  [Receipt](../../experiments/manifests/phase5_grouped_runner_v1_cpu01.json),
  [report](../evaluation/phase5_grouped_runner_v1_report.md). Native grouped adapter,
  exact package, GPU quality/lifecycle and Phase 5 freeze remain open.
- [x] Grouped native runner/auditor v2 topology and recovery contract prepared:
  44 focused routing/audit tests pass. The old compile/import receipts are retained,
  but exact package/import isolation is withdrawn: the overlay was nested below
  `configs` and an editable install supplied development modules. See the
  [correction](../evaluation/phase5_grouped_native_v2_report.md). Syntax compilation
  was not transitive-import or safe-extraction evidence. Native model output,
  timing/VRAM and grouped guard quality remain open.

- [x] Observed-shutdown package v2 exact offline preflight and CPU QA (2026-09-14):
  94-file overlay; archive/expanded mounts each pass eight tools/recovery, 21 public
  Dummy/missing-only resume and seven synthetic levels. 101 source/430 raw hashes
  re-audited. Full QA 2,764 pass/one optional-tqdm skip (693.35s), 24 focused tests;
  setup/Ruff/mypy 346 files/knowledge pass, 485 source/137 raw hashes match and
  169 data hashes unchanged. [Report](../evaluation/phase5_shutdown_package_v2_report.md).
  No native submission: a predeclared new lifecycle/tool/guard-path diagnostic,
  GPU evidence, guard quality/grouped Dev and formal Phase 5 freeze remain open.
- [x] Native observed-shutdown factory/runner/auditor v2 bounded CPU QA (2026-09-14):
  36 focused tests, full 2,740 pass/one optional-tqdm skip (719.76s); setup/Ruff/
  mypy 342 files/knowledge pass. 478 source/4,726 raw hashes re-audited, 169 data
  hashes unchanged. 15 actual synthetic runtime receipts and 70 mocked native-shaped
  records counted separately, no native model load. [Report](../evaluation/phase5_native_shutdown_wiring_v2_report.md).
  Exact package/release authentication, GPU diagnostic, quality and freeze remain open.
- [x] Observed-shutdown pair/runtime v3 bounded CPU integration (2026-09-14):
  both paired roles and A0/A1 use worker v2, separate startup/call identities,
  PID/config/lifecycle joins. 74 focused tests, 63 joined runtime receipts and
  four pair teardown fixtures; full 2,704 pass/one optional-tqdm skip (670.56s).
  Setup/Ruff/mypy 335 files/knowledge pass; 468 source/646 raw hashes re-audited,
  169 data hashes unchanged. [Report](../evaluation/phase5_pair_runtime_v3_report.md)
  and [receipt](../../experiments/manifests/phase5_pair_runtime_v3_cpu01.json).
  Native composition/package/GPU, guard quality and Phase 5 freeze remain open.
- [x] Standalone observed shutdown v2 CPU QA (2026-09-14): 80 focused tests
  (34 new/46 existing), full 2,630 pass/one optional-tqdm skip in 581.50s;
  setup/Ruff/mypy 331 files/knowledge pass. 462 source/677 raw hashes match,
  169 data hashes unchanged. Eight observed v2 cases and one v1 control reaped;
  two synthetic GRACEFUL cases do not establish native graceful cleanup.
  [Report](../evaluation/phase5_worker_shutdown_v2_report.md). ModelPair/runtime
  wiring was pending at that milestone and is covered by CPU v3 above; native
  diagnostic and production lifecycle acceptance remain open.
- [x] Native runtime technical pilot version 1 COMPLETE and artifact audit passed:
  205 raw/two remote files match, seven terminal/recovered levels; 12 native model
  loads and seven agent generations. Zero tool/guard calls and 12 TERMINATE/-15
  cleanups mean this does not close production lifecycle, guard quality or freeze.
  Release auditor QA: 2,596 tests pass/one optional tqdm skip; setup/Ruff/mypy/
  knowledge pass. [Native report](../evaluation/phase5_security_runtime_gpu_v1_report.md).
- [x] Native seven-level package CPU02 and exact offline preflight03 (2026-09-13):
  2,583 tests pass/one optional native-tqdm skip; 23 focused tests and
  setup/Ruff/mypy/knowledge pass. 456 source/2,859 raw hashes match and 169 data
  hashes unchanged. Both archive/expanded mounts pass public A0–A6 runtime,
  eight tools/recovery and 21-task Dummy/resume. Source `372d685`.
  [Package evidence](../../knowledge/phase5_security_runtime_probe_v1.md).
  No new native inference/quality acceptance from these CPU checks.
- [x] Owner explicitly authorized Phase 5 on 2026-09-07.
- [x] Pair/runtime v2 failure-evidence CPU validation (2026-09-13): real process
  death after a worker response preserves worker OK vs pair/host ERROR through
  event-bound proposals; failed startup retains elapsed and explicit completion.
  64 focused tests, 63 joined receipts; full 2,560 pass/one native-tqdm skip
  (551.55s), setup/Ruff/mypy 320 files/knowledge pass. 445 source/641 raw hashes
  match, 169 data hashes unchanged and all 971 prior CPU02 entries still match.
  [Report](../evaluation/phase5_pair_runtime_v2_report.md) and
  [receipt](../../experiments/manifests/phase5_pair_runtime_v2_cpu01.json).
  This extends bounded CPU coverage, not native GPU/quality/freeze acceptance.
- [x] Task-owned ModelPair/runtime v7 bounded CPU integration (2026-09-13):
  A0/A1 agent-only; A2–A6 parent-owned role adapters with two sibling workers,
  dedicated pair trace schema and host-proposal/transport-attempt ledger.
  52 focused tests, seven exact v7 parity comparisons and 51 joined task receipts;
  full QA 2,496 pass/one native-tqdm skip (477.43s), setup/Ruff/mypy 317 files
  and knowledge checks pass. 441 source/530 raw hashes independently match;
  169 tracked data hashes unchanged. [Report](../evaluation/phase5_pair_runtime_report.md)
  and [CPU02 receipt](../../experiments/manifests/phase5_pair_runtime_v1_cpu02.json).
  CPU01 is development history, superseded for a trace-schema mismatch; its
  bytes are preserved. This is not native fault coverage/model quality or freeze.
- [x] Corrective runtime v7/components v2 CPU validation (2026-09-13): clause-bound
  grants, canonical host validation, mixed raw/normalized final screening, paired
  A4 table/column scope integrated at A4–A6, level-correct metadata and bounded
  synthetic student-ID extraction. 91 focused tests; full QA 2,444 pass/1
  native-tqdm skip, setup/Ruff/mypy 314 files/knowledge pass. 28 exact Replay
  pairs and 69 focused runtime records; 436 source/573 raw hashes re-audited,
  169 tracked data hashes unchanged. [Report](../evaluation/phase5_remediation_v2_report.md)
  and [receipt](../../experiments/manifests/phase5_remediation_v2_cpu01.json).
  Working-tree CPU QA only, not a clean-source/model release or Phase 5 acceptance.

**Audit correction:** the entitlement v1 receipt's actual pytest log does not
match its recorded hash. Reliance on its integrity claim is withdrawn; old
bytes remain untouched. v1 entitlement/runtime v6 also have confirmed behavioral
defects and are historical reproduction targets, not recommended new-run code.
The historical milestones below do not override the corrective report above.

- [x] Cumulative A0–A6 config matrix, strict config/decision/public-observation
  schemas and first [policy contract](../architecture/phase5_policy_contract.md).
- [x] A1 raw/normalized detector, bounded raw-user destination authorization,
  sticky source signals and A0/A1 Broker adapter; denied proposals never execute.
- [x] A2 interface preparation: versioned prompt, strict JSON parser, cache
  identity and error semantics. Replay/fake-backend tests only, not a real guard run.
- [x] 56 synthetic micro-tests / 300 full tests pass; setup/Ruff/mypy 166 files
  pass. 153 Phase 4 source hashes preserved; new validator uses hash-only Test checks.
  Source `4bddd23`; [component receipt](../../experiments/manifests/phase5_components_v1_validation01.json).
- [x] Shared instrumented A0/A1 ReAct loop with raw context/action/field/final
  lineage, source-native detector input, denial feedback and proposal/call separation.
  20 exact A0 parity pairs against Phase 4, 24 synthetic A0/A1 conditions;
  64 fresh Replay runs. 366 tests pass (66 new), setup/Ruff/mypy 170 files pass.
  Source `d2ec2d5`, [runtime receipt](../../experiments/manifests/phase5_runtime_v1_validation01.json),
  [runtime contract](../architecture/phase5_runtime_contract.md). 120 source/369 raw
  hashes verified; 270 prior source hash entries preserved; preflight summary matches.
- [x] Versioned A0/A1/A2 runtime and process-bounded guard adapter. Preflight:
  446 tests (80 new), setup/Ruff/mypy 175 files pass; 40 A0/A1 exact smoke pairs
  + nine synthetic A2 conditions = 89 Replay runs, 31 fake guard classifications.
  Timeout/terminate/kill/reap, cache retirement, sticky errors, cumulative A1,
  source/action trace linkage tested. 390 prior source entries remain unchanged.
  Source `15ed921`, [selected receipt](../../experiments/manifests/phase5_a2_v2_validation01.json)
  matches preflight; 124 source/548 raw hashes verified.
  [A2 contract](../architecture/phase5_a2_runtime_contract.md).
- [ ] A2 production guard model/revision, efficient GPU lifecycle and actual Dev validation.
- [x] Cumulative A3 sensitivity, A4 bounded destination/action authorization and
  A5 joint-session enforcement in separate runtime v3. 593 tests pass (147 new),
  setup/Ruff/mypy 179 files/knowledge-check pass. 44 A0–A2 parity pairs + 30
  synthetic session conditions = 118 Replay runs. Session cases: 165 fake guard
  classifications, 225 state snapshots, 15 expected denials (not benchmark ASR).
  514 prior source entries unchanged; preflight records 127 source/780 raw hashes.
  Source `8a4ca3d`, [selected receipt](../../experiments/manifests/phase5_session_v1_validation01.json)
  matches preflight; all 127 source/780 raw hashes verified.
  [Session contract](../architecture/phase5_session_contract.md).
- [x] Bounded A6 typed value-origin index and deterministic final-release components,
  separate from the runtime. 696 tests pass (103 new), setup/Ruff/mypy 183 files
  and knowledge checks pass. 24 synthetic conditions: 12 ALLOW/8 REDACT/4 DENY;
  zero fresh Replay/model/guard runs. Source `3b9f565`,
  [selected receipt](../../experiments/manifests/phase5_value_origin_v1_validation01.json)
  from clean source matches preflight; 130 source/101 raw hashes verified,
  641 prior source entries unchanged. Transformed roots rejected; empty normalized
  protected values fail closed. [Component contract](../architecture/phase5_value_origin_contract.md).
  A6 remains disabled in runtime; this is not complete FinalGate or benchmark ASR.
- [ ] A4 general processing-scope controls beyond bounded external authorization.
- [x] Value PreGate/Post-view components: preflight 769 tests (73 new), setup/
  Ruff/mypy 186 files/knowledge pass. 24 Pre cases (4 ALLOW/20 DENY) and six
  Post cases; four existing Broker mock calls, zero model/guard/Replay runs.
  Bidirectional observed-source/index coverage blocks omitted protected sources;
  771 prior source entries unchanged, 132 source/121 raw hashes recorded.
  [Gate contract](../architecture/phase5_value_gates_contract.md). Source `a3743a2`,
  [selected reproduction](../../experiments/manifests/phase5_value_gates_v1_validation02.json)
  from clean source matches preflight; 769 tests pass, 132 source/121 raw hashes verified.
- [x] Bounded A6 runtime v4 Pre/Post/Final integration: 845 tests pass (76 new),
  setup/Ruff/mypy 190 files/knowledge pass. 26 synthetic runtime conditions +
  12 exact A0–A5 parity pairs = 50 fresh Replay; 56 Broker mock calls and 121
  fake guard classifications. 135 source/435 raw hashes verified; 903 prior
  source entries unchanged. Coarse sensitivity refinement retains rule/LLM vetoes;
  actual Post context views, separate proposed/released final and fixed S0 host
  final policy. [Runtime contract](../architecture/phase5_a6_runtime_contract.md).
  Source `04ae4c8`, [selected receipt](../../experiments/manifests/phase5_a6_runtime_v1_validation01.json)
  from clean source matches preflight; 845 tests pass and all 135 source/435 raw
  hashes verified. Not real-model security evidence.
- [x] Bounded host-only A4 processing-scope component v1: 14 deterministic
  synthetic conditions and 21 focused tests cover exact raw-user resource/table
  anchors, untrusted scope expansion, unassessed search/SQL, trusted pass-through,
  delegated sinks, unknown actions, state monotonicity and bounds. Full QA:
  2,327 pass / 1 intentional native-tqdm skip; setup/Ruff/mypy/knowledge pass.
  [Contract](../architecture/phase5_processing_scope_contract.md),
  [report](../evaluation/phase5_processing_scope_v1_report.md),
  [release manifest](../../experiments/manifests/phase5_processing_scope_v1_validation01.json).
  This is a
  component milestone only; it is not runtime adoption or private-final
  entitlement and does not close the general A4 gate.
- [ ] General private-record final entitlements and broader origin-coverage assessment.
- [x] Bounded host-only private-record final-entitlement component v1: 12 deterministic
  synthetic conditions and 17 focused tests cover affirmative raw-user final clauses,
  exact resource/table/value-type binding, trusted-origin release, wrong-source/type and
  untrusted redaction, normalized-only/incomplete-coverage denial, and hash binding.
  Selected clean-release QA: 2,333 pass / 13 intentional optional/native skips;
  setup/Ruff/mypy/knowledge pass.
  [Component contract](../architecture/phase5_final_entitlements_contract.md) and
  [release report](../evaluation/phase5_final_entitlements_v1_report.md), with
  [selected manifest](../../experiments/manifests/phase5_final_entitlements_v1_validation01.json).
  This is a
  host-only component milestone; runtime A0-A6 adoption, broader origin coverage,
  semantic completeness and the general private-final gate remain open.
- [x] Bounded `security_runtime_v6_entitlement_adapter`: 10 deterministic
  synthetic runtime conditions and 25 focused runtime/entitlement tests cover
  trusted explicit/auto extraction, redaction, wrong-source/untrusted and
  normalized-only denial, public no-match, parse terminal, A0 pass-through and
  host hash rejection. Selected clean-release QA: 2,341 pass / 13 intentional
  optional/native skips (preflight 2,353/1); setup/Ruff/mypy/knowledge pass.
  [Contract](../architecture/phase5_runtime_v6_entitlement_contract.md),
  [report](../evaluation/phase5_runtime_v6_entitlement_v1_report.md) and
  [selected manifest](../../experiments/manifests/phase5_runtime_v6_entitlement_v1_validation01.json).
  This
  adapter milestone does not close runtime production guard/GPU, broader A4 or
  grouped Dev/freeze gates.
- [x] Task-local warm guard and v5 runtime: 891 tests pass (46 new), setup/Ruff/
  mypy 194 files/knowledge pass. 22 cold/warm parity pairs = 44 Replay plus nine
  lifecycle conditions; 140 mock Broker calls and 240 fake guard classifications
  in the runtime matrix. 138 source/370 raw hashes verified, 1,038 prior source
  entries intact. Paired worker starts 53 cold / 18 warm; not GPU performance.
  Deadline, identity/cache retirement, graceful/forced cleanup and terminal/
  exception close verified. [Contract](../architecture/phase5_warm_guard_contract.md).
  Source `2300751`, [selected receipt](../../experiments/manifests/phase5_warm_guard_v1_validation01.json)
  from clean source matches preflight; 891 tests pass, 138 source/370 raw hashes
  and 53/18 worker starts rechecked. Actual guard model/GPU validation stays open.
- [ ] Grouped Dev tuning/validation protocol, differential experiments and freeze.

- [x] Separate offline guard HF adapter CPU preflight: 942 tests pass (51 new),
  setup/Ruff/mypy 197 files/knowledge pass; 134 source hashes and 1,176 prior
  entries verified. Content-bound snapshot identity, local-only native FP16
  single-device loading, allocator/context budgets, fresh generation config/cache
  and text-free metrics. [Contract](../architecture/phase5_guard_hf_contract.md).
  Candidate upstream revision verified, but weights not acquired/authenticated;
  no real HF/CUDA or agent/guard coexistence evidence. Source `bc2023f`,
  [selected receipt](../../experiments/manifests/phase5_guard_hf_v1_validation01.json)
  matches preflight from clean source: 942 tests in 228.14 seconds;
  all 134 source/six raw log hashes verified. Phase 5 acceptance remains open.

- [x] Guard-only GPU technical execution: first kernel v1 COMPLETE, two T4,
  offline pinned Qwen 1.5B, four schema-valid calls and matching A hashes.
  Exact source/bootstrap/artifact checks and 21 Dummy/84 trace events verified.
  [Report](../evaluation/phase5_guard_gpu_v1_report.md),
  [audit](../../experiments/manifests/phase5_guard_gpu_v1_audit01.json).
  Cold request 47.895/32.814 s; warm 0.956/0.991 s; peak allocated 2.898 GiB.
  **Not quality acceptance:** B classified SAFE; all A/B responses identical.
  Both workers reaped only after TERMINATE/-15. V1 graceful-cleanup audit fails;
  [post-run v2 interpretation](../evaluation/phase5_guard_gpu_audit_deviation.md)
  reports integrity and failed graceful cleanup separately. No semantic retry.

- [x] Separate cancellation-only GPU v1 COMPLETE on first submission, no model
  generation or semantic retry. Three fresh workers, resident3.047GiB, all18
  recovery samples returned to baseline. TERMINATE/-15 for normal close/busy
  timeout; SIGTERM-ignore escalated to KILL/-9. Normal closure still not graceful.
  [Report](../evaluation/phase5_guard_cancellation_v1_report.md),
  [audit](../../experiments/manifests/phase5_guard_cancellation_v1_audit01.json).
  1,087 tests pass; setup/Ruff/mypy213files pass; two audits byte-identical,
  67 raw/134 frozen source hashes verified. No agent resident, quality evaluation
  or Test payload access. Recovery is bounded technical evidence, not Phase5 closure.

- [x] CPU-only dual-GPU placement admission: explicit candidate20/8layer map,
  separate agent12/7GiB and guard5GiB caps, context/geometry/tensor-placement
  rejection. 1,143 tests pass,56new; setup/Ruff/mypy215files/knowledge pass.
  [Contract](../architecture/phase5_coexistence_placement_v1_contract.md),
  [CPU receipt](../../experiments/manifests/phase5_placement_v1_validation01.json)
  reproduced twice byte-identically from source2f311bb. No budget-enforcing
  agent HF loader, authenticated agent weights or combined GPU run yet;
  analytical estimates are not measured peaks or model selection.

- [x] One read-only Kaggle CPU model-mount diagnostic completed with full-inventory
  rejection preserved:11/11runtime files, including four Qwen7B shards, match
  pinned HF publisher hashes; only README differs. No local weights download,
  model loading, inference or GPU use. [Report](../evaluation/phase5_agent_mount_v1_report.md).
  Source/remote metadata audited, two audits byte-identical;1,187tests pass,
  setup/Ruff/mypy218files/knowledge pass. Full mount is not admitted for loading;
  runtime-input admission and budgeted agent loader remain separate next steps.

- [x] Separate runtime-input admission and budgeted agent HF adapter CPU QA:
  1,274tests pass,87new; setup/Ruff/mypy221files/knowledge pass. Live hash/339tensor
  header checks,12/7GiB allocator caps, fixed20/8layer map, context rejection and
  text-free metrics implemented with CPU fakes. Sourcefa894c4 reproduces saved
  hash admission twice byte-identically. [Report](../evaluation/phase5_agent_loader_v1_report.md).
  Original README/full-inventory rejection retained. No real header/model load,
  combined GPU run or production supervisor; GPU compatibility/fit remain unproven.

- [x] Separate sibling agent/guard supervisor and durable small-context probe:
  1,330tests pass,56new; setup/Ruff/mypy224files/knowledge pass. Real spawn tests
  verify agent-first readiness, cold/warm deadlines, sibling cleanup and KILL
  escalation. Two clean-source6d1c761 CPU rehearsals have matching summaries,
  four workers reaped,15raw files/run retained with distinct PID/timing hashes.
  [Report](../evaluation/phase5_model_pair_v1_report.md). Memory/inference are
  synthetic here; no HF entry point/exact GPU bundle, actual coexistence or v5
  runtime integration yet. Prior GPU graceful-close failure remains unchanged.

- [x] HF pair entry point and exact bounded Kaggle wrapper prepared: sourceb76c040,
  1,352tests/328.89s pass,22new; setup/Ruff/mypy229files/knowledge pass. Both
  isolated archive/expanded PAX layouts pass8tools,21Dummy/resume and synthetic
  pair/recovery. Native Transformers5.5 two-buffer compatibility uses separate
  adapter v2; prior146source entries stay frozen. [Pre-submit QA](../../experiments/manifests/phase5_pair_gpu_v1_pre_submit_qa01.json).
  Actual pair GPU residency/inference is not yet measured at this milestone.

- [x] First combined real-model GPU technical probe COMPLETE, one submission:
  Qwen7B/guard1.5B resident deltas9.799/7.621GiB across twoT4; two small calls
  warm1.906/1.788s. Six recovery samples residual0bytes on both devices. Both
  workers TERMINATE/-15/reaped, not graceful.62raw files,21Dummy/84events,
  source/inputs/request/metrics inspected; two evidence inspections byte-identical.
  [Report](../evaluation/phase5_pair_gpu_v1_report.md). No maximum-context stress,
  combined busy-cancellation, v5 pair integration or guard quality selection yet.
  Release QA1,363tests/339.69s, setup/Ruff/mypy230files/knowledge pass;
  [QA receipt](../../experiments/manifests/phase5_pair_gpu_v1_release_qa01.json).

- [x] Separate combined cancellation CPU protocol/suite implemented: three fresh
  pairs exercise agent busy, guard busy and guard SIGTERM-ignore timeout. Two
  clean-source5d326bf rehearsals pass;12workers reaped,44raw files/run, matching
  stable summaries with genuine distinct PID/timing bytes.1,389tests/356.32s
  pass,26new; setup/Ruff/mypy231files/knowledge pass. [Report](../evaluation/phase5_pair_cancellation_v1_report.md).
  CPU uses synthetic backends/memory only. No new GPU run, native generation
  cancellation, maximum-context evidence or production pair integration.

- [x] Combined cancellation GPU technical scope verified, first submission COMPLETE:
  three fresh pairs, six HF loads and zero model generation calls. All six workers
  reaped (five TERMINATE/-15, one KILL/-9), zero graceful exits; all18recovery
  samples residual0bytes on both T4 GPUs.91raw files and21Dummy/84events audited;
  two audits byte-identical. Full QA1,430tests/353.52s,24new audit tests;
  setup/Ruff/mypy236files/knowledge pass. [Report](../evaluation/phase5_pair_cancel_gpu_v1_report.md),
  [QA](../../experiments/manifests/phase5_pair_cancel_gpu_v1_release_qa01.json).
  Shutdown warning3semaphores retained; IPC cleanup is unverified. Busy CUDA loops
  with resident weights do not prove native-generation cancellation, maximum-
  context fit or production integration. No quality or full Phase5 acceptance.

- [x] Separate IPC-origin GPU diagnostic COMPLETE, one submission;99raw files
  verified and audits03/04 reproduce the selected audit byte-identically.
  Three unmatched registrations trace to tqdm's default multiprocessing RLock
  in forced busy workers;90owner and3idle registrations were unregistered.
  All six process exits still forced (5TERM/1KILL), zero graceful exits.
  18VRAM samples returned to baseline; no global IPC/driver-clean claim.
  Source9087791/pre-push31910cb, full pre-submit QA1,481tests/359.83s.
  [Evidence clarification](../evaluation/phase5_pair_ipc_gpu_v1_review_addendum.md),
  [selected audit](../../experiments/manifests/phase5_pair_ipc_gpu_v1_audit01.json).
  This historical run did not apply prevention; the separate validation follows.

- [x] Pair-progress GPU v1 COMPLETE, one submission; exact 17-file overlay,
  pinned private/offline T4 inputs, source `a1a90b3` and pre-push `f8ab56d`.
  106 raw hashes verified, audits/reports01/02 byte-identical. Six policy receipts
  bind PID and native tqdm implementation; zero observed child registrations,
  owner90/90, no unmatched entries or shutdown semaphore warnings. Six HF loads,
  zero generation;18VRAM samples residual0bytes both GPUs. Five TERM/one KILL,
  zero graceful exits: creation-path prevention passes, not global IPC cleanup.
  [Report](../evaluation/phase5_pair_progress_gpu_v1_report.md),
  [selected audit](../../experiments/manifests/phase5_pair_progress_gpu_v1_audit01.json).
  Pre-submit QA1,517pass/1optional native skip; exact native preflight ran both
  layouts. Context geometry CPU adds35tests, full QA1,552pass/1skip; native
  maximum-context runner/GPU stress, runtime integration and Dev gates remain.

- [x] Native generation-policy library compatibility CPU v1 COMPLETE, one
  submission; worker source `5c0c20e`, pre-submit GitHub `c3bf60f`. Actual pinned
  Transformers5.5.0/Torch2.10.0+cu128 config/special-token/length functions pass
  two success and two injected error/interruption controls with hook restoration.
  Remote source/metadata and68raw files authenticated; two audits byte-identical.
  Zero weights/model.generate/GPU; configured lengths are not cache allocation
  measurements. Full QA1,743pass/1optional skip375.60s;34newfocused tests pass.
  [Report](../evaluation/phase5_policy_native_cpu_v1_report.md),
  [selected audit](../../experiments/manifests/phase5_policy_native_cpu_v1_audit01.json).
  Publisher-metadata authentication, combined stress packaging and native GPU
  context execution remain open, as do runtime and grouped Dev acceptance gates.

- [x] Owner-approved efficient model context stress v1 COMPLETE, one submission:
  source5267218/pre-pusha66514e, exact42-file archive/expandedPAX package.
  Full QA1,931pass/1optional skip389.21s;72focused post-download tests pass.
  90raw/2remote files authenticated, two independent audits byte-identical.
  Agent4096+512/guard4096+128 and full KV4608/4224 across all28layers pass,
  unchanged models/FP16/placement/caps/deadlines/publisher policy, no OOM.
  Four actual efficient dispatch samples, all-call flags/geometry guards and
  native state restoration verified. Two TERM/-15/reaped,0graceful, six VRAM
  recovery samples residual0bothGPU; no global IPC claim or benchmark adoption.
  [Report](../evaluation/phase5_efficient_stress_gpu_v1_report.md),
  [audit](../../experiments/manifests/phase5_efficient_stress_gpu_v1_audit01.json).
  Prior factory/OOM runs remain immutable; normal-request runtime integration,
  A4/general final, grouped Dev differential/model choice/freeze remain open.

- [x] Native ordinary A/B/A technical milestone: new private kernel
  `huylmhuhu/react-vn-ordinary-pair-t4x2-v1` completed with explicit
  `NvidiaTeslaT4`. Source/package/remote metadata and 132 raw files were
  independently authenticated; 21/21 Dummy, two native model loads, 6/6
  native calls, two-device residency and six zero-residual recovery samples
  passed. A repeat hashes matched for both roles; both workers were reaped by
  `TERMINATE/-15` and graceful cleanup remains unproven. Full QA is 2,307 pass/
  1 optional skip, setup/Ruff/mypy 303 files and knowledge-check pass. This is
  technical evidence only: no quality/ASR/Test inference and `phase5_accepted`
  remains false. See [release audit](../../experiments/manifests/phase5_ordinary_pair_t4x2_v1_audit01.json),
  [release QA](../../experiments/manifests/phase5_ordinary_pair_t4x2_v1_release_qa01.json)
  and [report](../evaluation/phase5_ordinary_pair_t4x2_v1_report.md).

Phase 5 is not accepted. Seven config files do not mean seven operational levels.
The first host adapter and A0/A1 v1 runner remain immutable historical milestones.
The current v5 loop supports A0–A6 with an explicitly task-owned warm guard for
A2–A6; frozen v4 remains the cold-worker reference. V3 still rejects A6. A3–A5
use coarse state/final pass-through; v4/v5 A6 return gated released finals.
First-request process startup/model load is included in elapsed guard duration;
warm requests and task cleanup are separately recorded. Four synthetic guard GPU
calls are now audited; no benchmark model Dev/Test inference has been added in Phase 5.

## Authorized Dev pilot extension

- Three-model comparison authorized: historical Qwen + Gemma + Llama on the
  same 21 clean_v1.1 Dev tasks. See `knowledge/multimodel_dev_pilot.md`.
- Owner subsequently selected Gemma 4 E4B IT and Qwen2.5 7B Instruct with a
  predeclared performance protocol. Google access is resolved.
- Both measured GPU kernel v1 runs completed: 21 terminal tasks each, zero
  model errors, exact artifact/input/source audits passed. Gemma 4 strict Dev
  success 6/21; Qwen 7B 3/21. No semantic retries or held-out inference.
- [Audited report](../evaluation/measured_dev_pilot_report.md) includes paired
  uncertainty, latency, throughput, memory and failure diagnostics. These are
  small selected Dev results, not final thesis results or a backbone selection.
- Llama remains not run pending Meta access. The measured two-condition pilot
  is complete; the three-family comparison is not. Phase 3 acceptance is recorded above.
