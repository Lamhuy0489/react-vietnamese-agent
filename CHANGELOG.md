# Changelog

## clean_v1.0 — 2026-09-05

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

No rejected task was carried into the frozen dataset. The generator history and
QA reports preserve the reproducible transformation from pool to split.
