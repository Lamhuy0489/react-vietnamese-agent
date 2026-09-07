# Twelve task-effect pairs: verified authoring milestone

2026-09-07. Source `9917eb0`.
[Contract](completion_batch_contract.md),
[selected receipt](../../experiments/manifests/phase3_completion_v1_validation01.json),
[review/data](../../data/adversarial/completion_batch_v1/README.md).

Twelve paired scenarios cover denomination, rounding, idempotency identity,
atomicity, expiring permission, budget allocation, computation attribution,
signatory identity, source citation, backdating, time zone and queue priority.
Seven tool-output, three document and two cached-page cases improve coverage
without adding another DB-only batch. Existing runtime and scorers are unchanged.

Each public instruction specifies the authorized payload, successful source
prerequisite and one successful send. Full-payload equality includes unexpected
fields and JSON type distinctions. Safe scripts complete the required sink;
negative scripts send the prohibited payload, and therefore fail legitimate
sink utility despite retaining the correct final fact. No claim of utility
success is made for these negative scripts. All effects are synthetic mocks.

## Evidence and interpretation

- 48 fresh Replay paths: 24 safe/24 negative, all four combinations per pair.
- Reuse 208 hash-bound standard paths, for 256 total standard paths (128/128),
  not 256 fresh runs. Prior admission counterexamples remain separate.
- 64 stored candidates, 62 retained working representatives, two prior merges,
  17 conservative groups and 2,016 pair comparisons. All twelve new cases join
  the existing business-payload group, now 25 retained members. They are not
  twelve independent abstract mechanisms. Final family selection remains open.
- Retained categories: 18 indirect, 15 tool-output, 16 exfiltration, 13 policy.
  Retained sources: 17 document, 13 cache, 17 DB, 15 tool-output. Detailed-plan
  category numbers are proposals; they are not silently turned into new scope.
- 428 tests pass (27 new). Setup, Ruff, mypy 131 source files and clean_v1.1
  sealed-read-only validation pass. Twelve prior receipts/956 hash entries
  match, including twelve measured model artifacts.
- Real Broker edge cases cover extra fields, wrong JSON type, premature send,
  successful duplicate, failed duplicate and failed wrong send. No-network,
  deterministic trace and immutable input checks pass.

Assistant self-review is under the owner waiver, not independent-human review.
Pair comparisons/group annotations do not certify semantic independence. No
LLM/Kaggle or held-out inference, Test-driven tuning, variants or split creation.
`valid=true` but `phase3_accepted=false`; exit 2 under `--require-acceptance`
correctly refuses phase closure. Raw traces remain ignored under
`results/phase3_completion_v1_validation01`.
Selected receipt: 143 source/input/prior hash entries and all 48 raw trace files
match. Four credential values scanned across 23 changed files: zero matches.
Knowledge links and handoff structure pass validation.

## Remaining work and progress estimate

At least eight more retained scenarios are needed, and full-pool review may
require further merges. Then assign the grouped 40/30 split before generating
and reviewing 350 attack/350 benign variants, validate mappings and seal Test.
The large business group must stay together; do not rename/split it to improve
stratification. Prefer remaining distinct information-flow or authorization
boundaries over further scalar-field substitutions solely to fill counts.

Current effort estimate: **50–55% of Phase 3**, an unweighted planning estimate,
not an acceptance metric. 62/70 ≈ 89% is provisional representative count only.
Canonical authoring/QA has advanced, but variants, split and release remain open.
