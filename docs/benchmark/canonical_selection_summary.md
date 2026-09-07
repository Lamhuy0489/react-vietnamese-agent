# Canonical selection and grouped split

2026-09-07. Source `dc45ccb`.
[Contract](canonical_selection_contract.md),
[whole-pool review](../../data/adversarial/canonical_selection_v1/review.json),
[selection manifest](../../experiments/manifests/phase3_canonical_selection_v1_validation01.json).

Seventy canonical task/authorization scenarios are admitted **for variant
authoring** after whole-pool self-review under the owner waiver. All 72 stored
scenarios have a specific retain/merge rationale; hexcode and rowretry remain
merged regression cases. Earlier benign-pair reviews are hash-bound. This is
not independent human review or 70 unrelated abstract mechanisms.

Exact grouped split: **40 Dev / 30 Test**, with all 20 conservative connected
groups intact. Additional source/artifact/destination equality checks retain one
shared-recipient edge within an existing group. Merged cases cannot bridge a
group across splits. Canonical and benign IDs are paired in one manifest;
historical source files remain byte-identical and still say `unassigned`.

Enumerating all 17,429 feasible whole-group assignments gives minimum primary
integer loss 96, secondary loss 156, then a fixed-seed SHA256 tie-break. These
losses are seven times absolute family-count deviation from the 4/7 Dev share,
not percentages or model scores. Primary dimensions are category/source;
secondary dimensions are reference target sink/action-count complexity.

| Primary category | Dev | Test |
|---|---:|---:|
| Data exfiltration | 10 | 10 |
| Indirect injection | 10 | 10 |
| Policy violation | 8 | 7 |
| Tool-output poisoning | 12 | 3 |

The 25-member business group contains 12/15 output-poisoning cases. Therefore
ideal category/source balance is impossible without splitting related templates.
This limitation is retained, not hidden by relabelling or searching model scores.
The manifest also reports sink and complexity cells, including zeros: both
five-action safe references fall in Dev. Complexity is an observable reference
proxy, not measured difficulty; category-specific results will have limited
support and must not be described as representative.

## Verification and boundaries

- 495 tests pass, including 29 new selection tests. Setup, Ruff, mypy 136 source
  files and clean_v1.1 sealed-read-only validation pass.
- All eight candidate snapshots, earlier review, linked reference receipts,
  inherited source and clean-environment hashes revalidate. No old tracked
  data, source, scorer or receipt bytes change.
- Revalidate 288 stored reference records; 280 belong to the 70 selected
  scenarios and eight to merged cases. **Zero fresh Replay or model runs**;
  this is evidence reuse, not new execution or re-reading all raw traces.
- Boundary final-policy and derived-final outcomes remain distinct from raw
  artifact leakage and tool effects. Bounded exact/typed scorers do not prove
  general entailment or comprehensive safety.
- `--check-existing` reproduces the selected manifest without overwriting it.
  `--require-acceptance` exits 2: canonical admission/split pass, but
  `phase3_accepted=false` and `test_sealed=false` are intentional.
- Selected receipt's 78 direct input/evidence/source/review hash entries match;
  inherited source bindings also pass selection validation. Four credential
  values scanned across 16 changed files: zero matches. Knowledge validation
  and Git whitespace checks pass.

Next: use this assignment to author/review five matched variants per selected
family (350 attacks + 350 benign), run exposure/utility/oracle QA on those
variants, integrate release mappings and then seal Test. No LLM/Kaggle or
held-out inference, no Test tuning, and no new account access required.
