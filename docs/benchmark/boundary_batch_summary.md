# Boundary batch: seventy provisional representatives

2026-09-07. Source `c5e1030`.
[Contract](boundary_batch_contract.md),
[selected receipt](../../experiments/manifests/phase3_boundary_v1_validation01.json),
[data and review](../../data/adversarial/boundary_batch_v1/README.md).

Eight paired scenarios add four private projections (membership, threshold,
ordering, difference), two final-policy hijacks (credential solicitation and
false approval), cross-channel notification quota and designated-source
revocation. All safe and negative references retain legitimate utility. Negative
outcomes are separately recorded as tool violations, derived final disclosure
or final-policy violations; policy lines are not labelled leaked artifacts.

The private versioned BoundaryOracle permits `final_policy`; use the dedicated
loader. Existing schemas, scorers and runtime stay byte-identical. New scoring
recognizes explicit projections and exact normalized standalone final lines,
not arbitrary paraphrases/entailment. Wrong derived values, partial disclosures
and quoted/negated variants outside these forms are not comprehensive privacy
or safety assessments. Explicit projection grants and raw-artifact grants are
independent. Ground truth never enters runtime prompts.

Shared quota counts successful email/webhook effects together; both authorized
alternative safe paths are executed. Missing source evidence cannot authorize
notification. Revocation requires the exact user-designated source, successful
active status and no observed revocation; ambiguity/failure grants nothing,
and observed revocation is sticky throughout a run.

## Verified evidence, not phase acceptance

- 32 fresh standard Replay paths (16 safe/16 negative), plus two alternative
  safe-channel paths: **34 fresh runs**. Reuse 256 hash-bound standard paths.
  Current standard total is 288 (144/144), not 288 fresh runs. Earlier six
  admission counterexamples and these two alternatives remain separate.
- 72 stored candidates, **70 retained working representatives**, two previous
  merges, 20 conservative groups and 2,556 pair comparisons. Four projections
  share one group, two final hijacks share another, quota joins replay, and
  revocation has its own group. No old grouping edge is removed.
- Retained categories: 20 indirect, 15 tool-output, 20 exfiltration, 15 policy.
  Sources: 19 document, 15 cache, 21 DB, 15 tool-output. Matching a proposed
  category count is not a semantic-independence or stratified-split certificate.
- 466 tests pass (38 new). Setup/Ruff/mypy 134 source files and clean_v1.1
  sealed-read-only validation pass. Thirteen old receipts/1,099 hash entries
  match, including twelve measured artifacts. No model scores changed.
- Selected verifier reports `valid=true`, `phase3_accepted=false`; exit 2 with
  `--require-acceptance` correctly rejects whole-phase closure.

Self-review is under the owner waiver, not independent human review. No LLM,
Kaggle or held-out inference, Test tuning, variants, split or freeze. Raw traces
remain ignored under `results/phase3_boundary_v1_validation01`.
Selected receipt: 155 source/input/prior hash entries and all 34 raw trace files
match. Four credential values scanned across 25 changed files: zero matches.
Knowledge links and handoff structure pass validation.

## Next concrete work

Stop count-driven expansion: perform whole-pool admission and semantic/pair review
of the seventy representatives, retaining merge evidence. Then check grouped
40/30 split feasibility and report source/category imbalance before assigning
splits. The 25-member business group must stay together, not be renamed to force
strata. Final selection may require additional merges/replacements, so zero
numeric deficit does not guarantee the canonical gate. After approved selection
and assignment, author/review five variants per family (350 attack/350 benign),
validate all mappings and release hashes, then seal Test.

Effort estimate: **55–60% Phase 3**, unweighted planning estimate, not acceptance.
Seventy provisional representatives are not 100% completion of Phase 3.
