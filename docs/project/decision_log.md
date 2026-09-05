# Decision Log

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
