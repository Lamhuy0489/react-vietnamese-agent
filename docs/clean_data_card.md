# Clean Benchmark v1 Data Card

## Intended use

This synthetic Vietnamese benchmark measures baseline ReAct capability:
retrieval, argument construction, multi-step sequencing, clarification,
recovery, no-tool behavior, and benign mock-sink use. It is research data for
this repository, not a production university dataset.

## Data and environment

- 250 tasks: 150 Dev and 100 held-out Test.
- Seven categories with exact frozen quotas.
- 50 documents, 25 cached pages, eight SQLite tables.
- Synthetic people, identifiers, addresses, policies, and facts only.
- Reserved `.invalid` domains and mock endpoints; no live network dependency.
- Public task and private ground-truth files are separate.

## Collection and annotation

Tasks were deterministically authored by Codex under the approved project
contract. The original team allocation is retained as 125 records assigned to
Huy and 125 to Minh, with both represented in every category. This allocation
does not claim that two humans independently authored the generated records.

Because Huy and Minh share one machine, the owner explicitly waived independent
cross-review. All 250 records passed the ten-point automated QA protocol. The
review log therefore uses `automated_checks_owner_waiver`, records the automated
gate rather than a person, and never names a fabricated reviewer. This is a material limitation: the benchmark has
reproducible QA, but no independent human review coverage.

## Quality evidence

- Schema: 250/250 public tasks and 250/250 private records valid.
- Ground truth: 250/250 records complete.
- Oracle solvability: 250/250 accepted; 1,407 observable broker trace events.
- Exact normalized duplicates: 0 groups.
- Accent-insensitive duplicates: 0 groups.
- Fuzzy queue: 24 lexical pairs at token Jaccard ≥ 0.90; all have distinct
  semantic signatures (facts/evidence/missing slots) and are retained.
- Tool task coverage: document search/read 120 each, database 85, cached
  search/fetch 29 each, calculator 40, email mock 8, webhook mock 8.
- Split overlap: 0 task IDs, 0 instance groups, 0 semantic signatures.
- Source/entity overlap: 45 shared evidence IDs, reported rather than hidden;
  the split isolates task instances, not every environmental entity.

## Held-out Test policy

Test was sealed before the Dev pilot. Its public file, private ground truth,
environment, schema, and review log are covered by the benchmark manifest.
Test must not drive prompt, policy, architecture, threshold, or model choices.
The Kaggle inference bundle is allowlisted and contains public Dev only: no Test,
pool, review log, or private ground truth.

## Known limitations

- No independent human review under the owner-approved same-machine workflow.
- Synthetic university language may not represent production distributions.
- Shared environment sources appear across Dev and Test, although semantic task
  signatures and instance groups do not overlap.
- A small 3B baseline may have low semantic task success; model quality is not a
  dataset acceptance criterion.
- Near-duplicate disposition is deterministic semantic-signature QA, not human
  linguistic judgment.

## Baseline Dev pilot

The Qwen2.5-3B-Instruct Kaggle v2 pilot used 21 public Dev tasks (three per
category): 21/21 terminal, 17 completed, zero model crashes, one parse failure,
three max-step exits, 334 valid trace events, and 7/21 strict task successes.
These are baseline diagnostics, not benchmark selection or Test results.

## Reproducibility

Run `python scripts/validate_clean_environment.py`,
`python scripts/validate_clean_pool.py`, and
`python scripts/validate_clean_split.py`. Frozen hashes and seed 2026 are stored
under `data/clean/v1/manifests/` and `data/clean/v1/checksums/`.
