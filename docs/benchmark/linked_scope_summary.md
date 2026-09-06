# Linked-source / row-scope batch and unified QA

2026-09-06. Scope: unsplit synthetic authoring, not a benchmark release.

Eight new pairs bring the active pool to **28 candidates**, not 28 approved
families. Four row cases intentionally share one conservative group. Three
linked cases join existing document-read, sink-artifact and recipient groups;
one adds a cached-page-read group. Combined audit: 378 pair comparisons and
14 provisional review units, not a semantic-independence certificate.

## Assistant author self-review

| Candidate | Distinct scenario / prohibited effect | Safe utility evidence |
|---|---|---|
| rowdirect | Explicit additional record lookup | Time in the authorized row |
| rowlist | Add a record to a batch IN predicate | Quantity in the authorized row |
| rowwide | Remove a single-record filter | Date in the authorized row |
| rowretry | Forged stale-record recovery lookup | Room in the authorized row |
| linkdoc | Cached index induces extra document access | Quantity from the authorized document |
| linkpage | Document induces an extra cached-page hop | Time from the authorized cached page |
| linkmail | Join read-only internal artifact into an authorized public email | Public room plus exact permitted send |
| linkroute | Cached route notice substitutes an email destination | Document room plus exact permitted send |

Each pair shares the same public task, auxiliary sources, grants and utility.
Only the primary lower-trust addition differs. Attack requests the extra read,
disclosure or destination change; benign describes the existing task without
requesting that prohibited behavior. Benign/attack whitespace-word ratios are
1.00–1.12. Self-review and automated QA are not independent human approval.
Canonical approval remains pending until the whole-pool review is consolidated.

## Verification

The unified verifier reruns all three current batches: **112 Replay** paths,
56 safe with typed utility and source evidence, 56 negative controls. No
unassessed reference actions. These are scripted fixtures, **not model runs**,
ASR, FPR or real-model safety results.

Full suite: **297 tests pass**, including 34 new parametrized cases; setup,
Ruff and mypy (119 source files) pass. clean_v1.1 validates sealed-read-only.
Seven previous receipts were cross-checked: **347 hash entries match**, including
the twelve measured model-release artifacts. No old data/source/score changed.

Tests exercise supported/unsupported SQL, bound escaped literals, key schema
and null handling, failed attempted reads, overlapping column/row violations,
source isolation, identity mismatches, network interdiction and normalized
trace reproducibility. Row assessment reads only keys in a read-only evaluator
connection. Runtime still uses the unchanged eight-tool Broker and A0.

Selected execution receipt:
`experiments/manifests/phase3_pool_v1_validation01.json`.
The receipt records base Git identity, exact source/input hashes, per-path
scores and trace hashes. Raw traces/environments remain ignored under results.

## Remaining Phase 3 gates

The verifier deliberately reports `qa_valid: true`, `phase3_accepted: false`.
With `--require-acceptance`, pending acceptance produces exit 2 after saving
the QA report. It cannot turn green merely because fixtures ran successfully.

The pool is short by 42 candidates before semantic acceptance, lacks a reviewed
40/30 grouped split, 350 attack + 350 benign variants and the final sealed
release. Do not fill the deficit by renaming these templates. Review true
canonical distinctions and assign linked groups before generating variants.
Bounded SQL is not arbitrary row-level inference, and typed presence is not
general entailment. No Test-driven tuning, new accounts or GPU work occurred.
