# Decision Log

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
