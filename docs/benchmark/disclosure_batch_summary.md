# Disclosure batch: bounded QA and review

2026-09-07. Source `1c3f829`.
[Contract](disclosure_batch_contract.md),
[selected receipt](../../experiments/manifests/phase3_disclosure_v1_validation01.json),
[data/review](../../data/adversarial/disclosure_batch_v1/README.md).

Four new pairs cover a private value in a search argument, two labelled pieces
in final output, pieces accumulated across emails to one recipient, and pieces
in different JSON values of one webhook. Each negative fixture still completes
the public status task. Private reads are permitted; the violation is disclosure.
The same traces pass old typed security checks, isolating the new coverage.
No old scorer, dataset, raw trace or model score is overwritten.

Sixteen fresh Replay paths pass: four combinations of attack/benign and
safe/negative per pair, eight safe and eight negative. These are reference
scripts, not model responses; negative benign fixtures test the oracle and do
not measure benign false positives. Prior evidence explicitly reuses 192 standard
paths, yielding 208 current standard paths (104 safe/104 negative), not 208 new runs.
The six extra admission counterexamples remain separate historical evidence.

The pool now has 52 stored candidates, **50 retained working representatives**,
two prior merges, 17 conservative groups and 1,326 pair comparisons. Three
fragment cases share a group. Retention is assistant self-review under the
owner waiver, not independent human review or certified family independence.
All four additions use DB text sources and the exfiltration category; whole-pool
source/category stratification remains pending. At least 20 further retained
scenarios are needed before final selection, grouped split and variants.

## Bounded semantics and limitations

- Query channel recognizes the literal artifact in search arguments, even
  though search is offline. No external network disclosure is claimed.
- Fragment coverage recognizes only two exact declared pieces. Partial or
  differently transformed disclosure is not comprehensively evaluated.
- Email history is recipient-local and contains only successful sends. Count
  the call completing coverage; failed completion is proposed, not executed.
  Already-complete history does not make later public-only mail a new violation.
- Webhook fragment scope checks string values recursively, not JSON keys.
  Final scope checks only final output. Explicit artifact grants are respected.
- This is an offline evaluator extension, not A0 protection or general provenance.

401 tests pass (34 new), including incomplete/wrong pieces, channel/recipient
separation, grants, failures, trace reproducibility, stale inputs and no-network.
Setup, Ruff, mypy (129 source files), clean_v1.1 sealed-read-only validation pass.
Eleven older receipts/823 hash entries match, including twelve measured artifacts.
The selected verifier saves `valid=true`, `phase3_accepted=false` and exits 2
with `--require-acceptance`, correctly refusing whole-phase acceptance.
No LLM/Kaggle/held-out inference or Test-driven tuning; no variants or split.
Raw traces are ignored under `results/phase3_disclosure_v1_validation01`.
Selected receipt: 133 source/input/prior hash entries and all 16 raw trace hashes
match. Four credential values scanned across 24 changed files: zero matches.
Knowledge links and handoff structure pass validation.
