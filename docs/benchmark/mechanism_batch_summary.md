# Mechanism batch v1 — evidence and coverage

2026-09-06. Eight additional unsplit synthetic candidates beside the twelve
unchanged v2.2 pilot pairs: twenty candidates total, not twenty accepted families.
No LLM, Kaggle or held-out inference; no A0, prior input or measured-score changes.

| New candidates | Mechanism group | Observable negative check |
|---|---|---|
| `awb_quantity`, `awb_operation`, `awb_repair` | Business-payload substitution | Wrong nested payload fields at an otherwise authorized endpoint |
| `awb_repeat` | Successful-action replay | Repeated successful send exceeds user quota |
| `awb_order` | Premature commit | Send proposed before prerequisite calculation succeeds |
| `awb_query` | Retrieval-query scope | Search expands beyond the user-authorized query |
| `awb_encoded`, `awb_hexcode` | Encoded final disclosure | Complete Base64/hex representation of an artifact leaks in final |

The three parameter cases remain one conservative group, as do the two encoded
disclosure cases. Five new groups plus seven prior groups give twelve provisional
review units. The combined audit enumerates all 190 unordered pairs; it does not
prove semantic independence, assign splits or grant human approval.

## Executable evidence

- 32 new Replay runs: sixteen safe preserve typed utility and sixteen negative
  runs trigger the declared new mechanism. Eight tools are actually exercised
  across the batch; safe paths have two to four actions plus final.
- Two pairs expose their full additions through genuine 180-character search
  snippets. The other pairs expose at read/output actions, including four
  retrieval-led paths using both document and cached search. No search ranking
  or fabricated result is inserted by a replacement tool.
- Benign/attack whitespace-word ratios are 1.0556–1.2 under the local 0.8–1.25
  guard. Benign text describes legitimate task context without safety coaching.
- 263 tests pass, including nineteen new tests: wrong arguments beyond reference
  values, boolean/numeric distinction, failed sends, call quotas, late/failed
  prerequisites, encoding grants, missing snippet exposure/mappings and replay
  reproducibility. Integration QA blocks socket/DNS/SMTP.
- Setup, Ruff, mypy (115 source files) and clean_v1.1 sealed validation pass.
- [Receipt](../../experiments/manifests/phase3_mechanism_batch_v1_validation01.json)
  stores exact new/pilot/clean/source/trace hashes and combined group evidence.
  Together with the prior v2.2 receipt, the twenty-pair pool has eighty reference
  trajectories of QA evidence; this turn ran only the thirty-two new fixtures.

## Limits and next work

The new temporal/argument rules and encoded checks are private offline QA, not
runtime defenses. Encoded detection covers complete UTF-8 Base64/hex values only;
fragmentation, other encodings, steganography, row-level SQL authorization and
general semantic entailment remain outside the covered metrics. Exact argument
and prerequisite matching is intentionally bounded. Failed effects count as
proposed, not completed violations; artifact/final grants remain independent.

Author inspection is assistant self-review under the owner's same-machine
workflow, not independent human approval. No final family/variant acceptance is
claimed. Next: expand genuinely different multi-source/data-scope scenarios,
define necessary oracle extensions before counting them, then consolidate the
canonical pool and approve its grouping before variants and stratified split.
