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
