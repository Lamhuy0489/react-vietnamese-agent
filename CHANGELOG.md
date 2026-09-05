# Changelog

## Integrity audit — 2026-09-05

- Withdraw Phase 2 acceptance: 30 same-instance pairs were missed by the local
  fact-label signature; 12 cross Dev/Test. No release tag created.
- Preserve sealed v1 inputs and raw model artifacts; require approval for a
  separately versioned replacement, not an in-place reseal.
- Add cross-category screening, complete component/aggregate hash checks,
  pre-write seal guards, and invalid-benchmark bundle rejection.
- QA flags are not proof that checks ran; Dev pilot 7/21 is provisional TSR.
- Re-audit Phase 1 smoke DoD/eight Kaggle hashes; strengthen trace validation
  with synthetic regression tests. No new inference or runtime changes.

## clean_v1.0 — 2026-09-05

Historical creation record; acceptance/QA claims below are superseded by the
integrity audit above.

- Added typed public task, private ground-truth, oracle, fault, and owner-review
  contracts.
- Built `clean_env_v1` with 50 documents, 25 cached pages, and eight SQLite
  tables using synthetic data only.
- Authored the complete 250-task pool with exact category quotas and a balanced
  125/125 owner allocation.
- Replaced independent cross-review with the explicitly approved same-machine
  automated QA + project-owner acceptance workflow; no fake reviewer metadata.
- Validated all 250 oracles through Tool Broker and accepted 24 fuzzy lexical
  candidates only after distinct semantic signatures were confirmed.
- Created the seed-2026 group-wise split: 150 Dev and 100 held-out Test.
- Sealed benchmark components and recorded Test/environment checksums before any
  Dev model pilot.
- Added a Kaggle public-Dev-only pilot workflow that excludes Test and all
  private ground truth from the worker bundle.
- Accepted Kaggle kernel v2 evidence: 21/21 terminal Dev runs, zero crashes,
  334 valid trace events, and 7/21 strict task successes. Kernel v1 failure and
  the fault-adapter fix are retained in the evidence manifest.

No rejected task was carried into the frozen dataset. The generator history and
QA reports preserve the reproducible transformation from pool to split.
