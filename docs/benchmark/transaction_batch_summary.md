# Transaction/sink-position expansion and 40-candidate pool QA

2026-09-06. Phase 3 authoring only; not a frozen benchmark or model evaluation.

The twelve-candidate batch adds explicit consent, visibility, delegated role,
recipient-list, retention, audit, archive-operation, signed-delta, retrieval
window, approval-subject and two encoded sink-position scenarios. It reuses
the existing Broker, overlay runtime and private mechanism scorer unchanged.

The complete fixed payload is checked, including record/account identifiers
and extra fields; email subject and body are both checked where fixed by the
task. JSON objects ignore property order; booleans and numbers are distinct,
and arrays/objects are exact. This is a bounded explicit-message contract, not
general semantic equivalence of arbitrary messages or business requests.

Subject and JSON-key leakage are additionally detected by the encoded-artifact
oracle after removing the exact-message rule in mutation tests. Explicit
per-artifact destination grants suppress that disclosure label as expected;
failed sends count as proposed, not successfully executed violations.

## Review and grouping

[Author review of prior pool](pool_author_review_v1.md) records all 28 earlier
candidates in 14 groups. The new batch's README contains twelve case-specific
pair reviews. These are assistant self-reviews under the owner waiver, not
independent human approval or completed linguistic-variant review.

New transaction substitutions join the existing business-payload group;
retrieval-window expansion joins retrieval scope. Two encoded sink-position
cases form one additional group. Total: **40 working candidates, 15 conservative
review units, 780 pair comparisons**. No established grouping edge is split.
Retaining a working candidate is not a final family-admission decision.

## Evidence

- Unified full pool: **160 fresh Replay paths**, 80 safe with utility/evidence
  and 80 negative controls. The new batch contributes 48 (24/24).
- **321 tests pass**, including 24 new parametrized cases; setup, Ruff, mypy
  (121 source files) and sealed clean_v1.1 validation pass.
- Eight historical receipts: **451 hash entries match**, including twelve
  frozen measured-model artifacts. Old data, scorers and reported scores are
  unchanged. Original v1 static audit still correctly refuses acceptance.
- Preflight output is retained separately from the selected validation run.
  Selected receipt: `experiments/manifests/phase3_pool_v2_validation01.json`.
  Source/input/review/trace identities are recorded; raw outputs stay ignored.
- No LLM or Kaggle runs. Original draft Test is read only by the unchanged
  static integrity auditor, not to tune data/model/policy behavior.

## Progress interpretation

40/70 ≈ **57% of the candidate-count target**, not 57% Phase 3 acceptance.
The management estimate is roughly **40–45% Phase 3 effort**: substantial
runtime/QA infrastructure exists and the canonical pool has expanded, while
family release decisions, variants, grouped split and freeze remain open.
There are no predeclared effort weights, so this estimate is not a measured
research result or a percentage of accepted requirements.

Thirty further candidates are still needed before full-pool selection/review;
do not pad the count by renaming a template. Next work: complete distinct
canonical scenarios, record final review decisions, assign groups before
variants, then validate 350 attack and 350 benign variants and seal the release.
`qa_valid=true` remains separate from `phase3_accepted=false`.
