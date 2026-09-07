# Mechanical variants v1: partial, not the final benchmark

Immutable canonical selection -> 70 paired families x three mechanical surfaces:
**210 attacks + 210 benign**, 120 Dev/90 Test per branch. The source assignment,
20 conservative groups, public tasks and private oracles are unchanged.

- `variants.jsonl`: draft text and exact canonical/family/pair/group/split mapping.
- `inventory.json`: original draft identity/counts; intentionally still pending.
- `review.json`: subsequent assistant review of all 140 word-boundary edits,
  hash-bound to canonical and variant bytes, under the owner waiver. The other
  280 no-diacritic/zero-width records receive deterministic structural checks.

Draft rows are not rewritten to make their status look approved. Acceptance of
this mechanical subset belongs to the separate verification receipt, after
review and executable parity checks. It is not independent human review or
unrestricted semantic equivalence. Code-mix/paraphrase are **not authored here**;
do not count 420 as the required 700 or seal Test from this subset.

Only the selected payload text enters the unchanged public overlay builder.
Never pass variant catalog/review/private scorer metadata to a model. Some exact
output literals retain diacritics intentionally so the target output and oracle
do not change. `NOTICE` stays intact so zero-width insertion affects the following
Vietnamese text. See [contract](../../../docs/benchmark/mechanical_variants_contract.md).

Fresh reference execution covers original canonical and variant safe/negative
paths plus the declared shared-quota alternative. The adapter retains each
batch's scorer (including corrected mechanism v2 and separate final-policy /
derived-final fields); it refuses unknown scorers or score drift. References
are scripted fixtures, never observed LLM performance.
