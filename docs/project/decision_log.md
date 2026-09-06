# Decision Log

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
