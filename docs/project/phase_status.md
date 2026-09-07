# Phase Status

- Current stage: **Phase 5 in progress: A2 bounded-process integration verified on synthetic QA**
- Setup owner: Lâm Quang Huy
- Last updated: 2026-09-07

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

- [x] Owner explicitly authorized Phase 5 on 2026-09-07.
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
- [ ] A3–A5 session enforcement and A6 value-origin Pre/Post/Final policies.
- [ ] Grouped Dev tuning/validation protocol, differential experiments and freeze.

Phase 5 is not accepted. Seven config files do not mean seven operational levels.
The first host adapter and A0/A1 v1 runner remain immutable historical milestones.
The new v2 loop supports A2 with an explicit process-owned backend factory; A3–A6
are rejected. Cold process startup/model loading is included in guard duration,
not warm inference throughput. No new real model/benchmark Dev/Test inference.

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
