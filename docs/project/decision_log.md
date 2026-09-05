# Decision Log

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
